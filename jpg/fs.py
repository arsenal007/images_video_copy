from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Optional
import os
import stat
import posixpath

class FS(ABC):
    """A file system interface sufficient for clean()."""

    @abstractmethod
    def listdir(self, path: str) -> list[str]:
        ...

    @abstractmethod
    def isdir(self, path: str) -> bool:
        ...

    @abstractmethod
    def join(self, *parts: str) -> str:
        ...

    @abstractmethod
    def chmod(self, path: str, mode: int) -> None:
        ...

    @abstractmethod
    def access_write(self, path: str) -> bool:
        ...

    @abstractmethod
    def rmdir(self, path: str) -> None:
        """Delete an EMPTY directory."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        ...

# ===================== Local implementation =====================
class LocalFS(FS):
    def listdir(self, path: str) -> list[str]:
        return os.listdir(path)

    def isdir(self, path: str) -> bool:
        return os.path.isdir(path)

    def join(self, *parts: str) -> str:
        return os.path.join(*parts)

    def chmod(self, path: str, mode: int) -> None:
        os.chmod(path, mode)

    def access_write(self, path: str) -> bool:
        return os.access(path, os.W_OK)

    def rmdir(self, path: str) -> None:
        os.rmdir(path)  # видаляє ТІЛЬКИ порожні каталоги

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

# ===================== SFTP implementation =====================
class SFTPFS(FS):
    """
    Usage:
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=..., username=..., password=... or pkey=...)
    sftp = client.open_sftp()
    fs = SFTPFS(sftp)
    clean(fs, "/remote/dir")
    """
    def __init__(self, sftp_client) -> None:
        self.sftp = sftp_client

    def listdir(self, path: str) -> list[str]:
        # listdir повертає лише імена — як у os.listdir
        return self.sftp.listdir(path)

    def isdir(self, path: str) -> bool:
        try:
            st = self.sftp.stat(path)
        except IOError:
            return False
        return stat.S_ISDIR(st.st_mode)

    def join(self, *parts: str) -> str:
        # A POSIX path is required on the remote *nix machine
        return posixpath.join(*parts)

    def chmod(self, path: str, mode: int) -> None:
        self.sftp.chmod(path, mode)

    def access_write(self, path: str) -> bool:
        # Rough permission check by directory write bits: owner/group/other write
        try:
            st = self.sftp.stat(path)
        except IOError:
            return False
        m = st.st_mode
        return bool(m & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))

    def rmdir(self, path: str) -> None:
        self.sftp.rmdir(path)  # Same as locally — removes ONLY empty directories

    def exists(self, path: str) -> bool:
        try:
            self.sftp.stat(path)
            return True
        except IOError:
            return False

def default_handle_remove_readonly(fs: FS, path: str, exc: BaseException) -> bool:
    """
    Attempt to remove read-only (0o700) and request a retry of deletion.
    Return True to let clean() try again; False to give up.
    """
    try:
        fs.chmod(path, stat.S_IRWXU)  # 0o700
        return True
    except Exception:
        return False

# ===================== Universal clean =====================
def clean(
    fs: FS,
    dir_path: str,
    *,
    make_writable: bool = True,
    onerror: Optional[Callable[[FS, str, BaseException], bool]] = default_handle_remove_readonly,
) -> None:
    """
    Recursively traverses subdirectories of dir_path and removes EMPTY directories.
    - fs: FS implementation (LocalFS or SFTPFS)
    - make_writable: if no write permission — try setting 0o700 and continue
    - onerror(fs, path, exc) -> bool: if removing an empty directory fails,
      return True to retry after removing read-only; False to skip retry.
    """
    # Get directory contents
    try:
        entries = fs.listdir(dir_path)
    except Exception as e:
        # No access or does not exist — just exit
        return

    # If necessary — ensure write permissions on the directory itself (for subsequent rmdir)
    if make_writable and not fs.access_write(dir_path):
        try:
            fs.chmod(dir_path, stat.S_IRWXU)  # 0o700
        except Exception:
            # If it didn’t work — continue as is (we may not be able to delete)
            pass

    # First, traverse subdirectories (post-order, same as in your version)
    for name in entries:
        subpath = fs.join(dir_path, name)
        if fs.isdir(subpath):
            clean(fs, subpath, make_writable=make_writable, onerror=onerror)

    # After traversal — if the directory is empty, delete it
    try:
        if not fs.listdir(dir_path):  # empty
            fs.rmdir(dir_path)
    except Exception as e:
        # Try to remove read-only and retry (if allowed)
        if onerror and onerror(fs, dir_path, e):
            try:
                if not fs.listdir(dir_path):
                    fs.rmdir(dir_path)
            except Exception:
                # finally give up
                pass

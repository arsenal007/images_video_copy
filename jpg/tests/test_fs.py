import os
import stat as statmod
import tempfile
import shutil
import unittest

from jpg.fs import FS, clean, LocalFS, SFTPFS


def onerror_retry(fs_obj, path, exc):
    """Universal onerror handler for tests: removes RO and requests a retry."""
    try:
        fs_obj.chmod(path, statmod.S_IRWXU)  # 0o700
    except Exception:
        pass
    return True


class TestCleanLocalFS(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="fs_local_")
        self.fs = LocalFS()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_removes_empty_leaf_and_parents(self):
        # root/a/empty -> обидві мають зникнути
        a = os.path.join(self.tmpdir, "a")
        empty = os.path.join(a, "empty")
        os.makedirs(empty, exist_ok=True)

        self.assertTrue(os.path.isdir(empty))
        clean(self.fs, a, onerror=onerror_retry)
        self.assertFalse(os.path.exists(empty))
        self.assertFalse(os.path.exists(a))

    def test_keeps_non_empty_dir(self):
        d = os.path.join(self.tmpdir, "data")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "file.txt"), "w", encoding="utf-8") as f:
            f.write("x")

        clean(self.fs, d, onerror=onerror_retry)
        self.assertTrue(os.path.isdir(d))
        self.assertTrue(os.path.isfile(os.path.join(d, "file.txt")))

    def test_make_writable_enables_delete(self):
        # Створимо /top/empty і заберемо write у /top — clean має виставити 700 і видалити все
        top = os.path.join(self.tmpdir, "top")
        empty = os.path.join(top, "empty")
        os.makedirs(empty, exist_ok=True)

        # забрати write для всіх на top (тільки r-x для власника)
        try:
            os.chmod(top, statmod.S_IRUSR | statmod.S_IXUSR)
        except PermissionError:
            # on some systems it may not allow this; in that case, skip changing permissions
            pass

        clean(self.fs, top, make_writable=True, onerror=onerror_retry)
        self.assertFalse(os.path.exists(empty))
        self.assertFalse(os.path.exists(top))

    def test_nonexistent_is_graceful(self):
        missing = os.path.join(self.tmpdir, "no_such_dir")
        # Should not raise an exception
        clean(self.fs, missing, onerror=onerror_retry)


# -------------------------- Fake SFTP client --------------------------
class _FakeSFTPClient:
    """
    A minimal in-memory SFTP-like implementation for testing FS.SFTPFS.
    Stores the tree as {path: {"type": "dir"/"file", "mode": int, "entries": set()}}.
    """
    def __init__(self):
        self.nodes = {}
        self._mkroot("/")

    # --- API, яке викликає SFTPFS ---
    def listdir(self, path: str):
        n = self._node(path)
        if n["type"] != "dir":
            raise NotADirectoryError(path)
        return sorted(n["entries"])

    class _Attr:
        def __init__(self, st_mode):
            self.st_mode = st_mode

    def stat(self, path: str):
        n = self._node(path)
        return self._Attr(n["mode"])

    def chmod(self, path: str, mode: int):
        self._node(path)["mode"] = mode

    def rmdir(self, path: str):
        n = self._node(path)
        if n["type"] != "dir":
            raise NotADirectoryError(path)
        if n["entries"]:
            raise OSError("Directory not empty")
        parent, name = self._split(path)
        if parent in self.nodes:
            self.nodes[parent]["entries"].discard(name)
        self.nodes.pop(path, None)

    # --- helper methods for building the tree ---
    def mkdir(self, path: str, mode: int = statmod.S_IRWXU):
        if path in self.nodes:
            return
        parent, name = self._split(path)
        if parent not in self.nodes or self.nodes[parent]["type"] != "dir":
            raise FileNotFoundError(parent)
        self.nodes[path] = {"type": "dir", "mode": statmod.S_IFDIR | mode, "entries": set()}
        self.nodes[parent]["entries"].add(name)

    def touch(self, path: str, mode: int = statmod.S_IRUSR | statmod.S_IWUSR):
        parent, name = self._split(path)
        if parent not in self.nodes:
            raise FileNotFoundError(parent)
        self.nodes[path] = {"type": "file", "mode": statmod.S_IFREG | mode}
        self.nodes[parent]["entries"].add(name)

    # --- internal utilities ---
    def _mkroot(self, path="/"):
        self.nodes[path] = {"type": "dir", "mode": statmod.S_IRWXU | statmod.S_IRWXU, "entries": set()}

    def _node(self, path: str):
        if path not in self.nodes:
            raise FileNotFoundError(path)
        return self.nodes[path]

    def _split(self, path: str):
        path = path.rstrip("/")
        if not path or path == "/":
            return ("/", "")
        i = path.rfind("/")
        parent = "/" if i == 0 else path[:i]
        name = path[i + 1 :]
        return (parent, name)


class TestCleanSFTPFS(unittest.TestCase):
    def setUp(self):
        self.sftp = _FakeSFTPClient()
        self.fs = SFTPFS(self.sftp)

    def test_removes_empty_leaf_and_parents(self):
        # /a/empty -> everything should disappear
        self.sftp.mkdir("/a")
        self.sftp.mkdir("/a/empty")
        clean(self.fs, "/a", onerror=onerror_retry)
        # /a/empty has been deleted, /a is empty -> it should disappear too
        with self.assertRaises(FileNotFoundError):
            self.sftp._node("/a/empty")
        with self.assertRaises(FileNotFoundError):
            self.sftp._node("/a")

    def test_keeps_non_empty_dir(self):
        self.sftp.mkdir("/data")
        self.sftp.touch("/data/file.jpg")
        clean(self.fs, "/data", onerror=onerror_retry)
        # /data лишається, бо всередині файл
        self.assertEqual(set(self.sftp.listdir("/data")), {"file.jpg"})

    def test_make_writable_enables_delete(self):
        # Заберемо write на /top і /top/empty, clean має поставити 700 та видалити
        self.sftp.mkdir("/top", mode=statmod.S_IRUSR | statmod.S_IXUSR)
        self.sftp.mkdir("/top/empty", mode=0)
        clean(self.fs, "/top", make_writable=True, onerror=onerror_retry)
        with self.assertRaises(FileNotFoundError):
            self.sftp._node("/top/empty")
        with self.assertRaises(FileNotFoundError):
            self.sftp._node("/top")

    def test_onerror_retry_called(self):
        self.sftp.mkdir("/p")
        self.sftp.mkdir("/p/empty")

        calls = {"n": 0}
        orig_rmdir = self.sftp.rmdir

        def flakey_rmdir(path):
            if path == "/p/empty" and calls["n"] == 0:
                calls["n"] += 1
                raise OSError("simulated")
            return orig_rmdir(path)

        self.sftp.rmdir = flakey_rmdir  # monkey-patch

        tries = {"on": 0}
        def onerror(fs_obj, path, exc):
            tries["on"] += 1
            fs_obj.chmod(path, statmod.S_IRWXU)
            return True

        clean(self.fs, "/p", onerror=onerror)
        self.assertEqual(tries["on"], 1)
        with self.assertRaises(FileNotFoundError):
            self.sftp._node("/p")

    def test_nonexistent_is_graceful(self):
        # не повинно падати
        clean(self.fs, "/no/such/dir", onerror=onerror_retry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
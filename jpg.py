from PIL import Image
import sys
import os
import time
import datetime
import glob
import filecmp
import piexif
import errno
import os
import stat
import shutil
from jpg.ren import FileRenamer




# Вхідні та вихідні директорії
DIR_IN = "F:\\1\\2"
DIR_OUT = "F:\\photos\\"
#os.path.join("E:", "photos", "2023-01", "2023-01-01_12.00.00_Sunday_2.jpg")








def get_minimum_creation_time(exif_data):
    mtime = "?"
    if 306 in exif_data and exif_data[306] < mtime:  # 306 = DateTime
        mtime = exif_data[306]
    # 36867 = DateTimeOriginal
    if 36867 in exif_data and exif_data[36867] < mtime:
        mtime = exif_data[36867]
    # 36868 = DateTimeDigitized
    if 36868 in exif_data and exif_data[36868] < mtime:
        mtime = exif_data[36868]
    return mtime


def min(x, y):
    if x > y:
        return y
    elif x < y:
        return x
    elif x == y:
        return x


def min3(x, y, z):
    return min(min(x, y), z)


def exif(file):
    #dict = piexif.load(file)
    #l = len(dict)
    return (True)


def get_ext(name):
    base, ext = os.path.splitext(name)
    return ext[1:]


def is_ext(name, ext):
    return get_ext(name) == ext


'''
    For the given path, get the List of all files in the directory tree 
'''


def getListOfFiles(dirName, ext):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = []
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath, ext)
        elif is_ext(entry, ext):
            allFiles.append(fullPath)

    return allFiles


def handleRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise


def clean(dirr):
    dirContents = os.listdir(dirr)
    if not os.access(dirr, os.W_OK):
        os.chmod(dirr, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    if len(dirContents) == 0:
        # os.remove(dirr)
        shutil.rmtree(dirr, ignore_errors=False, onerror=handleRemoveReadonly)
    else:
        for f in dirContents:
            fullPath = os.path.join(dirr, f)
            if os.path.isdir(fullPath):
                clean(fullPath)



#==============================================
# fix
# input: filename with arbitrarery extension
# output: filename with lower case extension
# example 1.JPG -> 1.jpg
#==============================================

def fix(name):
    base, ext = os.path.splitext(name)
    return base + ext.lower()

supported_extensions = ["jpg", "JPG", "mp4", "MP4", "3gp", "MOV", "3GP", "avi", "wmv",
              "WMV", "jpeg", "JPEG", "MOD", "mov", "tiff", "TIFF", "NEF", "png", "gif", "GIF", "AVI","MPG","mpg"]

def process_files_rename(input_directory, output_directory, extensions):
    fse = sys.getfilesystemencoding()
    for ext in extensions:
        list = getListOfFiles(input_directory, ext)
        for file in list:
            renamer = FileRenamer(output_directory)
            head, teil = os.path.split(file)
            move_to = fix(teil)
            file_encoded = file.encode(fse)
            move_to_encoded = move_to.encode(fse)
            print(file_encoded, move_to_encoded, sep=' -> ',
                  end=' [', file=sys.stdout, flush=False)
            json_extension = ".json".encode(fse)
            json_file = file_encoded + json_extension
            if os.path.exists(json_file):
                new_json_file = move_to_encoded + json_extension
                shutil.move(json_file, new_json_file)

            shutil.move(file_encoded, move_to_encoded)
            new_ext = get_ext(move_to_encoded)
            renamer.ren(move_to_encoded, new_ext.decode(fse))
    clean(input_directory)

if __name__ == "__main__":
    process_files_rename( DIR_IN,DIR_OUT, supported_extensions)
    #input("Press Enter to continue...")

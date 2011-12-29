import os

def safe_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass

def safe_mkdirs(path):
    try:
        os.makedirs(path)
    except OSError:
        pass

def safe_link(from_path, to_path):
    tmp_path = to_path + ".tmp"

    safe_unlink(tmp_path)
    safe_mkdirs(os.path.dirname(to_path))

    try:
        os.symlink(from_path, tmp_path)
        os.rename(tmp_path, to_path)
    except OSError, e:
        print "Error linking %s to %s" % (from_path, to_path)
        raise e

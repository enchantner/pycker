import os
import ctypes
import ctypes.util
import argparse
import socket
import subprocess
import sys

MS_PRIVATE      = (1 << 18)
MS_REC          = 16384

CLONE_NEWNS = 0x00020000  
CLONE_NEWPID = 0x20000000
CLONE_NEWUTS = 0x04000000


libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


def unshare(flags):
    _unshare = libc.unshare
    _unshare.restype = ctypes.c_int
    _unshare.argtypes = (ctypes.c_int, )

    if _unshare(flags) == -1:
        print("Error: in unshare:", os.strerror(ctypes.get_errno()))
        return False
    return True


def mount(source, target, fs, flags, options):
    _mount = libc.mount
    _mount.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_ulong,
        ctypes.c_char_p
    )
    if _mount(
            source.encode(),
            target.encode(),
            fs.encode(),
            flags,
            options.encode()
    ) == -1: 
        print("Error in mount:", os.strerror(ctypes.get_errno()))
        return False
    return True


def umount(target, flags):
    _umount = libc.umount2
    _umount.argtypes = (ctypes.c_char_p, ctypes.c_int)
    if _umount(target.encode(), flags) == -1: 
        print("Error in umount:", os.strerror(ctypes.get_errno()))
        return False
    return True


def run(*args):
    unshare(CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS)
    subprocess.run(["/proc/self/exe", sys.argv[0], "child", *args])


def child(*args):
    socket.sethostname("container")
    os.chroot(os.path.join(os.getcwd(), "fakeroot"))
    os.chdir("/") 
    #mount("/", "/", "auto", MS_PRIVATE | MS_REC, "")
    mount("proc", "/proc", "proc", 0, "") 
    subprocess.run(args)
    umount("/proc", 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('action', type=str, help="action to perform")
    args, other = parser.parse_known_args()
    if args.action == "run":
        run(*other)
    elif args.action == "child":
        child(*other)
    else:
        parser.print_help()



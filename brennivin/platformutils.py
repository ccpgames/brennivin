"""
Functionality for learning about the current platform/executable.

Supports finding the Python flavor (ExeFile, Maya, 26, 27),
whether the OS is 64 bit Windows,
and whether the current process is 64 bits.

Members
=======
"""

import os as _os
import struct as _struct
import sys as _sys

try:
    import multiprocessing as _multiprocessing
except ImportError:
    _multiprocessing = None

from .dochelpers import ignore as _ignore

EXE_MAYA = 'Maya Python'
EXE_MAYA27 = 'Maya Python 2.7'
EXE_EXEFILE = 'Exefile Python'
EXE_VANILLA26 = 'Pure Python 2.6'
EXE_VANILLA27 = 'Pure Python 2.7'


def get_interpreter_flavor(_exepath=_ignore, _vinfo=_ignore):
    """Return one of the ``'EXE'``-prefixed consts showing
    which interpreter is in use.
    """
    _exepath = _exepath or _sys.executable
    _vinfo = _vinfo or _sys.version_info

    def getType(path):
        # The .lower() call below is questionable under POSIX/Linux.
        # normcase would require two sets of tests to function reliably.
        # If this ever causes strange behavior, we can change how this works,
        # but since the scope is so limited to some executables we know about,
        # it should be fine.
        path = path.lower().replace('_d.exe', '.exe')
        if path.endswith(('exefile.exe', 'exefileconsole.exe')):
            return EXE_EXEFILE
        if path.endswith(('maya.exe', 'mayabatch.exe', 'mayapy.exe')):
            if _vinfo[1] == 6:
                return EXE_MAYA
            elif _vinfo[1] == 7:
                return EXE_MAYA27
        if path.endswith(('python.exe', 'pythonw.exe', 'python')):
            if _vinfo[1] == 6:
                return EXE_VANILLA26
            elif _vinfo[1] == 7:
                return EXE_VANILLA27
        raise NameError("Could not identify executable path '%s'" % path)
    return getType(_exepath)


def is_64bit_windows():
    """Return true if the current OS is a 64 bit windows OS, False if not.
    Behavior unreliable on other OSes."""
    # http://stackoverflow.com/questions/2208828/detect-64bit-os-windows-in-python
    # No framework I know of makes this easy
    # (because I don't think it is truly explicit anywhere).
    # This is the recommended (and easy to understand!) hack.
    return 'PROGRAMFILES(x86)' in _os.environ


def is_64bit_process(_structmod=_ignore):
    """Return True if the current process is 64 bits,
    False if 32,
    otherwise raises OSError."""
    _structmod = _structmod or _struct
    #x64: 8, x32: 4
    size = _structmod.calcsize("P")
    if size == 8:
        return True
    elif size == 4:
        return False
    raise OSError('Could not determine process architecture for %s' % size)


def cpu_count(_multiprocmod=_ignore):
    """ Number of virtual or physical CPUs on this system."""
    _multiprocmod = _multiprocmod or _multiprocessing
    if _multiprocessing:
        try:
            return _multiprocmod.cpu_count()
        except (NotImplementedError, AttributeError):
            pass

    # Will only work on Windows but whatevs
    try:
        res = int(_os.environ['NUMBER_OF_PROCESSORS'])
        if res > 0:
            return res
    except (KeyError, ValueError):
        pass
    raise SystemError('Number of processors could not be determined.')

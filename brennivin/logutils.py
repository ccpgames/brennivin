"""
Useful stuff for working with the stdlib's :mod:`logging` module.

See the :class:`Fmt` class for commonly used format strings/formatters.

If you need a :class:`NullHandler`,
use the one from this package to add Python 2.6 compatibility.

There are various functions for working with timestamped log filenames
(getting the timestamped name, cleaning up old versions, etc).

Use :func:`get_filenames_from_loggers` to get all the logging filenames currently
registered.

Members
=======
"""

import fnmatch
import logging
import os
import time


try:
    NullHandler = logging.NullHandler
except AttributeError:
    # python 2.6 does not have this null handler so we need to patch this.
    class NullHandler(logging.Handler):
        """
        This handler does nothing. It's intended to be used to avoid the
        "No handlers could be found for logger XXX" one-off warning. This is
        important for library code, which may contain code to log events. If a user
        of the library does not configure logging, the one-off warning might be
        produced; to avoid this, the library developer simply needs to instantiate
        a NullHandler and add it to the top-level logger of the library module or
        package.
        """
        def emit(self, record):
            pass
    logging.NullHandler = NullHandler


class Fmt(object):
    """Commonly used format strings and formatters.
    Formatter instances begin with `'FMT'`.

    Attributes should be strings of letters that describe the format:

    - N: name
    - T: asctime
    - L: levelname
    - M: message
    """
    NTLM = '%(name)s %(asctime)s %(levelname)s:  %(message)s'
    FMT_NTLM = logging.Formatter(NTLM)
    LM = '%(levelname)s: %(message)s'
    FMT_LM = logging.Formatter(LM)


class MultiLineIndentFormatter(logging.Formatter):
    """Indents every newline character in a formatted logrecord to have
    the same indentation as the formatted record's header.
    """
    def __init__(self, fmt=None, datefmt=None, sep=' '):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.sep = sep

    def format(self, record):
        formattedRecord = logging.Formatter.format(self, record)
        header, footer = formattedRecord.split(record.msg)
        # noinspection PyTypeChecker
        s = formattedRecord.replace('\n', '\n' + (self.sep * len(header)))
        return s


def timestamped_filename(
        filename, fmt='%Y-%m-%d-%H-%M-%S',
        timestruct=None, sep='_'):
    """Given a filename, return a new filename
    '{head}_{formatted timestruct}.{ext}'.

    :param filename: The filename.
    :param fmt: The format string.
    :param timestruct: A named tuple instance such as from time.localtime().
      Defaults to time.gmtime().
    :param sep: Separator between the filename and the time.

    >>> timestamped_filename(r'C:\blah.log', timestruct=(2010,9,8,7,6,5,4,3,0))
    r'C:\blah_2010-09-08-07-06-05.log'
    """
    head, ext = os.path.splitext(filename)
    timestr = timestamp(fmt, timestruct)
    return '%s%s%s%s' % (head, sep, timestr, ext)


def timestamp(fmt, timestruct=None):
    """Return timestamp by calling ``time.strftime(fmt, timestruct())``.

    :param fmt: format str, see
      http://docs.python.org/2/library/datetime.html?highlight=time.strftime#strftime-strptime-behavior
      for details
    :param timestruct: 9-tuple, see :py:func:`time.gmtime` for details.
    """
    return time.strftime(fmt, timestruct or time.gmtime())


def get_timestamped_logfilename(
        folder, basename=None, ext='.log',
        fmt='%Y-%m-%d-%H-%M-%S', timestruct=None,
        _getpid=os.getpid):
    """Using default keyword arguments
    return filename ``<folder>/<basename>_<timestamp>_<pid>.log``
    in the app's folder in ccptechart prefs.

    :param folder: Folder to put file into.
    :param basename: The prefix of the log filename.
      If None, use ``os.path.basename(folder)``.
    """
    if basename is None:
        basename = os.path.basename(folder)
    timestamped = timestamp(fmt, timestruct)
    pid = _getpid()
    logname = '{basename}_{timestamped}_pid{pid}{ext}'.format(**locals())
    logfilename = os.path.join(folder, logname)
    try:
        remove_old_files(folder, '*{basename}_*{ext}'.format(**locals()), 15)
    except OSError:
        pass
    return logfilename


def get_filenames_from_loggers(loggers=None, _logging=None):
    """
    Get the filenames of all log files from loggers.
    If not supplied,
    use all loggers from :mod:`logging` module.
    """
    _logging = _logging or logging
    # noinspection PyUnresolvedReferences
    loggers = loggers or (
        _logging.Logger.manager.loggerDict.values() + [_logging.root])
    allfilenames = set()
    # Placeholders can be in the logger so limit it to
    # only loggers who have handlers.
    for logger in filter(lambda lo: hasattr(lo, 'handlers'), loggers):
        #Get all loghandler's baseFilename attr (or None), filter out
        # those that don't have it.
        filenames = [getattr(h, 'baseFilename', None) for h in logger.handlers]
        for f in filter(None, filenames):
            allfilenames.add(os.path.abspath(f))
    return tuple(allfilenames)


def remove_old_files(rootDir, namePattern='*', maxFiles=1):
    """Removes the oldest files that match ``namePattern`` inside of ``rootDir``,
    so that only ``maxFiles`` of those matches remain.

    :param maxFiles: Number of files to keep. If 0, remove all files.
    """
    if maxFiles < 0:
        raise ValueError('maxFiles must be >= 0, got %s' % maxFiles)

    lstFiles = []
    for f in os.listdir(rootDir):
        if fnmatch.fnmatch(f, namePattern):
            fileName = os.path.join(rootDir, f)
            lstFiles.append(fileName)
    lstFiles.sort(key=os.path.getmtime, reverse=True)
    for f in lstFiles[maxFiles:]:
        try:
            os.remove(f)
        except (OSError, IOError):
            pass


def wrap_line(s, maxlines, maxlen=254, pfx="- "):
    """
    :param s: input string
    :param maxlines: max amount of lines, or 0 for no limit
    :param maxlen: max length of any one line
    :param pfx: prefix for lines after first (counts towards line length)
    """
    e = len(s)
    if e <= maxlen:
        yield s
    else:
        i = maxlen
        maxlen -= len(pfx)
        maxlines -= 1
        yield s[:i]
        while i < e and maxlines:
            yield pfx + s[i:i + maxlen]
            i += maxlen
            maxlines -= 1

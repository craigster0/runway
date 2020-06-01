import datetime
import platform

if platform.system() == 'Windows':
    from colorama import init
    init()


class bcolors:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def colorize(text, color):
    return "{}{}{}".format(color, text, bcolors.ENDC)


def debug(text, logfile_path=None):
    print(colorize(text, bcolors.BLUE))
    log(text, logfile_path)


def error(text, logfile_path=None):
    print(colorize(text, bcolors.RED))
    log(text, logfile_path)


def info(text, logfile_path=None):
    print(colorize(text, bcolors.BOLD))
    log(text, logfile_path)


def success(text, logfile_path=None):
    print(colorize(text, bcolors.GREEN))
    log(text, logfile_path)


def warning(text, logfile_path=None):
    print(colorize(text, bcolors.YELLOW))
    log(text, logfile_path)


def normal(text, logfile_path=None):
    print(text)
    log(text, logfile_path)


def log(text, logfile_path):
    if logfile_path is not None:
        with open(logfile_path, "a") as logfile:
            logfile.write("[{}] {}\n".format(
                datetime.datetime.now().strftime("%F %H:%M:%S"), text))

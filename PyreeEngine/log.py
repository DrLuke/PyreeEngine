from sys import stderr
from datetime import datetime

def time() -> str:
    return datetime.now().strftime("%H:%M:%S")

def info(modulename: str, text: str):
    print("[%s] \033[96m%s: \033[0m%s" % (time(), modulename, text))

def warning(modulename: str, text: str):
    print("[%s] \033[93m%s: \033[0m%s" % (time(), modulename, text))

def success(modulename: str, text: str):
    print("[%s] \033[92m%s: \033[0m%s" % (time(), modulename, text))

def error(modulename: str, text: str):
    print("[%s] \033[91m%s: \033[0m%s" % (time(), modulename, text), file=stderr)
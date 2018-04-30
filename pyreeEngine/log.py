def info(modulename: str, text: str):
    print("\033[96m%s: \033[0m%s" % (modulename, text))

def warning(modulename: str, text: str):
    print("\033[93m%s: \033[0m%s" % (modulename, text))

def success(modulename: str, text: str):
    print("\033[92m%s: \033[0m%s" % (modulename, text))

def error(modulename: str, text: str):
    print("\033[91m%s: \033[0m%s" % (modulename, text))
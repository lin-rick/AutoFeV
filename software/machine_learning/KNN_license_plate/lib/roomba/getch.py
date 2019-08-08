import platform


def __win_create_getch():
    # import msvcrt
    # Correct this later, but windows implementation seems to return binary
    return (lambda: getch().decode("utf-8"))


def __unix_create_getch():
    import sys, tty, termios
    def unix_getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    return unix_getch


__getch = None
if platform.system() == 'Windows':
    __getch = __win_create_getch()
elif platform.system()  == 'Linux':
    __getch = __unix_create_getch()
else:
    raise print('Platform OS Unsupported')


def getch():
    """Gets a single character from standard input.  Does not echo to the screen."""
    return __getch()

#NOT FOR UNIX!!!
#def getchar():
#    getch().decode("utf-8")


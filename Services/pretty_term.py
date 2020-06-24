import sys

class Style:
    reset=0
    bold=1
    dim=2
    underline=4
    blink=5
    reverse=7
    hidden=8
    reset_bold=21
    reset_dim=22
    reset_underline=24
    reset_blink=25
    reset_reverse=27
    reset_hidden=28

class Foreground:
    default=39
    black=30
    red=31
    green=32
    yellow=33
    blue=34
    magenta=35
    cyan=36
    light_gray=37
    dark_gray=90
    light_red=91
    light_green=92
    light_yellow=93
    light_blue=94
    light_magenta=95
    light_cyan=96
    white=97

    def color_number(self, num):
        if not isinstance(num, int):
            raise Exception('Error: Foreground color must be and integer.')
        if num < 1 or num > 256:
            raise Exception('Error: Foreground color number out of range, must be between 1 and 256.')
        return f"38;5;{num}"

class Background:
    default=49
    black=40
    red=41
    green=42
    yellow=43
    blue=44
    magenta=45
    cyan=46
    light_gray=47
    dark_gray=100
    light_red=101
    light_green=102
    light_yellow=103
    light_blue=104
    light_magenta=105
    light_cyan=106
    white=107

    def color_number(self, num):
        if not isinstance(num, int):
            raise Exception('Error: Background color must be and integer.')
        if num < 1 or num > 256:
            raise Exception('Error: Background color number out of range, must be between 1 and 256.')
        return f"48;5;{num}"

class Colors:
    foreground=Foreground()
    background=Background()

    @classmethod
    def get_color(cls, color='default', isForeground=True):
        if isinstance(color, int):
            if isForeground:
                return cls.foreground.color_number(color)
            return cls.background.color_number(color)
        if color.startswith('f_'):
            return getattr(cls.foreground, color[2:])
        if color.startswith('b_'):
            return getattr(cls.background, color[2:])
        if isForeground:
            return getattr(cls.foreground, color)
        return getattr(cls.background, color)

def get_code(arg, isForeground=True):
    try:
        return Colors().get_color(arg, isForeground)
    except AttributeError:
        try:
            return getattr(Style, arg)
        except AttributeError:
            raise Exception(f"Error: {arg} not recognized.")

def cprint(text='', *args):
    if sys.stdout.isatty() and len(args) > 0:
        code = ';'.join([str(get_code(a)) for a in args])
        print(f"\033[{code}m{text}\033[{Style.reset}m")
    else:
        print(text)
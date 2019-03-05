from DP import Dynamic
from Things import Things
from Funpiler import Funpiler
import argparse

def dp_flags(sub):
    dp = Dynamic()
    dp_parser = sub.add_parser("dp", help="Runs dynamic programming scripts.")
    # Confilcting arguments are mutually exclusive
    dp_tools = dp_parser.add_mutually_exclusive_group()

    dp_tools.add_argument(
        '-s',
        '--sum-subset',
        help=Dynamic.sum_subset.__doc__,
        nargs=2,
        metavar=('S="1,2,..."', 'N'),
        default=False
        )
    dp_tools.add_argument(
        '-f',
        '--fib',
        help=Dynamic.fibonacci.__doc__,
        type=int,
        metavar=('N'),
        default=False
        )
    dp_tools.add_argument(
        '-l',
        '--lcs',
        help=Dynamic.LCS.__doc__,
        nargs=2,
        metavar=('X', 'Y'),
        default=False
        )
    dp_parser.set_defaults(func=dp.start)

def things_flags(sub):
    things = Things()
    things_parser = sub.add_parser("things", help=Things.__doc__)
    # Confilcting arguments are mutually exclusive
    things_tools = things_parser.add_mutually_exclusive_group()

    things_tools.add_argument(
        '-p',
        '--pennys-game',
        help=Things.pennys_game.__doc__,
        action='store_true',
        default=False
        )
    things_parser.set_defaults(func=things.start)

def funpiler_flags(sub):
    funpiler = Funpiler()
    funpiler_parser = sub.add_parser("funpiler", help=Funpiler.__doc__)
    # Confilcting arguments are mutually exclusive
    funpiler_tools = funpiler_parser.add_mutually_exclusive_group()

    funpiler_tools.add_argument(
        '-t',
        '--tokenize',
        help=Funpiler.scan.__doc__,
        type=str,
        metavar=('CODE/FILE'),
        default=False
        )
    funpiler_tools.add_argument(
        '-l',
        '--logic',
        help=Funpiler.logic.__doc__,
        type=str,
        metavar=('CODE/FILE'),
        default=False
        )
    funpiler_parser.set_defaults(func=funpiler.start)

def pdfer_flags(sub):
    pdfer = Funpiler()
    pdfer_parser = sub.add_parser("pdfer", help=Funpiler.start_pdf.__doc__)
    
    pdfer_parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='PDF File location.',
        default=False
        )
    pdfer_parser.add_argument(
        '-t',
        '--tokens',
        action='store_true',
        help='Display the tokenized version of the object.',
        default=False
        )
    pdfer_parser.add_argument(
        '-r',
        '--raw',
        type=int,
        help='Display the raw version of the object.',
        metavar=('VERBOSE_LEVEL'),
        default=False
        )
    pdfer_parser.add_argument(
        '-p',
        '--parsed',
        action='store_true',
        help='Display the parsed version of the object.',
        default=False
        )
    pdfer_parser.add_argument(
        '-o',
        '--object-number',
        type=int,
        help='Get an object from the pdf using the cross-reference table.',
        default=False
        )
    pdfer_parser.add_argument(
        '-n',
        '--fonts',
        type=int,
        help='Get as many fonts from the starting object number.',
        default=False
        )
    pdfer_parser.add_argument(
        '-u',
        '--unicodes',
        type=int,
        help='Get unicode object for each font from the starting object number.',
        default=False
        )
    pdfer_parser.add_argument(
        '-T',
        '--page-text',
        type=int,
        help='Get text from a page.',
        default=False
        )
    pdfer_parser.add_argument(
        '-a',
        '--all',
        action='store_true',
        help='Display the both the raw and tokenized version of the object.',
        default=False
        )
    pdfer_parser.add_argument(
        '-s',
        '--sect',
        type=int,
        nargs=2,
        help='Get a section of the pdf file given the start and end in bytes.',
        metavar=('START', 'END')
        )
    pdfer_parser.set_defaults(func=pdfer.start_pdf)

def create_flags():
    p = argparse.ArgumentParser(prog="FUN", description='Run rando funscripts with shell.')
    # Create subparsers for applications.
    sub = p.add_subparsers(help="choose an application to run")
    dp_flags(sub)
    things_flags(sub)
    funpiler_flags(sub)
    pdfer_flags(sub)
    return p

if __name__ == '__main__':
    # Create all of the flags.
    parser = create_flags()
    # Parse user input to match flags.
    args = parser.parse_args()
    # Run functions.
    args.func(args)
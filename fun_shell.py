from DP import Dynamic
from Things import Things
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

def create_flags():
    p = argparse.ArgumentParser(prog="FUN", description='Run rando funscripts with shell.')
    # Create subparsers for applications.
    sub = p.add_subparsers(help="choose an application to run")
    dp_flags(sub)
    things_flags(sub)
    return p

if __name__ == '__main__':
    # Create all of the flags.
    parser = create_flags()
    # Parse user input to match flags.
    args = parser.parse_args()
    # Run functions.
    args.func(args)
from DynamicPrograms import Dynamic
from Things import Things
from Funpiler import Funpiler
from PDFer import PDFer
from ImageProcessing import ImageController
from Config import Configuration
import argparse

def dp_flags(sub):
    dp = Dynamic()
    dp_parser = sub.add_parser("dyno", help="Runs dynamic programming scripts.")
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
    dp_tools.add_argument(
        '-e',
        '--edit-distance',
        help=Dynamic.minimum_edit_distance.__doc__,
        nargs=2,
        metavar=('X', 'Y'),
        default=False
        )
    dp_tools.add_argument(
        '-w',
        '--word-image',
        type=str,
        help=Dynamic.similarity_seq_image.__doc__,
        default=False
        )
    dp_parser.set_defaults(func=dp.start)

def things_flags(sub):
    things = Things()
    things_parser = sub.add_parser("things", help=Things.__doc__)
    # Confilcting arguments are mutually exclusive
    things_tools = things_parser.add_mutually_exclusive_group()

    things_tools.add_argument(
        '-g',
        '--gauss-trick',
        help=Things.gauss_trick.__doc__,
        action='store_true',
        default=False
        )
    things_tools.add_argument(
        '-p',
        '--pennys-game',
        help=Things.pennys_game.__doc__,
        action='store_true',
        default=False
        )
    things_tools.add_argument(
        '-a',
        '--author',
        help="print quotes from an author",
        type=str,
        default=False
        )
    
    things_parser.add_argument(
        '-s',
        '--start',
        type=int,
        help='Number to start the sum from.',
        default=1
        )
    things_parser.add_argument(
        '-e',
        '--end',
        type=int,
        help='Number to sum to.',
        default=10
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
    pdfer = PDFer()
    pdfer_parser = sub.add_parser("pdfer", help=PDFer.start.__doc__)
    
    pdfer_parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='PDF File location.',
        default=False
        )
    pdfer_parser.add_argument(
        '-b',
        '--base',
        action='store_true',
        help='Test the pdf base.',
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
        '-i',
        '--page-images',
        type=int,
        help='Get image objects from a page.',
        default=False
        )
    pdfer_parser.add_argument(
        '-I',
        '--view-image',
        nargs='+',
        help='Display image from a page.(must provide page object number, you can add aditional image names)',
        default=False
        )
    pdfer_parser.add_argument(
        '-S',
        '--save-image',
        action='store_true',
        help='Save displayed image from a page.',
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
    pdfer_parser.set_defaults(func=pdfer.start)

def impro_flags(sub):
    impro = ImageController()
    impro_parser = sub.add_parser("impro", help=ImageController.start.__doc__)
    impro_tools = impro_parser.add_mutually_exclusive_group()

    impro_parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Image File location.',
        default=False
        )
    impro_parser.add_argument(
        '-p',
        '--operations',
        nargs='+',
        help='List of operation objects to preform on the image.',
        default=False
        )
    impro_parser.add_argument(
        '-d',
        '--ocr-data',
        action='store_true',
        help='Print out the complete data from the ocr process.',
        default=False
        )
    impro_tools.add_argument(
        '-H',
        '--histogram',
        action='store_true',
        help='Plot the histogram of the image.',
        default=False
        )
    impro_tools.add_argument(
        '-o',
        '--ocr',
        action='store_true',
        help='OCR the image and print out the text.',
        default=False
        )
    impro_tools.add_argument(
        '-m',
        '--method',
        action='store_true',
        help='Run the Harraj and Raissouni Pre-Processing method.',
        default=False
        )
    impro_tools.add_argument(
        '-r',
        '--resize',
        type=str,
        help='Resize the image to be displayed.',
        default=False
        )
    impro_parser.set_defaults(func=impro.start)

def config_flags(sub):
    config = Configuration()
    # Config application descriptor.
    config_parser = sub.add_parser("config", help="Configures 'cm' for the user's instance")
    # Display section from local.ini file.
    config_parser.add_argument(
        "-s",
        "--section",
        help="Print a section from the config file (case doesn't matter)",
        nargs=1,
        metavar=('SECT_NAME')
        )
    # Adds and updates sections and/or entries to local.ini.
    config_parser.add_argument(
        "--set",
        help="if 1 argument is provided then it is added as a section. If 3 args are provided then the entry SECT KEY VALUE is added/updated",
        nargs='+'
        )
    # Deletes sections and/or entries from local.ini.
    config_parser.add_argument(
        "-d",
        "--delete",
        help="if 1 argument is provided then the section is deleted. If 2 args are provided then the entry SECT KEY VALUE is deleted",
        nargs='+'
        )
    # Returns the initial local fields established in the config.setup().
    config_parser.add_argument(
        "-m",
        "--merge",
        help="Merges the user defined entries with the initial global configuration",
        action='store_true',
        default=False
        )
    # Set the function to run for this application.
    config_parser.set_defaults(func=config.start)

def create_flags():
    p = argparse.ArgumentParser(prog="FUN", description='Run rando funscripts with shell.')
    # Create subparsers for applications.
    sub = p.add_subparsers(help="choose an application to run")
    dp_flags(sub)
    things_flags(sub)
    funpiler_flags(sub)
    pdfer_flags(sub)
    impro_flags(sub)
    config_flags(sub)
    return p

if __name__ == '__main__':
    # Create all of the flags.
    parser = create_flags()
    # Parse user input to match flags.
    args = parser.parse_args()
    # Run functions.
    args.func(args)
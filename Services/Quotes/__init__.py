from .quotes import Quotes

description = f"{Quotes.__doc__}.(default will fetch the 'quote of the day')"

def start(args):
    brainy_quote = Quotes()
    if args.search:
        brainy_quote.find_quotes(args.search, args.search_limit)
    else:
        brainy_quote.qotd()
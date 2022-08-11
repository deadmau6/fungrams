# Today in history module
from .history import HistoryChannel
from ..pretty_term import cprint

def display_events(events):
    print()
    for event in events:
        intro = f"{event['topic']} - {event['year']}"
        header_line = ''.join(['-' * max(len(event['title']), len(intro))])
        cprint(intro, 'green')
        cprint(event['title'], 'bold', 'blue')
        cprint(header_line, 'dark_gray')
        cprint(event['summary'])
        cprint(event['link'], 'light_cyan')
        cprint()

def display_feat(feat):
    print()
    citation = feat.get('citation', {})
    title = citation.get('Article Title', {})
    body = feat['body']
    links = []
    cprint(f"\t{title.get('text', 'Today in History')}", 'yellow', 'bold', 'underline')
    print()
    for section in body:
        if section.get('links'):
            links.extend(section.get('links'))
        print()
        print(section['text'])
    print()
    if len(citation.keys()) > 0:
        cprint('Citation:', 'bold', 'blue')
        for k,v in citation.items():
            cprint(f"\t{k} : {v['text']}", 'dark_gray')
            if v.get('link'):
                cprint(f"\t({v.get('link')})", 'light_cyan')
            print()
    if len(links) > 0:
        cprint('Related Links:', 'bold', 'magenta')
        for l in links:
            cprint(f"\t* {l}", 'light_cyan')

def start(args):
    tih = None
    if args.website == 'history channel':
        tih = HistoryChannel()
    feat, events = tih.get_history_data(args)
    if args.featured:
        display_feat(feat)
    if args.events:
        display_events(events)
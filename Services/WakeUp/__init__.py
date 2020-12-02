from .wake_up import WakeUp
from pprint import pprint

description = f"{WakeUp.__doc__}.(default will run the 'default' group command)"

def start(args):
    wake_up = WakeUp()
    if len(args.add) >= 1:
        err, res = None, None
        if args.command:
            err, res = wake_up.add_command(args.command, args.add[0])
        else:
            err, res = wake_up.add_group_command(args.group, args.add)
        print(err, res)
    elif len(args.update) >= 1:
        err, res = None, None
        if args.command:
            err, res = wake_up.add_command(args.command, args.update[0], True)
        else:
            err, res = wake_up.add_group_command(args.group, args.update, True)
        print(err, res)
    elif args.list:
        pprint(wake_up.get_config())
    elif args.command:
        wake_up.process_single_command(args.command, args.timeout)
    else:
        wake_up.process_group_command(args.group, args.timeout)
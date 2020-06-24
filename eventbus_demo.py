"""This file is only used to test the manager."""
from multiprocessing import freeze_support
from Services.EventBus import Manager

if __name__ == '__main__':
    freeze_support()
    message = "This file is only used to test the manager."
    events = [
        {'id': 121, 'type': 'reverse', 'message': message},
        {'id': 123, 'type': 'reverse', 'message': message},
        {'id': 124, 'type': 'compress', 'message': message},
        {'id': 125, 'type': 'yell', 'message': message}
    ]
    manager = Manager()
    for e in events:
        manager.handle_request(e)
    manager.monitor()

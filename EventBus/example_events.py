from multiprocessing import Process
from .event_base import EventBase
import random, time

class ReverseMessage(EventBase, Process):
    """The ReverseMessage class

    This class is a simple event type that reverses a message one character at a time.
    This class is also a subclass of Process and can overwrite the `run()` method this
    way when a Class Instance calls the start() method it with promptly run the `run()`
    method.
    """

    def __init__(self, event_conn, event_id, event_str):
        # Create our connection object to the manager.
        EventBase.__init__(self, event_conn)
        # Subclass the Process module. 
        Process.__init__(self)
        self.event_id = event_id
        self.event_str = event_str
        # This is used to simulate varying computation times.
        self.wait_time = random.randrange(1, 3)

    def run(self):
        """This is like the main function to the individual Event Process."""
        rev_str = ''
        for c in self.event_str:
            # Parse through the event message one char at a time.
            if self.is_cancelled(timeout=0.1):
                # Periodically check for a cancellation request.
                self.report({'id': self.event_id, 'update': "cancelling", 'percent': -1, 'complete': False})
                break
            # Reverse the string.
            rev_str = f'{c}{rev_str}'
            # Determine the percentage complete.
            percent = int((len(rev_str) / len(self.event_str)) * 100)
            # Update the manager. 
            self.report({'id': self.event_id, 'update': rev_str, 'percent': percent, 'complete': False})
            """This portion is supposed to simulate computational work and it does, kinda.

            While this can accurately simulate the time aspect of work, it doeshowever do
            a poor job of simulating energy portion of work. In fact it does the exact
            opposite of spending energy, `time.sleep()` actually frees up resources.
            """
            time.sleep(self.wait_time)
        # Final Update.
        self.finish(conclusion={'id': self.event_id, 'update': rev_str, 'complete': True})

class CompressMessage(EventBase, Process):
    """The ReverseMessage class

    This class is a simple event type that filters the message one character at a time.
    This class is also a subclass of Process and can overwrite the `run()` method this
    way when a Class Instance calls the start() method it with promptly run the `run()`
    method.
    """

    def __init__(self, event_conn, event_id, event_str):
        # Create our connection object to the manager.
        EventBase.__init__(self, event_conn)
        # Subclass the Process module. 
        Process.__init__(self)
        self.event_id = event_id
        self.event_str = event_str.lower()
        # This is static time simulates varying computation times accross differing events.
        self.wait_time = 0.5

    def run(self):
        """This is like the main function to the individual Event Process."""
        rev_str = ''
        i = 0
        for c in self.event_str:
            # Parse through the event message one char at a time.
            i += 1
            if self.is_cancelled(timeout=0.1):
                # Periodically check for a cancellation request.
                self.report({'id': self.event_id, 'update': "cancelling", 'percent': -1, 'complete': False})
                break
            # Only add it to the update if it is a lowercase character.
            rev_str = f'{rev_str}{c}' if 97 <= ord(c) <= 122 else rev_str
            # Determine the percentage complete.
            percent = int((i / len(self.event_str)) * 100) 
            # Update the manager.
            self.report({'id': self.event_id, 'update': rev_str, 'percent': percent, 'complete': False})
            """This portion is supposed to simulate computational work and it does, kinda.

            While this can accurately simulate the time aspect of work, it doeshowever do
            a poor job of simulating energy portion of work. In fact it does the exact
            opposite of spending energy, `time.sleep()` actually frees up resources.
            """
            time.sleep(self.wait_time)
        # Final Update.
        self.finish(conclusion={'id': self.event_id, 'update': rev_str, 'complete': True})

class YellMessage(EventBase, Process):
    """The ReverseMessage class

    This class is a simple event type that capitalizes a message one character at a time.
    This class is also a subclass of Process and can overwrite the `run()` method this
    way when a Class Instance calls the start() method it with promptly run the `run()`
    method.
    """

    def __init__(self, event_conn, event_id, event_str):
        # Create our connection object to the manager.
        EventBase.__init__(self, event_conn)
        # Subclass the Process module. 
        Process.__init__(self)
        self.event_id = event_id
        # Capitalize the message.
        self.event_str = event_str.upper()
        # This is static time simulates varying computation times accross differing events.
        self.wait_time = 0.1

    def run(self):
        """This is like the main function to the individual Event Process."""
        rev_str = ''
        for c in self.event_str:
            # Parse through the event message one char at a time.
            if self.is_cancelled(timeout=0.1):
                # Periodically check for a cancellation request.
                self.report({'id': self.event_id, 'update': "cancelling", 'percent': -1, 'complete': False})
                break
            # Reconstruct the message one char at a time.
            rev_str = f'{rev_str}{c}'
            # Determine the percentage complete.
            percent = int((len(rev_str) / len(self.event_str)) * 100) 
            # Update the manager.
            self.report({'id': self.event_id, 'update': rev_str, 'percent': percent, 'complete': False})
            """This portion is supposed to simulate computational work and it does, kinda.

            While this can accurately simulate the time aspect of work, it doeshowever do
            a poor job of simulating energy portion of work. In fact it does the exact
            opposite of spending energy, `time.sleep()` actually frees up resources.
            """
            time.sleep(self.wait_time)
        # Final Update.
        self.finish(conclusion={'id': self.event_id, 'update': rev_str, 'complete': True})


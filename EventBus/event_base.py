import select

class EventBase:
    """The EventBase class

    This class is a parent class as for the event types.
    Therefore this class should only be inherited!
    This class holds the basic communication with the manager.
    """

    def __init__(self, event_conn):
        # Connection to the manager.
        self.event_conn = event_conn

    def report(self, status_report):
        """Send an update to the manager."""
        self.event_conn.send(status_report)

    def finish(self, conclusion):
        """Conclusion message to the manager."""
        self.event_conn.send(conclusion)
        self.event_conn.close()

    def is_cancelled(self, timeout=1):
        """This checks the pipe to see if the manager has sent a message to the event."""
        return self.event_conn.poll(timeout)


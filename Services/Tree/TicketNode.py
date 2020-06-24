from .Node import Node

class TicketNode(Node):
    """ A node extention for objects with a ticket_num attribute """
    def get(self):
        return self.data['ticket_num']

    def isLeft(self, val):
        return val['ticket_num'] < self.data['ticket_num']

    def isRight(self, val):
        return val['ticket_num'] > self.data['ticket_num']
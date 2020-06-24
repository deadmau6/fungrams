from .OrderedTree import OrderedTree
from .TicketNode import TicketNode

class BinarySearch(OrderedTree):
    """ Implementation of a Binary search tree"""
    def insert(self, val):
        self.root = BinarySearch.__insert(self.root, val)

    def __insert(root, val):
        if root == None:
            return TicketNode(val)
 
        if root.isLeft(val):
            root.set_left(BinarySearch.__insert(root.get_left(), val))
        elif root.isRight(val):
            root.set_right(BinarySearch.__insert(root.get_right(), val))
        else:
            return None

        return root

    def find(self, val):
        return BinarySearch.__find(self.root, val)

    def __find(root, val):
        if root == None:
            return None
        if root.get() == val:
            return root
        if val < root.get():
            return BinarySearch.__find(root.get_left(), val)
        else:
            return BinarySearch.__find(root.get_right(), val)
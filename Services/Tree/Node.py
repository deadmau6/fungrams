class Node:
    """ Node Object should onlt be used directly by tree"""
    def __init__(self, data, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

    def get(self):
        return self.data

    def set(self, data):
        self.data = data

    def get_right(self):
        return self.right

    def get_left(self):
        return self.left

    def set_right(self, val):
        self.right = val

    def set_left(self, val):
        self.left = val

    def get_children(self):
        return self.left, self.right

    def has_children(self):
        return (self.left != None) or (self.right != None)

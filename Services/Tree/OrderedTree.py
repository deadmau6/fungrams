from .Node import Node

class OrderedTree:
    """ The base Tree structure. """
    def __init__(self, root=None):
        self.root = root
        self.height = 0
        self.total_nodes = 0
        self.total_edges = 0
        self.traversal = []

    def clean_traverse(self):
        self.traversal = []
        
    def print_order(self, order):
        if order == 'in':
            self.inorder(self.root)
            print('Inorder: {}'.format(self.traversal))
        elif order == 'pre':
            self.preorder(self.root)
            print('Preorder: {}'.format(self.traversal))
        elif order == 'post':
            self.postorder(self.root)
            print('Postorder: {}'.format(self.traversal))
        self.clean_traverse()

    def inorder(self, root):
        if root == None:
            return None

        self.inorder(root.get_left())
        self.traversal.append(root.get())
        self.inorder(root.get_right())
        
    def preorder(self, root):
        if root == None:
            return None

        self.traversal.append(root.get())
        self.preorder(root.get_left())
        self.preorder(root.get_right())
        
    def postorder(self, root):
        if root == None:
            return None

        self.postorder(root.get_left())
        self.postorder(root.get_right())
        self.traversal.append(root.get())

    def set_metrics(self, root, h=0):

        if root:
            self.total_nodes += 1

        if self.height < h:
            self.height = h

        left, right = root.get_children()
        if left:
            self.total_edges += 1
            hg = h + 1
            self.set_metrics(left, hg)
        if right:
            self.total_edges += 1
            hg = h + 1
            self.set_metrics(right, hg)

    def print_metrics(self):
        self.set_metrics(self.root)
        print('Height: {}'.format(self.height))
        print('Number of Nodes: {}'.format(self.total_nodes))
        print('Number of Edges: {}'.format(self.total_edges))
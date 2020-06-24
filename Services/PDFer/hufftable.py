import heapq
import os

class HuffNode:
    def __init__(self, char, code):
        self.char = char
        self.code = code

class HuffTable:
    def __init__(self, ht):
        self.heap = []
        self.compact_huff = ht

    def generate_huff_tree(self):
        '''
        This method finds the huffman codes for each symbol, it does not construct the whole tree.
        The leaves of the tree are constructed left to right, any node which has a character is the end of that branch.
        Therefore the next character is coded in one node to the right (+1) of the previously coded character at it's coresponding row (append '0's)
        '''
        for r, row in enumerate(self.compact_huff, 1):
            for char in row:
                if not self.heap:
                    self.heap.append(HuffNode(char, '0' * r))
                    continue
                prev_node = self.heap[-1]
                if (len(prev_node.code) == r):
                    code = bin(int(prev_node.code, 2) + 1)
                    self.heap.append(HuffNode(char, code[2:]))
                else:
                    node_right = bin(int(prev_node.code, 2) + 1)
                    row_extend = (r - len(prev_node.code))
                    code = str(node_right) + ('0' * row_extend)
                    self.heap.append(HuffNode(char, code[2:]))

        return self.heap

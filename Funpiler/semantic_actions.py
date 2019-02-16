from .symbol_table import SymbolTable

class SemanticActions:

    def __init__(self, root_table=None):
        self.root_table = root_table

    def create_table(self, scope):
        self.root_table = SemanticActions._create_table(self.root_table, scope)

    @staticmethod
    def _create_table(root_table, scope):
        if root_table == None:
            return SymbolTable(scope)

        table = SymbolTable(scope, root_table)
        root_table.children.append(table)
        return table

    def find(self, name):
        return SemanticActions._find(self.root_table, name)

    @staticmethod
    def _find(root_table, name):
        if root_table == None:
            return None

        symbol = root_table.lookup(name)
        if symbol:
            return symbol
        else:
            return SemanticActions._find(root_table.parent, name)

    def insert_record(self, name, typ):
        self.root_table.insert_record(name, typ)

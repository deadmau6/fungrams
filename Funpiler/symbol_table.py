
class SymbolRecord:

    def __init__(self, name, typ):
        self.name = name
        self.type = typ
        self.state = None
        self.ident = hash((name, typ))
        

class SymbolTable:

    def __init__(self, scope, parent=None):
        self.table = {}
        self.scope = scope
        self.parent = parent
        self.children = []

    def insert(self, name, typ):
        if name in self.table:
            raise RuntimeError(f"{name} was already declared")

        self.table[name] = SymbolRecord(name, typ)

    def lookup(self, name):
        if name in self.table:
            return self.table[name]
        return False
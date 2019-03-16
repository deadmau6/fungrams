from pprint import pprint
class XRef:
    """Holds the xref"""

    def __init__(self, start, fname, xref=None):
        self.xref_start = start
        self.fname = fname
        self.table = self._create_table(xref) if xref else None

    def _create_table(self, xref):
        # self.table = { obj_number: (start_byte, end_byte) }
        sorted_addresses = sorted([v['byte_offset'] for k, v in xref.items()])

        table = {}
        
        for k, v in xref.items():
            start = v['byte_offset']
            start_index = sorted_addresses.index(start)
            
            if start_index == len(sorted_addresses) - 1:
                table[k] = (start, self.xref_start)
            else:
                table[k] = (start, sorted_addresses[start_index + 1])

        return table

    def update_table(self, xref):
        self.table = self._create_table(xref)

    def get_object(self, obj_number):
        """From the file, returns bytes of the object."""
        if isinstance(obj_number, tuple):
            obj_number = obj_number[0]

        start, end = self.table[obj_number]

        #TODO: check if xref table is in RAM(redis?)
        with open(self.fname, 'rb') as f:
            f.seek(start)
            data = f.read(end - start)

        return data

    def toJSON(self):
        return {
            'start': self.xref_start,
            'table': self.table
        }
    
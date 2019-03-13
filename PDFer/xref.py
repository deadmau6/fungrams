
class XRef:
    """Holds both the xref and trailer"""

    def __init__(self, start, fname):
        self.table = None
        self.xref_start = start
        self.fname = fname

    def create_table(self, xref):
        # self.table = { obj_number: (start_byte, end_byte) }
        sorted_addresses = sorted([v['byte_offset'] for k, v in xref.items()])
        
        for k, v in xref.items():
            start = v['byte_offset']
            start_index = sorted_addresses.index(start)
            
            if s_index == len(sorted_addresses) - 1:
                self.table[k] == (start, self.xref_start)
            else:
                self.table[k] == (start, sorted_addresses[s_index + 1])

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
        
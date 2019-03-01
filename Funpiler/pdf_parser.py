from .recursive_parser import RecursiveParser
from pprint import pprint

class PDFParser(RecursiveParser):

    def parse(self, tokens):
        self.tokens = tokens
        self.advance()
        ref_table = self.xref()
        trailer = self.trailer()
        return ref_table, trailer

    def parse_indirect_object(self, tokens):
        self.tokens = tokens
        self.advance()
        obj_number, gen_number, vals = self._indirect_object()
        self.match('NEWLINE')
        return {
            'obj_number': obj_number,
            'gen_number': gen_number,
            'values': vals
        }

    def _skip_space(self):
        if self.current == None:
            return False
        if self.current.kind == 'NEWLINE':
            self.match('NEWLINE')
            return True
        if self.current.kind == 'WHTSPC':
            self.match('WHTSPC')
            return True
        return False

    def _any_object(self):
        # Get rid of any floating line breaks.
        self._skip_space()

        if self.current.kind == 'OPR':
            return self._name_object()

        if self.current.kind == 'NUMBER':
            return self._indirect_object()

        if self.current.kind == 'PAREN':
            return self._literal_string_object()

        if self.current.kind == 'SQUARE':
            return self._array_object()

        if self.current.kind == 'stream':
            return self._stream_object()

        if self.current.kind == 'ARROW':
            return self._hex_string_object()

        if self.current.kind == 'true':
            self.match('true')
            return True

        if self.current.kind == 'false':
            self.match('false')
            return False

        self.match('null')
        return None

    def _name_object(self):
        sign = self.match('OPR')
        if sign == '/':
            name = []
            while not self._skip_space():

                if self.current.kind == 'OPR' and self.current.value == '/':
                    break
                
                if self.current.kind in ['PERCENT','ARROW','PAREN','CURLY','SQUARE']:
                    break

                val = self.match(None)

                if not isinstance(val, str):
                    val = str(val)
                
                name.append(val)
            
            return ''.join(name)

        return self._numeric_object(sign=sign)

    def _numeric_object(self, sign=None):
        if not sign:
            return self.match('NUMBER')
        if sign == '+':
            return self.match('NUMBER')

        return -self.match('NUMBER')

    def _indirect_object(self):
        obj_number = self.match('NUMBER')
        self._skip_space()

        if self.current.kind != 'NUMBER':
            # normal number
            return obj_number

        gen_number = self.match('NUMBER')
        self._skip_space()

        if self.current.kind == 'ID' and self.current.value == 'R':
            # Indirect Reference
            ref = self.match('ID', 'R')
            self._skip_space()
            return obj_number, gen_number, ref

        if self.current.kind != 'obj':
            # just two numbers (!WILL RETURN AS TUPLE!)
            return obj_number, gen_number

        self.match('obj')
        obj_vals = []
        while self.current.kind != 'endobj':
            
            if self._skip_space():
                continue

            obj_vals.append(self._any_object())

            if self.current is None:
                break
        self.match('endobj')

        return obj_number, gen_number, obj_vals

    def _literal_string_object(self):
        self.match('PAREN', '(')
        paren_count = 1
        literal_string = []
        while paren_count != 0:
            
            if self.current.kind == 'PAREN':
                val = self.match('PAREN')
                if val == '(':
                    paren_count += 1
                else:
                    paren_count -= 1
            else:
                val = self.match(None)
                if not isinstance(val, str):
                    val = str(val)
                literal_string.append(val)

        return ''.join(literal_string)

    def _array_object(self):
        self.match('SQUARE', '[')
        arr = []
        while self.current.kind != 'SQUARE':
            if self._skip_space():
                continue

            arr.append(self._any_object())

        self.match('SQUARE', ']')
        return arr

    def _stream_object(self):
        self.match('stream')
        stream = []
        while self.current.kind != 'endstream':
            
            val = self.match(None)
            
            if not isinstance(val, str):
                val = str(val)
            
            stream.append(val)
            
            if self.current is None:
                break
        self.match('endstream')
        
        return bytes(''.join(stream), 'utf-8')

    def _hex_string_object(self):
        #First ARROW must be removed
        self.match('ARROW', '<')
        if self.current.kind == 'ARROW':
            return self._dictionary_object()

        hex_string = []
        while self.current.kind != 'ARROW':
            val = self.match(None)
            
            if not isinstance(val, str):
                val = str(val)

            hex_string.append(val)
        
        self.match('ARROW', '>')

        return ''.join(hex_string)

    def _dictionary_object(self):
        #One ARROW should have already been removed
        self.match('ARROW', '<')
        arrow_count = 2
        d_obj = {}
        while arrow_count != 0:
            if self._skip_space():
                continue

            if self.current.kind == 'ARROW':
                val = self.match('ARROW', '>')
                arrow_count -= 1
                continue

            key = self._name_object()
            value = self._any_object()
            d_obj[key] = value

        return d_obj

    def trailer(self):
        self.match('trailer')
        self.match('NEWLINE')
        self.match('ARROW')
        trailer = self._dictionary_object()
        return {k.lower(): v for k, v in trailer.items()}

    def xref(self):
        self.match('xref')
        self.match('NEWLINE')
        table = {}
        while self.current.kind != 'trailer':
            obj_num = self.match('NUMBER')
            self._skip_space()
            sect_size = self.match('NUMBER')
            self.match('NEWLINE')

            for k, b, g, u in self._xref_section(obj_num, sect_size):
                table[k] = { 'byte_offset': b, 'gen_number': g, 'in_use': u }
            if self.current is None:
                break
        return table

    def _xref_section(self, obj_num, sect_size):
        obj_number = obj_num
        while obj_number < sect_size:
            byte_offset = self.match('NUMBER')
            self._skip_space()
            gen_number = self.match('NUMBER')
            self._skip_space()
            use_flag = self.match('ID') == 'n'
            self._skip_space()
            self.match('NEWLINE')
            yield obj_number, byte_offset, gen_number, use_flag
            obj_number += 1

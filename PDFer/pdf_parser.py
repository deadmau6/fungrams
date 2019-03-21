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
        self._skip_space()
        return {
            'obj_number': obj_number,
            'gen_number': gen_number,
            'values': vals
        }

    def parse_to_unicode(self, tokens):
        self.tokens = tokens
        self.advance()
        cid_init = self._name_object()
        proc_set_k = self._name_object()
        proc_set_arr = []
        while self.current.kind != 'NEWLINE':
            if self._skip_space():
                continue
            if self.current.kind == 'ID':
                val = self.match('ID')
                if val == 'begin':
                    break
                else:
                    proc_set_arr.append(val)
        self._skip_space()

        pre_crap = []
        while self.current.kind != 'begincmap':
            pre_crap.append(self.match(None))
            self._skip_space()

        info, cmap = self._cmap()
        
        self._skip_space()
        post_crap = []
        while self.current != None:
            post_crap.append(self.match(None))
            self._skip_space()

        return {
            'proc_set': proc_set_arr,
            'info': info,
            'cmap': cmap,
            'pre': pre_crap,
            'post': post_crap
        }

    def parse_content(self, tokens):
        self.tokens = tokens
        self.advance()
        return self._content_stream()

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
            elif self.current.value == '\\':
                self.match(None)
                if self.current.kind == 'PAREN':
                    self.match(None)

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

    def _literal_byte_string(self):
        self.match('PAREN', '(')
        paren_count = 1
        literal_bytes = []
        while paren_count != 0:
            
            if self.current.kind == 'PAREN':
                val = self.match('PAREN')
                if val == '(':
                    paren_count += 1
                else:
                    paren_count -= 1
            elif self.current.value == b'\\':
                #Escape literal strings.
                self.match(None)
                if self.current.kind == 'PAREN':
                    val = self.match(None)
                    if not isinstance(val, bytes):
                        val = bytes(val, 'utf-8')
                    literal_bytes.append(val)
                elif self.current.value == b'\\':
                    self.match(None)
                    #print(self.current.kind, self.current.value)

            else:
                val = self.match(None)
                if not isinstance(val, bytes):
                    val = bytes(val, 'utf-8')
                literal_bytes.append(val)

        return b''.join(literal_bytes)

    def _hex_bytes_object(self):
        #First ARROW must be removed
        self.match('ARROW', '<')

        hex_bytes = []
        while self.current.kind != 'ARROW':
            val = self.match(None)
            
            if not isinstance(val, str):
                val = str(val, 'utf-8')

            hex_bytes.append(val)
        
        self.match('ARROW', '>')

        return ''.join(hex_bytes)

    def _byte_name_object(self):
        self.match('OPR')
        name = []
        while not self._skip_space():
            if self.current.kind == 'OPR' and self.current.value == b'/':
                break
                
            if self.current.kind in ['PERCENT','ARROW','PAREN','CURLY','SQUARE']:
                break

            val = self.match(None)

            if not isinstance(val, str):
                val = str(val, 'utf-8')
                
            name.append(val)
            
        return ''.join(name)

    def _content_stream(self):
        text = []
        while self.current != None:
            if self.current.kind == 'BT':
                text.append(self._find_text())
            else:
                self.match(None)
        return text

    def _find_text(self):
        self.match('BT')
        font = 'other'
        b_text = []
        while self.current.kind != 'ET':
            if self.current.kind == 'PAREN':
                b_text.append(self._literal_byte_string())
            elif self.current.kind == 'ARROW':
                b_text.append(self._hex_bytes_object())
            elif self.current.kind == 'OPR' and self.current.value == b'/':
                font = self._byte_name_object()
            else:
                self.match(None)
        self.match('ET')
        self._skip_space()
        return font, b_text

    def _cmap(self):
        self.match('begincmap')
        meta_info = {}
        cmap = {}
        
        while self.current.kind != 'endcmap':
            
            if self._skip_space():
                continue

            if self.current.kind == 'NUMBER':
                key, value = self._cmap_entries()
                try:
                    cmap[key].extend(value)
                except KeyError:
                    cmap[key] = value
            else:
                key, value = self._cmap_meta_info()
                meta_info[key] = value
        
        self.match('endcmap')
        return meta_info, cmap

    def _cmap_meta_info(self):
        key = None
        values = []
        if self.current.kind == 'OPR':
            key = self._name_object()
            self._skip_space()
            value = self._any_object()
            self._skip_space()
        if self.current.kind == 'ID' and self.current.value == 'def':
            self.match(None)
        self._skip_space()
        return key, value

    def _cmap_entries(self):
        n = self.match('NUMBER')
        self._skip_space()
        if self.current.kind == 'begincodespacerange':
            return 'code_space_range', self._cmap_codespace()

        if self.current.kind == 'beginbfchar':
            return 'bf_char', self._cmap_bfchar()

        if self.current.kind == 'beginbfrange':
            return 'bf_range', self._cmap_bfrange()

    def _cmap_codespace(self):
        self.match('begincodespacerange')
        code_space = []

        while self.current.kind != 'endcodespacerange':
            self._skip_space()
            start_range = self._hex_string_object()
            self._skip_space()
            end_range = self._hex_string_object()
            self._skip_space()
            code_space.append((start_range, end_range))
        
        self.match('endcodespacerange')
        return code_space

    def _cmap_bfchar(self):
        self.match('beginbfchar')
        bfchars = []

        while self.current.kind != 'endbfchar':
            self._skip_space()
            src_code = self._hex_string_object()
            self._skip_space()
            dst_string = self._hex_string_object()
            self._skip_space()
            bfchars.append((src_code, dst_string))
        
        self.match('endbfchar')
        return bfchars

    def _cmap_bfrange(self):
        self.match('beginbfrange')
        bfrange = []

        while self.current.kind != 'endbfrange':
            self._skip_space()
            start_code = self._hex_string_object()
            self._skip_space()
            end_code = self._hex_string_object()
            self._skip_space()
            if self.current.kind == 'ARROW':
                dst_list = [self._hex_string_object()]
                bfrange.append((start_code, end_code, dst_list))
            else:
                bfrange.append((start_code, end_code, self._array_object()))
            self._skip_space()

        self.match('endbfrange')
        return bfrange

    def trailer(self):
        self.match('trailer')
        self._skip_space()
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
        while (obj_number - obj_num) < sect_size:
            byte_offset = self.match('NUMBER')
            self._skip_space()
            gen_number = self.match('NUMBER')
            self._skip_space()
            use_flag = self.match('ID') == 'n'
            while self._skip_space():
                pass
            yield obj_number, byte_offset, gen_number, use_flag
            obj_number += 1

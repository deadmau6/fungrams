from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from pprint import pprint
import numpy as np
import cv2 as cv
import zlib, re

class PDFObject:

    def __init__(self, fname, start):
        self.fname = fname
        self.xref_start = start
        self.scanner = PdfScanner()
        self.parser = PDFParser()
        self.xref_table, self.trailer = self._parse_xref()
        self.sorted_addresses = sorted([v['byte_offset'] for k, v in self.xref_table.items()])
        self.fonts = {}
        self.translation_table = {}
        self.catalog = {}

    def _end(self, start):
        s_index = self.sorted_addresses.index(start)
        if s_index == len(self.sorted_addresses) - 1:
            return self.xref_start
        else:
            return self.sorted_addresses[s_index + 1]

    def get_root_num(self):
        return self.trailer['root'][0]

    def raw_catalog(self, more=False):
        root_num = self.trailer['root'][0]
        return self.get_raw_object(root_num, more)

    def create_catalog(self):
        root_num = self.trailer['root'][0]
        return self.get_indirect_object(root_num)

    def get_indirect_object(self, obj_number, search_stream=False, decode_stream=True):
        data = self.get_raw_object(obj_number, more=True)

        if not search_stream:
            return self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))
        
        stream_regex = re.compile(br'(.*stream[\r\n]+)(.*?)(endstream.*)', re.S)
        
        m = re.match(stream_regex, data)
        
        if m:
            match = m.groups()
            info = self.parser.parse_indirect_object(self.scanner.tokenize(str(match[0] + match[2], 'utf-8')))
            stream = self._raw_stream(info['values'], match[1], decode_stream)
            return info, stream

        return self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))

    def get_raw_object(self, obj_number, more=False):
        start = self.xref_table[obj_number]['byte_offset']
        end = self._end(start)

        with open(self.fname, 'rb') as f:
            f.seek(start)
            data = f.read(end - start)

        if more:
            return data
        return str(data, 'utf-8')

    def get_resources(self, resource_obj):
        if isinstance(resource_obj, tuple):
            return self.get_indirect_object(resource_obj[0])['values'][0]

        if 'Resources' in resource_obj:
            return self.get_resources('Resources')

        return resource_obj 

    def get_fonts(self, obj_number):
        """Preferably start with a Resources Object"""
        if obj_number is None:
            return None

        obj = self.get_indirect_object(obj_number)
        fnt = None
        ret_val = None
        for item in obj['values']:
            # Recur to Font.
            if 'Pages' in item:
                ret_val = item['Pages'][0]
                break

            if 'Kids' in item:
                first_kid = item['Kids'][0]
                ret_val = first_kid[0]
                break

            if 'Resources' in item:
                resource = self.get_resources(item['Resources'])
                fnt = resource.get('Font')
                break

            if 'Font' in item:
                fnt = item['Font']
                break

        if isinstance(fnt, tuple):
            fnt = self.get_indirect_object(fnt[0])['values'][0]

        if fnt:
            for k, v in fnt.items():
                if k in self.fonts:
                    continue
                
                self.fonts[k] = self.get_indirect_object(v[0])['values'][0]

            return self.fonts

        return self.get_fonts(ret_val)

    def get_unicodes(self, obj_number):
        """Preferably start with a Resources Object"""
        if self.get_fonts(obj_number) is None:
            return "Error: No Fonts Found"
        
        for k,v in self.fonts.items():
            if 'ToUnicode' in v:
                info, u_stream = self.get_indirect_object(v['ToUnicode'][0], search_stream=True)
                res = self.parser.parse_to_unicode(self.scanner.tokenize(u_stream, convert_nums=False))
                self._update_translation_table(k, res['cmap'])

        return self.translation_table

    def get_page_text(self, obj_number):
        """
        Acrobat Versions 4.0 and 5.0 (PDF Versions 1.3 and 1.4, respectively)
        must use “ToUnicode” mapping files that are restricted to UCS-2 (Big Endian) encoding,
        which is equivalent to UTF-16BE encoding without Surrogates.
        """
        obj = self.get_indirect_object(obj_number)
        page = None
        for item in obj['values']:
            obj_typ = item.get('Type')
            if obj_typ == 'Page':
                page = item
                break

        if page is None:
            return "Error: please provide a page's object number."

        self.get_unicodes(obj['obj_number'])

        content = page['Contents'][0] if isinstance(page['Contents'], tuple) else page['Contents'][0][0]


        i, stream = self.get_indirect_object(content, search_stream=True, decode_stream=False)

        res = self.parser.parse_content(self.scanner.b_tokenize(stream))

        text_arr = []
        for entry in res:
            font, b_arr = entry
            text_arr.append(self._decode_content(font, b_arr))
        
        return page, i, text_arr

    def get_page_images(self, obj_number):
        obj = self.get_indirect_object(obj_number)
        page = None
        for item in obj['values']:
            obj_typ = item.get('Type')
            if obj_typ == 'Page':
                page = item
                break

        if page is None:
            return "Error: please provide a page's object number."

        x_obj = self.get_resources(page['Resources']).get('XObject')

        if x_obj is None:
            return "No images found"
        
        images = {}

        for name, loc in  x_obj.items():
            i, stream = self.get_indirect_object(loc[0], search_stream=True, decode_stream=False)
            info = None
            for item in i['values']:
                sub_type = item.get('Subtype') if isinstance(item, dict) else None
                if sub_type and sub_type.lower() == 'image':
                    info = item
                    break
            if info:
                images[name] = {
                    'info': info,
                    'stream': stream
                }

        return images

    def display_image(self, obj_number, name=None):
        images = self.get_page_images(obj_number)
        if isinstance(images, str):
            print(images)
            return

        iname, img_obj = (name, images.get(name)) if name else images.popitem()
        info = img_obj['info']
        w, h, color_space, bits_per_comp = (info['Width'], info['Height'], info.get('ColorSpace'), info.get('BitsPerComponent'))
        
        if not isinstance(color_space, str):
            color_space = self._find_color_space(color_space)

        color_depth = 1

        if color_space.lower().endswith('rgb'):
            color_depth = 3

        if color_space.lower().endswith('lab'):
            color_depth = 3

        if color_space.lower().endswith('cmyk'):
            # Fucking god dammit!
            # needs its own "SPECIAL CONVERSION"
            # Red = 255 * (1 - C) * (1 - K)
            # Green = 255 * (1 - M) * (1 - K)
            # Blue = 255 * (1 - Y) * (1 - K)
            color_depth = 4

        # This might only work because the bit depth is 8.
        # Pdf images can have differing bit depths to save space but
        # OpenCV only accepts uinsigned 8 bit integers (AKA 'uint8')
        # Coincidentally if the PDF's bit depth is 8 then it works like a charm
        # *HAVE NOT FOUND OR TESTED ON DIFFERENT BIT DEPTHS* 
        img = np.frombuffer(img_obj['stream'], dtype=np.uint8).reshape(h, w, color_depth)
        cv.imshow(iname, img)
        cv.waitKey(0)
        cv.destroyAllWindows()
        return

    def _find_color_space(self, color_space):
        if isinstance(color_space, list):
            best_option = None
            
            for color in color_space:
                if color.lower().endswith('gray'):
                    best_option = color
                    break
                if color.lower().endswith('rgb'):
                    best_option = color
                    break
                if color.lower().endswith('cmyk'):
                    best_option = color
                    break
                if color.lower().endswith('lab'):
                    best_option = color
                    break
                best_option = color

            return best_option


        obj = self.get_indirect_object(color_space[0], search_stream=True, decode_stream=False)
        
        if isinstance(obj, tuple):
            #we just want the info dict
            obj = obj[0]

        vals = obj['values'][0]

        if isinstance(vals, dict):
            color = None
            for k, v in vals.items():
                if k.lower() == 'alternate':
                    color = v
                    break
            return color

        elif isinstance(vals, list):
            potentials = []
            for cs in vals:
                if isinstance(cs, tuple):
                    potentials.append(self._find_color_space(cs))
                elif isinstance(cs, str):
                    potentials.append(cs)
            return self._find_color_space(potentials)

    def _update_translation_table(self, font_key, cmap):
        char_map = {}
        bf_chars = cmap.get('bf_char', [])
        for entry in bf_chars:
            key, val = entry
            char_map[key] = chr(int(format(val, '0>4'), 16))
        
        bf_range = cmap.get('bf_range', [])
        for entry in bf_range:

            u_start, u_end, val = entry
            start = int(format(u_start, '0>4'), 16)
            end = int(format(u_end, '0>4'), 16)

            if (end - start) == 0:
                char_map[u_start] = chr(int(format(val[0], '0>4'), 16))

            elif len(val) == 1:
                val_num = int(format(val[0], '0>4'), 16)

                for i in range(start, (end + 1)):
                    key = hex(i)[2:]
                    char_map[key] = chr(val_num)
                    val_num += 1

            else:
                for i in range(start, (end + 1)):
                    key = hex(i)[2:]
                    index = i - start
                    char_map[key] = chr(int(format(val[index], '0>4'), 16))

        self.translation_table[font_key] = char_map

    def _parse_xref(self):
        end_regex = re.compile(br'^%%EOF.*?', re.S)
        with open(self.fname, 'rb') as f:
            f.seek(self.xref_start, 0)
            lines = f.read().splitlines()
            ref_lines = []
            for l in lines:
                ref_lines.append(l)
                if re.match(end_regex, l):
                    break

            ref_table = b'\n'.join(ref_lines)

        xref, trailer = self.parser.parse(self.scanner.tokenize(str(ref_table, 'utf-8')))
        if 'prev' in trailer:
            self.xref_start = trailer['prev']
            x_2, t_2 = self._parse_xref()
            xref.update(x_2)
            trailer.update(t_2)
        return xref, trailer

    def _raw_stream(self, stream_info, stream_data, decode_stream=True):
        decomp_typ = None
        for item in stream_info:
            if 'Filter' in item:
                decomp_typ = item['Filter']
                break

        if decomp_typ.lower() == 'flatedecode':
            if decode_stream:
                return zlib.decompress(stream_data).decode('utf-8')
            else:
                return zlib.decompress(stream_data)

        return stream_data

    def _parse_content(self, obj_number):
        """
        Acrobat Versions 4.0 and 5.0 (PDF Versions 1.3 and 1.4, respectively)
        must use “ToUnicode” mapping files that are restricted to UCS-2 (Big Endian) encoding,
        which is equivalent to UTF-16BE encoding without Surrogates.
        """
        x = self.get_indirect_object(obj_number, search_stream=True, decode_stream=False)

        if isinstance(x, tuple):
            x = x[0]

        #res = self.parser.parse_content(self.scanner.b_tokenize(stream))
        #res = [t for t in self.scanner.b_tokenize(stream)]
        #pprint(res)
        return x

    def _decode_content(self, font, b_arr):
        if font in self.translation_table:
            return ''.join(self._remap(b_arr, font))

        f_encoding = self.fonts[font]['Encoding'].lower()

        if f_encoding.startswith('mac'):
            return ''.join([str(text, 'mac_roman') for text in b_arr])
        
        if f_encoding.startswith('winansi'):
            return ''.join([str(text, 'cp1252') for text in b_arr])

        if f_encoding.startswith('standard'):
            return ''.join([str(text, 'latin_1') for text in b_arr])

        return ''.join([str(text, 'utf-8') for text in b_arr])

    def _remap(self, b_stream, font):
        hx_arr = []
        for x in b_stream:
            try:
                hx_arr.append(x.hex())
            except Exception as e:
                # x must be a string which means it's already a hex string.
                hx_arr.append(x)

        hex_string = ''.join(hx_arr)
        translator = self.translation_table[font]
        text = []
        for a, b in zip(hex_string[::2], hex_string[1::2]):
            code = a+b
            if code in translator:
                text.append(translator[code])
            else:
                # user4369081 on stackoverflow
                text.append(bytearray.fromhex(code).decode())

        return ''.join(text)
        

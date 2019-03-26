import numpy as np
from pprint import pprint
import math, io, zlib

class FilterHelper:
    """Static methods to help reformat/unfilter compressed streams."""
    @staticmethod
    def tiff_prediction(bits_per_component, colors, columns, row_size, bpp, data):
        """Not yet implemented! only works on single row!"""
        # initialize the prediction line to all zeros
        predline = [0] * row_size
        # Might want to do separate methods
        if bits_per_component == 1:

            buff_in = predline[bpp - 1]
            for i in range(bpp, row_size, 8):
                buff_in = (buff_in << 8) | predline[i]
                predline[i] ^= buff_in >> colors

        elif bits_per_component == 8:
            for i in range(bpp, row_size):
                predline[i] += predline[i - colors]
        else:
            up_left_buffer = [0] * (colors + 1)
            bit_mask = (1 << bits_per_component) - 1
            
            buff_in = 0
            buff_out = 0
            
            bits_in = 0
            bits_out = 0
            
            j = bpp
            k = bpp
            for a in range(0, columns):
                for b in range(0, colors):
                    if bits_in < bits_per_component:
                        j += 1
                        buff_in = (buff_in << 8) | (predline[j] & 255)
                        bits_in += 8

                    up_left_buffer[b] += (buff_in >> (bits_in - bits_per_component)) & bit_mask

                    bits_in -= bits_per_component
                    buff_out = (buff_out << bits_per_component) | up_left_buffer[b]
                    bits_out += bits_per_component
                    if bits_out >= bits_per_component:
                        k += 1
                        predline[k] = buff_out >> (bits_out - 8)
                        bits_out -= 8

            if bits_out > 0:
                k += 1
                predline[k] = (buff_out << (8 - bits_out)) + (buff_in & ((1 << (8 - bits_out)) - 1))

        return final

    @staticmethod
    def png_prediction(columns, row_size, bpp, data):
        """ Sources:
        * https://github.com/davidben/poppler/blob/master/poppler/Stream.cc
        * https://github.com/davidben/poppler
        * https://www.w3.org/TR/PNG-Filters.html
        """
        k = 0
        # initialize the prediction line to all zeros
        predline = [0] * row_size
        final = []
        while k < len(data):
            # Each row is prefaced with a 'prediction'
            curr_pred = data[k]
            # "Cut off" the prediction byte
            k += 1
            # initialize an empty up_left_buffer (only used for paeth prediction)
            up_left_buffer = [0] * (bpp + 1)
            # iterate through the row/line
            for i in range(bpp, row_size):
                # just in case
                try:
                    raw = data[k]
                    k += 1
                except Exception as e:
                    break

                # This conditional is evalulated per line/row(AKA: curr_pred shouldn't change in this for loop)
                if curr_pred == 1:
                    # PNG(1) Sub
                    predline[i] = predline[i - bpp] + raw
                elif curr_pred == 2:
                    # PNG(2) Up
                    predline[i] += raw
                elif curr_pred == 3:
                    # PNG(3) Average
                    predline[i] = ((predline[i - bpp] + predline[i]) >> 1) + raw
                elif curr_pred == 4:
                    # PNG(4) Paeth
                    # slide the up_left_buffer one over to the right
                    for j in range(bpp, 0, -1):
                        up_left_buffer[j] = up_left_buffer[j - 1]
                    # set the start of the up_left_buffer to the current
                    up_left_buffer[0] = predline[i]

                    predline[i] = self._paeth_predictor(predline[i - bpp], predline[i], up_left_buffer[bpp]) + raw
                else:
                    # PNG(0) No prediction
                    predline[i] = raw
            # Each row/line is buffered by the previous line's pixel which eqauls bpp
            final.append(predline[bpp:row_size])

        return final

    @staticmethod
    def _paeth_predictor(left, above, upper_left):
        """Reverses the paeth prediction."""
        # Source: https://www.w3.org/TR/PNG-Filters.html
        initial_estimate = left + above - upper_left

        distance_left = abs(initial_estimate - left)
        distance_above = abs(initial_estimate - above)
        distance_upper_left = abs(initial_estimate - upper_left)
        
        if distance_left <= distance_above and distance_left <= distance_upper_left:
            return left
        elif distance_above <= distance_upper_left:
            return above
        else:
            return upper_left

    @staticmethod
    def lzw(data, early_change=1):
        """
        (Source: PDF reference 1.7 Chapter 3, section 3, subsection 3 [3.3.3], Table 3.7)
        EarlyChange: 

        An indication of when to increase the code length.
        If the value of this entry is 0, code length increases are postponed as long as possible.
        If the value is 1, code length increases occur one code early.
        This parameter is included because LZW sample code distributed by some vendors increases the code
        length one code earlier than necessary.
        Default value: 1.
        """
        # Starts as 9 but ranges from 9-12.
        bit_size = 9
        
        s = ''
        index = 258
        table = {}
        
        output = io.BytesIO()

        b_data = np.frombuffer(data, dtype=np.uint8)
        fin = []

        for b in range(b_data.shape[0]):
            s += format(b_data[b], '0>8b')

            if len(s) < bit_size * 2:
                continue

            curr = int(s[:bit_size], 2)
            nxt = int(s[bit_size:bit_size*2], 2)
            if nxt == 441:
                print(s, )
            s = s[bit_size:]
            fin.append(curr)

            if nxt >= 4097:
                raise Exception("Corrupt LZW Compression.")
        
            if nxt + early_change == (1 << bit_size):

                bit_size += 1
            elif nxt == 257 or nxt == 256:

                if curr >= 258:
                    output.write(bytes(table[curr]))
                else:
                    output.write(bytes([curr]))
            
            elif curr == 257:
                #print(curr, nxt)

                #should be EOF?
                continue
            elif curr == 256:
                #print(curr, nxt)

                index = 258
                bit_size = 9

            elif curr >= 258:

                output.write(bytes(table[curr]))
                table[index] = table[curr].copy()
                if nxt >= 258:
                    a = table[nxt][0] if nxt in table else table[curr][0]
                    table[index].append(a)
                else:
                    table[index].append(nxt)
                index += 1
            else:
                # curr < 256
                output.write(bytes([curr]))
                if nxt >= 258:
                    table[index] = [curr]
                    table[index].extend(table[nxt])
                else:
                    table[index] = [curr, nxt]
                index += 1

        output.seek(0)
        b_out =  output.read()
        output.close()
        #print(b_out)
        return fin

    @staticmethod
    def fuck_off(data, early_change=1):
        output = io.BytesIO()

        i_bits = 0
        i_buf = 0
        code = 0
        prev_code = 0
        nxt_size = 0

        nxt_code = 258
        nxt_bits = 9
        s_index = 0
        s_size = 0
        first = True
        eof = False

        table = {}

        k = 0
        fin = []

        while k < len(data):
            while i_bits < nxt_bits:
                if k >= len(data):
                    eof = True
                    break

                c = data[k]
                k += 1

                i_buf = (i_buf << 8) | (c & 255)
                i_bits += 8

            code = (i_buf >> (i_bits - nxt_bits)) & ((1 << nxt_bits) - 1)
            fin.append(code)
            i_bits -= nxt_bits

            if code == 257 or eof:
                break
            if code == 256:
                nxt_code = 258
                nxt_bits = 9
                s_index = 0
                s_size = 0
                first = True
                continue
            if nxt_code >= 4097:
                raise Exception("Corrupt LZW Compression.")

            nxt_size = s_size + 1
            if code < 256:
                #sbuf[0] = code
                output.write(bytes([code]))
                nc = code
                s_size = 1
            elif code < nxt_code:
                s_size = table[code]['length']
                j = code
                sbuf = [0] * s_size 
                for i in range(s_size - 1, 0, -1):
                    sbuf[i] = table[j]['tail']
                    j = table[j]['head']
                sbuf[0] = j
                nc = j
                output.write(bytes(sbuf))
            elif code == nxt_code:
                #sbuf[s_size] = nc
                output.write(bytes([nc]))
                s_size += 1
            else:
                raise Exception("Corrupt LZW Compression.")

            #nc = sbuf[0]
            if first:
                first = False
            else:
                table[nxt_code] = {
                    'length': nxt_size,
                    'head': prev_code,
                    'tail': nc
                }
                nxt_code += 1
                if nxt_code + early_change == 512:
                    nxt_bits = 10
                elif nxt_code + early_change == 1024:
                    nxt_bits = 11
                elif nxt_code + early_change == 2048:
                    nxt_bits = 12
                prev_code = code
                s_index = 0

        output.seek(0)
        b_out =  output.read()
        output.close()
        #print(b_out)
        return fin
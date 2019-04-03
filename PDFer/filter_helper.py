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
        Sources (this code is taken from these sources, I tried but this was faster):
        * https://github.com/davidben/poppler/blob/master/poppler/Stream.cc
        * https://github.com/davidben/poppler
        
        (Source: PDF reference 1.7 Chapter 3, section 3, subsection 3 [3.3.3], Table 3.7)
        EarlyChange: 

        An indication of when to increase the code length.
        If the value of this entry is 0, code length increases are postponed as long as possible.
        If the value is 1, code length increases occur one code early.
        This parameter is included because LZW sample code distributed by some vendors increases the code
        length one code earlier than necessary.
        Default value: 1.
        """
        output = io.BytesIO()

        # Keeps track of how many bits the buffer('buff') needs to generate the next code.
        input_bits = 0
        # One big number that represents the entire bit stream and is used to get the next code.
        buff = 0

        code = 0
        prev_code = 0
        # Length of the next table entry being inserted.
        entry_size = 0
        """The table is a dictionary that maps character codes above 258 to values under 256.

        The table only keeps track of three numbers, the 'tail', 'head', and 'length'.
        'tail' - must be a valid ascii value under 256.
        'head' - can be either a valid ascii value under 256 or it can be another char code in the table.
        'length' - the actual length of the LZW table entry.
        Note: if lenght == 2: head <= 255 else: head >= 258.
        (I initially tried creating table as a map of character codes to entry list's, but that became problematic.) 
        """
        table = {}
        # This is the table's index.
        index = 258

        # Number of bits that equal a valid code (ranges from 9 to 12 bits).
        bit_size = 9
        # Size of the current code entry that will be written to the output.
        seq_size = 0
        # used to ignore Clear Table Marker.
        is_clear_marker = True
        eof = False
        new_code = 0

        k = 0

        while k < len(data):
            # Parse through the compressed bytes
            while input_bits < bit_size:
                # This loop essentially streams the bytes to bits. 
                if k >= len(data):
                    eof = True
                    break
                # grab the next compressed byte
                c = data[k]
                k += 1
                # Adds the byte 'c' to the input buffer.  
                buff = (buff << 8) | (c & 255)
                # each byte is 8 bits
                input_bits += 8

            # This gets the last bits of size 'bit_size' and converts it to integer.
            # This is the actual code that LZW uses in compression and decompression.
            code = (buff >> (input_bits - bit_size)) & ((1 << bit_size) - 1)

            # push the 'in_bits' back
            input_bits -= bit_size

            # End of Data Decompression
            if code == 257 or eof:
                break
            # Clear Table Marker
            if code == 256:
                # This resets the table creation process, It Does Not mean deleting the whole table.
                # It is more like a restart, 'Clear Table' is a little misleading.
                index = 258
                bit_size = 9
                seq_size = 0
                # We don't want to add clear table markers to the table.
                is_clear_marker = True
                continue
            # If this is True then the 'table' has overflowed.
            if index >= 4097:
                raise Exception("Corrupt LZW Compression.")

            entry_size = seq_size + 1
            # Code is in [0,..,255] then it is valid acsii value.
            if code < 256:
                # This is the first appearence of this code so it is directly written out. 
                output.write(bytes([code]))
                new_code = code
                seq_size = 1

            # This means that the 'code' is a valid entry in the table.
            elif code < index:
                # 's_size' keeps track of how long the "true" table entry is.
                # This is needed because of the table's structure.(see the comment above 'table' to understand the structure)
                seq_size = table[code]['length']
                j = code
                # 'sbuf' is the "true" table entry and is a list of valid codes to be written out.
                sbuf = [0] * seq_size
                # fill the 'sbuf'
                for i in range(seq_size - 1, 0, -1):
                    sbuf[i] = table[j]['tail']
                    # j recurses throught the table
                    j = table[j]['head']

                # add the final head code
                sbuf[0] = j
                new_code = j
                output.write(bytes(sbuf))

            # This special/rare case means that the head of the last table entry is appended to the tail of this entry.
            elif code == index:
                output.write(bytes([new_code]))
                seq_size += 1
            else:
                raise Exception("Corrupt LZW Compression.")

            if is_clear_marker:
                is_clear_marker = False
            else:
                table[index] = {
                    'length': entry_size,
                    'head': prev_code,
                    'tail': new_code
                }

                index += 1
                
                if index + early_change == 512:
                    bit_size = 10
                elif index + early_change == 1024:
                    bit_size = 11
                elif index + early_change == 2048:
                    bit_size = 12
            
            prev_code = code

        output.seek(0)
        b_out =  output.read()
        output.close()
        return b_out
    
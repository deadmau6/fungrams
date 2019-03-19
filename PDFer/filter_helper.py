
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

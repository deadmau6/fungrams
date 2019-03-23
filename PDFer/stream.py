from .filter_helper import FilterHelper
import zlib, lzma

class Stream:

    def __init__(self, info, data):
        self.data = data
        #Watch out for FFilters and FDecodeParms
        self.filter = info.get('Filter')
        self.filter_params = info.get('DecodeParms', {})
        self._info = info

    def get_info(self, key=None):
        if key:
            return self._info.get(key)
        return self._info

    def decompress(self):
        if isinstance(self.filter, list):
            # There can be a compression pipeline
            return None

        if self.filter == 'FlateDecode':
            # zlib.MAX_WBITS|32 should check header to see if it is gzip or zlib
            return zlib.decompress(self.data, zlib.MAX_WBITS|32)
        elif self.filter == 'LZWDecode':
            FilterHelper.lzw(self.data)
            return self.data
        else:
            return self.data

    def decode(self, decoding='utf-8'):
        #Watch out for FFilters and FDecodeParms
        return self.decompress().decode(decoding)

    def get_data(self, decompress=False, decode=False, decoding='utf-8'):
        if decode:
            return self.decode(decoding)
        if decompress:
            return self.decompress()
        return self.data

    def unpredict(self):
        """helpful docs = https://www.w3.org/TR/PNG-Filters.html
        Prediction Values & meanings:
        (1)  -> No prediction (defualt)
        (2)  -> TIFF predictor
        (10) -> PNG(0) No prediction on all rows 
        (11) -> PNG(1) Sub on all rows = predicts the same as the sample to the left
        (12) -> PNG(2) Up on all rows = predicts the same as the sample above
        (13) -> PNG(3) Average on all rows = predicts the avg of sample to the left and above
        (14) -> PNG(4) Paeth on all rows = nonlinear function of the sample above, left, and upper left.
        (15) -> PNG optimum (any of the above for each row)
        """
        # selects the predictor algorithm
        prediction = self.filter_params.get('Predictor')

        if prediction is None or prediction == 1:
            return self.decompress()

        # number of components per sample (valid numbers are 1 - 4)
        colors = self.filter_params.get('Colors', 1)
        # number of samples per row
        columns = self.filter_params.get('Columns', 1)
        # number of bits to represent each color component per sample
        bpc = self.filter_params.get('BitsPerComponent', 8)

        # bytes per pixel!
        bpp = (colors * bpc + 7) >> 3
        # total bytes in the prediction row/line
        row_size = ((columns * colors * bpc + 7) >> 3) + bpp
        # data needs to be decompressed
        data = self.decompress()
        if prediction == 2:
            return FilterHelper.tiff_prediction(bpc, columns, colors, row_size, bpp, data)

        return FilterHelper.png_prediction(columns, row_size, bpp, data)

    def is_prediction_filter(self):
        prediction = self.filter_params.get('Predictor')
        return prediction is not None and prediction > 1
        
import zlib

class Stream:

    def __init__(self, info, data):
        self.data = data
        self.filter = info.get('Filter')
        self.f_params = info.get('DecodeParms')

    def decompress(self):
        if isinstance(self.filter, list):
            # There can be a compression pipeline
            return None

        decomp = self.filter.lower()

        if decomp == 'flatedecode':
            if self.f_params:
                return {
                    'compression': 'filtered',
                    'args': self.f_params,
                    'data': zlib.decompress(self.data)
                }
            return zlib.decompress(self.data)

        if decomp == 'dctdecode':
            # For JPEGs only, DCT = Discrete Cosine Transform 
            return {
                'compression': 'dct',
                'args': self.f_params,
                'data': self.data
            }

    def decode(self):
        #Watch out for FFilters and FDecodeParms
        for item in stream_info:
            if 'Filter' in item:
                decomp_typ = item['Filter']
                params = item.get('DecodeParms')
                break
        
        if self.filter is None:
            return stream_data

        if isinstance(self.filter, list):
            return None

        if self.filter.lower() == 'flatedecode' and self.f_params is None:
            return self.decompress().decode('utf-8')
        
        return self.decompress()
    
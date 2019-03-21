from scipy import ndimage
import numpy as np
import io

class ImageStream:

    def __init__(self, pdfdoc, image_stream):
        self._document = pdfdoc
        self.stream = image_stream
        self.color_space = image_stream.get_info('ColorSpace')
        if isinstance(self.color_space, tuple):
            # ICC might be a stream so tuple is returned
            self.color_space = self._document.get_object(self.color_space)

    def _special_color_space(self, cspace, cspace_args=None):
        # Separation, DeviceN, Indexed, Pattern
        # *NOTE* TINTS ARE SUBTRACTIVE SO 0.0 denotes lightest of a color & 1.0 is the darkest! 
        if cspace == 'indexed':
            # Allows color components to be represented in a single component
            # 
            # [/Indexed, base, hival, lookup]
            # base = a color space used to define the color table
            # hival = max iinteger range of the color table (0 < hival <= 255)
            # lookup = the color table, can be a stream or byte string
            # lookup_size = base_color_depth * (hival + 1)
            return 1
        if cspace == 'separation':
            # (see subtractive notes above)
            # Used to control processes on a single colorant like cyan and
            # this is really only used for printers/printing devices.
            # 
            # [/Separation, name, alternateSpace, tintTransform]
            # name = name object specifying the colorant (can be All or None)
            # alternateSpace = alternative color space (can be array or name object)(any non special color space)
            # tintTransform = a function used to transform tint to color
            name, alternate, tint = (None, None, None)
            for x in cspace_args:
                if isinstance(x, tuple):
                    tint = x
                elif isinstance(x, list):
                    alternate = x
                    break
                else:
                    if x.lower() in ['devicecmyk', 'devicergb', 'devicegray', 'calrgb' , 'calgray', 'lab', 'iccbased']:
                        alternate = x.lower()
                        break
                    name = x
            if isinstance(alternate, list):
                return self._color_depth(alternate)

            if alternate.startswith('device'):
                return self._device_color_space(alternate)
            
            return self._cie_color_depth(alternate)
        if cspace == 'pattern':
            # Please God No!, this one is a real shit show.
            # 
            # Types:
            # Tiling Patterns (subtypes: Color or Non-Color)
            # Shading Patterns (7 different subtypes)
            return cspace_args
        # (see subtractive notes above)
        # Whole buncha crap if there is an SubType == NChannel in attributes, totally different rules(i think)
        # AKA: len(name) = color_depth
        # name -maps-to-> alternate w\(tintTransform) THEN alternate -maps-to-> out w\(attributes(sometimes))
        # 
        # [/DeviceN, name, alternateSpace, tintTransform, attributes(optional)]
        # name = array of name objects specifying color components (can be 'None')
        # alternateSpace = alternative color space (can be array or name object)(any non special color space)
        # tintTransform = a function used to transform tint to color
        # attributes = dictionary containing extra info for custom image blending
        name, alternate, tint, attributes = (None, None, None, None)
        for x in cspace_args:
            if isinstance(x, tuple):
                tint = x
            elif isinstance(x, dict):
                attributes = x
            elif isinstance(x, list):
                is_alter = False
                for nm in x:
                    if nm.lower() in ['devicecmyk', 'devicergb', 'devicegray', 'calrgb' , 'calgray', 'lab', 'iccbased']:
                        is_alter = True
                        break
                if is_alter:
                    alternate = x
                else:
                    name = x
            else:
                alternate = x.lower()
        # I think this is the over all depth?
        return len(name)

    def _device_color_space(self, cspace, cspace_args=None):
        if cspace.endswith('gray'):
            return 1

        if cspace.endswith('rgb'):
            return 3

        if cspace.endswith('cmyk'):
            # needs its own "SPECIAL CONVERSION" maybe
            # Red = 255 * (1 - C) * (1 - K)
            # Green = 255 * (1 - M) * (1 - K)
            # Blue = 255 * (1 - Y) * (1 - K)
            return 4
        # Must be DeviceN which is actually a special color space
        return self._special_color_space(cspace, cspace_args)

    def _cie_color_space(self, cspace, cspace_args=None):
        # CalRGB,CalGray, Lab, ICCBased
        if cspace.endswith('gray'):
            return 1

        if cspace.endswith('rgb'):
            return 3

        if cspace.endswith('lab'):
            return 3

        if cspace.endswith('cmyk'):
            return 4
        
        # [/ICCBased, stream]
        # cspace_args should be indirect object
        icc_stream = self._document.get_object(cspace_args[0], search_stream=True)
        return icc_stream.get_info('N')

    def get_color_depth(self):
        # Color space can be array or name or stream
        if self.color_space is None:
            # TODO: handle JPXDecode which is the only case color space is None
            return 1

        name = None
        cs_args = None

        if isinstance(self.color_space, str):
            name = self.color_space.lower()

        elif isinstance(self.color_space, list):
            name = self.color_space[0].lower()
            if len(self.color_space) > 1:
                cs_args = self.color_space[1:]

        if name.startswith('device'):
            return self._device_color_space(name, cs_args)
        
        if name.startswith('cal') or name in ['lab', 'iccbased']:
            return self._cie_color_space(name, cs_args)

        return self._special_color_space(name, cs_args)

    def get_shape(self):
        height = self.stream.get_info('Height')
        width = self.stream.get_info('Width')
        return height, width, self.get_color_depth()

    def get_image(self):
        # This might only work because the bit depth is 8.
        # Pdf images can have differing bit depths to save space but
        # OpenCV only accepts uinsigned 8 bit integers (AKA 'uint8')
        # Coincidentally if the PDF's bit depth is 8 then it works like a charm
        # *HAVE NOT FOUND OR TESTED ON DIFFERENT BIT DEPTHS*
        shape = self.get_shape()
        img_filter = self.stream.filter.lower()

        if img_filter.startswith('dct'):
            #JPEG
            jpg_file = io.BytesIO(jpg_stream['data'])
            return ndimage.imread(jpg_file)
        elif img_filter.startswith('flate') and self.stream.is_prediction_filter():
            # Prediction PNG/TIFF
            return np.array(self.stream.unpredict(), dtype=np.uint8).reshape(shape)

        return np.frombuffer(self.stream.decompress(), dtype=np.uint8).reshape(shape)


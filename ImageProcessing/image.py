from pprint import pprint
from .operations import ImageOperations
from matplotlib import pyplot as plt
import numpy as np
import cv2 as cv
import os.path as ospath

class Image:

    def __init__(self, data, **kwargs):
        """Args:

        (required)
        data: should be either a numpy array or bytes(must provide valid shape).

        (optional, kwargs)
        shape: a tuple describing the dimmensions of the data, an example of an image's shape would be: (height, width, color_depth).
        operations: a list of operations to preform on the image.
        keep_original: keep a copy of the original data.
        """
        self.operator = ImageOperations()
        self.accepted_formats = ['jpeg', 'jpg', 'jpe', 'jp2', 'png', 'ppm', 'pgm', 'ppm', 'tiff', 'tif', 'bmp', 'sr', 'ras']
        self.histogram = None
        self.color = None
        self.info = {}

        self.data = data if isinstance(data, np.ndarray) else np.frombuffer(data, dtype=np.uint8)
        
        if kwargs.get('shape'):
            self._reshape_data(kwargs.pop(shape))
        else:
            self.shape = self.data.shape

        if kwargs.get('keep_original'):
            self.original = np.copy(self.data)

        self.operations = kwargs.get('operations')

    def _reshape_data(self, shape, contiguous=True):
        if contiguous:
            # This will raise an error if the data is copied (aka the shape is changed in place)
            self.data.shape = shape
        else:
            self.data = self.data.reshape(shape)

        self.shape = self.data.shape

    def _perform_operation(self, opr, args, image=None):
        """This preforms a single image operation for the given image(default is self.data).

        I tried to order these 'if' statements to reflect the expected usage. For example, a
        lot of the operations below require the color to be converted before performing their
        operation, therefore I put 'convert_color' at the top since I expect it to be called
        fequently. Another good example is that 'find_skew' is above 'rotate' because intuitively
        you would want the skew angle before actually performing the rotation.
        """
        img = image if image else self.data

        if opr == 'convert_color':
            return self.operator.convert_color(img, args.get('color'))
        if opr == 'histogram':
            # check color
            return self.operator.histogram(img, **args)
        if opr == 'blur':
            return self.operator.blur(img, **args)
        if opr == 'bitwise':
            return self.operator.bitwise(img, **args)
        if opr == 'morph':
            return self.operator.morph(img, **args)
        if opr == 'binarization':
            return self.operator.binarization(img, args.get('method', 'otsu'), args.get('thresh_type', {}), args.get('thresh_args', {}))
        if opr == 'square':
            return self.operator.make_square(img, **args)
        if opr == 'find_skew':
            # check color binary
            return self.operator.find_skew_angle(img)
        if opr == 'rotate':
            return self.operator.affine_rotate(img, args.get('angle', 0))
        if opr == 'mask':
            # check color grayscale
            return self.operator.mask(img, args.get('x'), args.get('y'), args.get('w'), args.get('h'))
        if opr == 'contours':
            return self.operator.contours(img)
        if opr == 'canny':
            return self.operator.canny(img, **args)
        return None

    def do_operations(self, opr_list):
        """ I expect opr_list to be a list of tuple's (opr_obj) in which the first
        spot in the tuple specifies the data to be operated on and the 
        specifies a function or operation to be preformed. The list order also
        reflects the order of operations to be preformed.
        """
        for opr_obj in opr_list:
            typ, opr, args = opr_obj
            if typ == 'image':
                d = self._perform_operation(opr, args)
                if isinstance(d, tuple):
                    self.info[opr] = d[0]
                    self.data = d[1]
                else:
                    self.data = d
            elif typ == 'histogram':
                self.histogram = self._perform_operation(opr, args)
            elif typ == 'other':
                self.info[opr] = self._perform_operation(opr, args)
        return True

    def show(self, rsize=None, fsize=None):
        """Simply displays the current image data."""
        if rsize:
            image = cv.resize(self.data, resize)
            cv.imshow('image', image)
        elif fsize:
            image = cv.resize(self.data, None, fx=fsize, fy=fsize)
            cv.imshow('image', image)
        else:
            cv.imshow('image', self.data)
        cv.waitKey(0)
        cv.destroyAllWindows()

    def save(self, save_name='default', location=None, image_format=None):
        # Make sure the image format is supported.
        i_format = image_format if image_format in self.accepted_formats else 'jpg'
        fname = f"{save_name}.{i_format}"
        if location and ospath.exists(location):
            cv.imwrite(ospath.join(location, fname), self.data)
        else:
            cv.imwrite(ospath.abspath(fname), self.data)

    def plot(self):
        if self.histogram is None:
            plt.hist(self.data.ravel(), 256, [0,256])
        elif isinstance(self.histogram, dict):
            plt.subplot(211)
            plt.imshow(self.data)
            plt.subplot(212)
            for k,v in self.histogram.items():
                plt.plot(v, color=k)
            plt.xlim([0,256])
        else:
            plt.subplot(211)
            plt.imshow(self.data, 'gray')
            plt.subplot(212)
            plt.plot(self.histogram)
            plt.xlim([0,256])
        plt.show()
    
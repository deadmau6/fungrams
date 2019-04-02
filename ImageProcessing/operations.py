import numpy as np
import cv2 as cv
from pprint import pprint

class ImageOperations:

    def make_square(self, image, border_color=[255,255,255]):
        """Pad the image so that given any rotation, the entire image is visible.
        """
        rows, cols, channel = image.shape
        diameter = np.sqrt((rows ** 2) + (cols ** 2))
        top = bottom = int((diameter - rows)  / 2) + 1
        left = right = int((diameter - cols)  / 2) + 1
        return cv.copyMakeBorder(image, top, bottom, left, right, cv.BORDER_CONSTANT, value=border_color)

    def affine_rotate(self, image, angle):
        """Rotate an image around the center given an angle in degrees.
        If the image is not squared then the edges of the image could be cut off.  
        """
        rows, cols, ch = image.shape
        M = cv.getRotationMatrix2D((cols/2, rows/2),angle,1)
        return cv.warpAffine(image, M, (cols, rows))

    def mask(self, image, x, y, w, h):
        """This will create a mask that blacks out everything not in the window.
        This window is derived from the width, height and an (x, y) location.
        The (x, y) location signify the top left corner of the window.
        Currently the image must be in grayscale for the mask to work.
        """
        mask = np.zeros(image.shape[:2], np.uint8)
        mask[y:(y+h), x:(x+w)] = 255
        return mask, cv.bitwise_and(image, image, mask=mask)

    def contours(self, image):
        """Contours are still a relatively new feature to this module and are still under development.
        The only issue is that the input image must be binary.
        """
        im, cnts, h = cv.findContours(image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        color_img = self.convert_color(image, cv.COLOR_GRAY2RGB)
        x, y, w, h = cv.boundingRect(cnts[137])
        color_img = cv.rectangle(color_img, (x,y), (x+w,y+h), (0,0,255), 2)
        return cv.drawContours(color_img, cnts, -1, (0,255,0), 2)

    def canny(self, image, minval=100, maxval=200, aperature_size=3, L2gradient=True):
        """The four values that are used to compute the Canny edge detection are:
        * minval = the lower threshold  to ignore an edge.
        * maxval = the upper threshold which accepts an edge
        * aperature_size = the size of the Sobel Kernal
        * L2gradient = specifies which gradient function is used (if True the more accurate function is used)
        Also the input image should be in grayscale.
        """
        return cv.Canny(image, minval, maxval, aperature_size, L2gradient=L2gradient)

    def find_skew_angle(self, image):
        """This returns the correction angle for a skewed image.
        To straighten the image simply use this angle with affine_rotate.
        Note: the input image must be binary!
        """
        coords = np.column_stack(np.where(image > 0))
        Ar = cv.minAreaRect(coords)
        angle = -(90 + Ar[-1])
        return angle

    def histogram(self, image, method='opencv', **kwargs):
        """According to 'opencv-python-tutorials', OpenCV's histogram function is generally 40X faster
        than numpy's histogram function. However (according to the same source) for one dimensional histograms
        numpy's `bincount` function is the fastest and is 10X faster.
        You can specify which method you wish to use with the 'method' parameter:
        'opencv' (defualt)
        'bincount'
        'numpy'
        """
        #TODO: have a third method option that will auto select an optimal method
        if method == 'opencv':
            if kwargs.get('plot'):
                color_plot = kwargs.pop('plot')
                hst = {}
                for i,col in enumerate(color_plot): 
                    hst[col] = ImageOperations.cv_histogram(image, channel=i, **kwargs)
                return hst
            return ImageOperations.cv_histogram(image, **kwargs)
        if method == 'bincount':
            return ImageOperations.numpy_bincount(image.ravel(), **kwargs)
        if method == 'numpy':
            return ImageOperations.numpy_histogram(image, **kwargs)
        # Default
        return ImageOperations.cv_histogram(image, **kwargs)

    @staticmethod
    def cv_histogram(image, channel=0, mask=None, size=256, r=[0,256]):
        # channels determines the color depth
        return cv.calcHist([image], [channel], mask, [size], r)

    @staticmethod
    def numpy_bincount(image, weights=None, minlength=256):
        # WARNING: Image must be One Dimensional (flattened)
        return np.bincount(image, weights, minlength)

    @staticmethod
    def numpy_histogram(image, bins=10, r=None, normed=None, weights=None, density=None):
        # WARNING: Image must be One Dimensional (flattened)
        return np.histogram(image, bins, r, normed, weights, density)

    def blur(self, image, method='gaussian', **kwargs):
        """This is a general image blurring function that abstracts the actual OpenCV methods.
        You can specify which method you wish to use with the 'method' parameter:
        'gaussian' (defualt)
        'average' 
        'median'
        'bilateral'
        """
        if method == 'gaussian':
            return ImageOperations.gaussian_blur(image, **kwargs)
        if method == 'average':
            return ImageOperations.average_blur(image, **kwargs)
        if method == 'median':
            return ImageOperations.median_blur(image, **kwargs)
        if method == 'bilateral':
            return ImageOperations.bilateral_blur(image, **kwargs)
        # Defualt
        return ImageOperations.gaussian_blur(image, **kwargs)

    @staticmethod
    def average_blur(image, ksize=(5,5), normal=True):
        """Given a kernal size (ie ksize=(3,3)) an averaging value* and kernal are created. 
        This kernal passes through the image, summing up all the pixels in the kernal and then divides
        by the averaging value. That result value is then set for each image in the kernal.
        If normalize is 'True': 'avg_value = 1 / kernal_width * kernal_height' otherwise 'avg_value = 1'.
        """
        return cv.boxFilter(image, -1, ksize, normalize=normal)

    @staticmethod
    def gaussian_blur(image, ksize=(5,5), sigma=None):
        """Perform a Gaussian blur on the image. 
        The first argument should be the kernal size which is a tuple of (Width, Height).
        Both the width and height of the kernal must be postive and odd!
        Then you can provide the standard deviation or sigma which if provided is a tuple of (X, Y). 
        If sigma is not provided or sigma = (0,0) then sigma is calculated from the kernal size. 
        """
        x = 0
        y = 0
        if (ksize[0] * ksize[1]) % 2 == 0:
            raise Exception("Error: kernal/box size must be odd and greater than 2.")
        if sigma:
            x, y = sigma
        return cv.GaussianBlur(image, ksize, x, y)

    @staticmethod
    def median_blur(image, ksize=5):
        """Computes the median of all the pixels in the given kernal size.
        The kernal size must be a single number, positive, and odd.

        Notes:
        In the other blur methods the computed 'blur_value' may not exist in the original image, but in 
        median blur the 'blur_value' is gaurenteed to be a pre-existing pixel value. This can reduce noise
        effectively.
        """
        if ksize % 2 == 0:
            raise Exception("Error: kernal/box size must be odd and greater than 2.")
        return cv.medianBlur(image, ksize)

    @staticmethod
    def bilateral_blur(image, d=7, sigma_color=75, sigma_space=75):
        """This form of blurring uses two Gaussian filters, one does a normal blur over the space domain 
        and the other filter covers the alpha or pixel intensities. This creates pixels that are 'spatial 
        neighbors' and 'instensity neighbors', then both pixels are considered before applying the blur. 
        As a result the edges are preserved making bilateral filtering even MORE Effective in NOISE REMOVAL.
        However because twice the filters are used, bilateral filtering is SLOWER. The Args required are:
        'FILTER_DIAMETER'(d) - if negative it is computed from 'SIGMA_SPACE' (recommendation: 5 < d < 9).
        'SIGMA_COLOR' - filter in the color space, a larger value means that farther colors within the 
        'space' neighborhood will be mixed together, resulting in larger areas of semi-equal color.
        'SIGMA_SPACE' – filter in the coordinate space, a larger value means that farther pixels will influence 
        each other as long as their colors are close enough. When d > 0 , it specifies the neighborhood size 
        regardless of sigmaSpace . Otherwise, d is proportional to sigmaSpace. (Recommended for COLOR & SPACE 
        values is  10 < x < 150)
        """
        return cv.bilateralFilter(image, d, sigma_color, sigma_space)

    def morph(self, image, method='dilate', kshape='rectangle', ksize=(5,5), i=1):
        """Perform various Morphological transformations given the 'method', kernal shape 'kshape', kernal size 
        'ksize', iterations 'i' (recomend: 1).
        Valid 'methods': 'open', 'close', 'gradient', 'tophat', 'blackhat', 'erode', or 'dilate'(defualt).
        Valid 'KSHAPES': 'cross', 'ellipse', or 'rectangle'(defualt).
        """
        kernal = ImageOperations.get_kernal_shape(ksize, kshape)
        if method == 'dilate':
            return cv.dilate(image, kernal, iterations=i)
        if method == 'open':
            return cv.morphologyEx(image, cv.MORPH_OPEN, kernal, iterations=i)
        if method == 'close':
            return cv.morphologyEx(image, cv.MORPH_CLOSE, kernal, iterations=i)
        if method == 'gradient':
            return cv.morphologyEx(image, cv.MORPH_GRADIENT, kernal, iterations=i)
        if method == 'tophat':
            return cv.morphologyEx(image, cv.MORPH_TOPHAT, kernal, iterations=i)
        if method == 'blackhat':
            return cv.morphologyEx(image, cv.MORPH_BLACKHAT, kernal, iterations=i)
        if method == 'erode':
            return cv.erode(image, kernal, iterations=i)
        return cv.dilate(image, kernal, iterations=i)

    @staticmethod
    def get_kernal_shape(ksize, shape):
        if shape == 'rectangle':
            return cv.getStructuringElement(cv.MORPH_RECT, ksize)
        if shape == 'cross':
            return cv.getStructuringElement(cv.MORPH_CROSS, ksize)
        if shape == 'ellipse':
            return cv.getStructuringElement(cv.MORPH_ELLIPSE, ksize)
        # Defualt
        return cv.getStructuringElement(cv.MORPH_RECT, ksize)

    def bitwise(self, image, method='NOT', other_image=None):
        """Perform bitwise operations on the image(s)(Both images need to be grayscale!).
        You can directly provide another image or specify that the other image be all 'white' or all 'black'(defualt).
        The 'method' determines which bitwise operation to do:
        'NOT' -> !image (defualt)
        'AND' -> image & img_2
        'OR' -> image | img_2
        'XOR' -> image ^ img_2
        """
        if method == 'NOT':
            return cv.bitwise_not(image)

        if other_image is None:
            img_2 = np.zeros(image.shape, np.uint8)
        elif isinstance(other_image, str):
            img_2 = np.zeros(image.shape, np.uint8) if other_image == 'black' else np.full(image.shape, 255, np.uint8)
        else:
            img_2 = other_image

        if method == 'AND':
            return cv.bitwise_and(image, img_2)
        if method == 'OR':
            return cv.bitwise_or(image, img_2)
        if method == 'XOR':
            return cv.bitwise_xor(image, img_2)
        # Defualt
        return cv.bitwise_not(image)

    def convert_color(self, image, color):
        """Convert the color of the image.
        The color parameter can be either an Integer representing a valid OpenCV color conversion code.
        (Example: convert_color(image, cv.COLOR_RGB2GRAY) then color = cv.COLOR_RGB2GRAY = 7)
        Or color can be a dict with the keys 'to' and 'from' (the values can be like 'rgb' or 'lab' or etc).
        (Example: convert_color(image {'from': 'rgb', 'to': 'gray'}) then color = cv.COLOR_RGB2GRAY)
        """
        if isinstance(color, int):
            return cv.cvtColor(image, color)

        if isinstance(color, str):
            color_code = getattr(cv, color.upper())
            return cv.cvtColor(image, color_code)

        conversion = f"COLOR_{color['from'].upper()}2{color['to'].upper()}"
        # If conversion string doesn't exist then AttributeError will be raised.
        color_code = getattr(cv, conversion)
        return cv.cvtColor(image, color_code)

    def binarization(self, image, method='otsu', thresh_type={}, args={}):
        thresh_code = ImageOperations.get_threshold(**thresh_type) 
        if method == 'otsu':
            return ImageOperations.otsu_binarization(image, thresh_code, **args)
        if method == 'simple':
            return ImageOperations.simple_threshold(image, thresh_code, **args)
        if method == 'adaptive':
            return ImageOperations.adaptive_threshold(image, thresh_code, **args)

    @staticmethod
    def get_threshold(method='binary', inverted=False):
        if method == 'binary':
            if inverted:
                return cv.THRESH_BINARY_INV
            return cv.THRESH_BINARY
        if method == 'trunc':
            return cv.THRESH_TRUNC
        if method == 'tozero':
            if inverted:
                return cv.THRESH_TOZERO_INV
            return cv.THRESH_TOZERO
        # Default
        return cv.THRESH_BINARY

    @staticmethod
    def simple_threshold(image, thresh_code, thresh=127, maxval=255, get_thresh_value=False):
        # image should be grayscale
        ret, thresh = cv.threshold(image, thresh, maxval, thresh_code)
        if get_thresh_value:
            return ret, thresh
        return thresh

    @staticmethod
    def otsu_binarization(image, thresh_code, thresh=127, maxval=255, get_thresh_value=False):
        """Automatically calculates a threshold value for a bimodal* image using it's histogram. 
        It tries to find the middle value between peaks in the histogram. 
        NOT ACCURATE FOR NON-BIMODAL* IMAGES!
        *Bimodal image is essentially an image whose histogram has two peaks*
        """
        ret, thresh = cv.threshold(image, thresh, maxval, thresh_code+cv.THRESH_OTSU)
        if get_thresh_value:
            return ret, thresh
        return thresh

    @staticmethod
    def adaptive_threshold(image, thresh_code, method='mean', ksize=11, const=2, maxval=255):
        if method == 'mean':
            return cv.adaptiveThreshold(image, maxval, cv.ADAPTIVE_THRESH_MEAN_C, thresh_code, ksize, const)
        return cv.adaptiveThreshold(image, maxval, cv.ADAPTIVE_THRESH_GAUSSIAN_C, thresh_code, ksize, const)
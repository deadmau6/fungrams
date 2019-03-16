import re
import numpy as np
import cv2 as cv
from os.path import abspath
from matplotlib import pyplot as plt
from argparse import ArgumentParser
from pprint import pprint

def _convert_bw(image):
    if len(image.shape) == 3:
        return cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    return image

def _convert_color(image):
    if len(image.shape) == 3:
        return image
    return cv.cvtColor(image, cv.COLOR_GRAY2BGR)

def _draw_rectangle(image, x, y, w, h):
    c_image = _convert_color(image)
    return cv.rectangle(c_image, (x, y), (x+w, y+h), (0,255,0), 3)

def _make_square(image, color=[255, 255, 255]):
    """Pad the image so that given any rotation, the entire image is visible.
    """
    rows, cols, channel = image.shape
    diameter = np.sqrt((rows ** 2) + (cols ** 2))
    top = bottom = int((diameter - rows)  / 2) + 1
    left = right = int((diameter - cols)  / 2) + 1
    return cv.copyMakeBorder(image, top, bottom, left, right, cv.BORDER_CONSTANT, value=color)

def bitwise_operations(image, args):
    """Perform bitwise operations('&', '|', '^', '!') with a white('w'), black('b'), or another image
    (preface file with '#' like '&_#file.png').
    """
    opr, bkgrnd = args.split('_') if len(args.split('_')) == 2 else args
    gray = _convert_bw(image)
    img_2 = None

    if bkgrnd.lower().startswith('w'):
        # white image
        img_2 = np.full(gray.shape, 255, np.uint8)
    elif bkgrnd.lower().startswith('#'):
        fname = bkgrnd[1:]
        img_2 = cv.imread(fname, cv.IMREAD_GRAYSCALE)
    else:
        # black image
        img_2 = np.zeros(gray.shape, np.uint8)
    
    if opr == '&':
        print("AND")
        return cv.bitwise_and(gray, img_2)
    elif opr == '|':
        print("OR")
        return cv.bitwise_or(gray, img_2)
    elif opr == '^':
        print("XOR")
        return cv.bitwise_xor(gray, img_2)
    else:
        print("NOT")
        return cv.bitwise_not(gray)
    

    inv = cv.bitwise_not(gray)
    return cv.bitwise_xor(gray, white_board)

def affine_rotate(image, angle, square=True):
    """Rotate an image around the center given an angle in degrees. 
    """
    square_image = image
    if square:
        square_image = _make_square(image)
    rows, cols, ch = square_image.shape
    M = cv.getRotationMatrix2D((cols/2, rows/2),angle,1)
    return cv.warpAffine(square_image, M, (cols, rows))

def adaptive_threshold(image, typ, ksize=11, const=2):
    
    image = _convert_bw(image)
    if typ == 1:
        return cv.adaptiveThreshold(image, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, ksize, const)
    return cv.adaptiveThreshold(image, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, ksize, const)

def otsu_binarization(image):
    """Automatically calculates a threshold value for a bimodal* image using it's histogram. 
    It tries to find the middle value between peaks in the histogram. 
    NOT ACCURATE FOR NON-BIMODAL* IMAGES!
    *Bimodal image is essentially an image whose histogram has two peaks*
    """
    gray_image = _convert_bw(image)
    ret, thresh = cv.threshold(gray_image, 127, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
    print(f"Threshold Value used: {ret}")
    return thresh

def average_blur_filter(image, args):
    """Given a box size (ie '3' or '3x3') an averaging value* and kernal are created. 
    This kernal passes through the image, summing up all the pixels in the box and then divides
    by the averaging value. That result value is then set for each image in the box.
    If normalize is 'True': 'avg_value = 1 / box_width * box_height' otherwise 'avg_value = 1'.
    """
    box = int(args[0], 10)
    normal = args[1].lower() == 'true'
    return cv.boxFilter(image, -1, (box, box), normalize=normal)

def gaussian_blur(image, dims, sigma):
    """Perform a Gaussian blur on the image (similiar to box blur). 
    The first argument should be the height and width of the kernal/box in the form 'Width,Height'.
    If just 'Width' is provided then the 'Hieght = Width'. In any case they should both be postive and odd.
    Next provide the standard deviation in X and Y directions in the form 'X,Y' and if just 'X' is provided
    then 'Y = X'. Also if both 'X' and 'Y' equal zero then they are calculated from the kernal size. 
    """
    ksize = [abs(int(x, 10)) for x in dims.split(',')]

    k_w, k_h = ksize if len(ksize) == 2 else (ksize[0], ksize[0])

    if (k_w * k_h) % 2 == 0:
        raise Exception("Error: kernal/box size must be odd and greater than 2.")

    std_div = [abs(int(x, 10)) for x in sigma.split(',')]

    x, y = std_div if len(std_div) == 2 else (std_div[0], std_div[0])

    return cv.GaussianBlur(image, (k_w, k_h), x, y)

def median_blur(image, dim):
    """Computes the median of all the pixels in the given box size. The 'box_size' must be a single number, 
    positive and odd! In the other blur methods the computed 'blur_value' may not exist in the original image, 
    but in median blur the 'blur_value' is gaurenteed to be a pre-existing pixel value. This can reduce 
    noise effectively.
    """
    ksize = abs(dim)
    if ksize % 2 == 0:
        raise Exception("Error: kernal/box size must be odd and greater than 2.")
    return cv.medianBlur(image, ksize)

def bilateral_blur(image, diam, sigma_color, sigma_space):
    """This form of blurring uses two Gaussian filters, one does a normal blur over the space domain 
    and the other filter covers the alpha or pixel intensities. This creates pixels that are 'spatial 
    neighbors' and 'instensity neighbors', then both pixels are considered before applying the blur. 
    As a result the edges are preserved making bilateral filtering even MORE Effective in NOISE REMOVAL.
    However because twice the filters are used bilateral filtering is SLOWER. The Args required are:
    'FILTER_DIAMETER'(d) - if negative it is computed from 'SIGMA_SPACE' (recommendation: 5 < d < 9).
    'SIGMA_COLOR' - filter in the color space, a larger value means that farther colors within the 
    'space' neighborhood will be mixed together, resulting in larger areas of semi-equal color.
    'SIGMA_SPACE' – filter in the coordinate space, a larger value means that farther pixels will influence 
    each other as long as their colors are close enough. When d > 0 , it specifies the neighborhood size 
    regardless of sigmaSpace . Otherwise, d is proportional to sigmaSpace. (Recommended for COLOR & SPACE 
    values is  10 < x < 150)
    """
    print(diam)
    return cv.bilateralFilter(image, diam, sigma_color, sigma_space)

def morph(image, typ, kshape, dims, i):
    """Perform various Morphological transformations give the 'TYPE', kernal shape 'KSHAPE', kernal size 
    'W,H', iterations 'ITER' (recomend: 1).
    Valid 'TYPES': 'open', 'close', 'gradient', 'tophat', 'blackhat', 'dilate', or 'erode'.
    Valid 'KSHAPES': 'cross', 'ellipse', or 'rectangle'.
    'rectangle' and 'erode' are the defaults.
    """
    i = int(i, 10)

    ksize = [abs(int(x, 10)) for x in dims.split(',')]

    k_w, k_h = ksize if len(ksize) == 2 else (ksize[0], ksize[0])

    kernal = None

    if kshape.lower().startswith('cr'):
        print("KSAHPE: CROSS")
        kernal = cv.getStructuringElement(cv.MORPH_CROSS, (k_w, k_h))
    elif kshape.lower().startswith('el'):
        print("KSAHPE: ELLIPSE")
        kernal = cv.getStructuringElement(cv.MORPH_ELLIPSE, (k_w, k_h))
    else:
        print("KSAHPE: RECTANGLE")
        kernal = cv.getStructuringElement(cv.MORPH_RECT, (k_w, k_h))

    if typ.lower().startswith('open'):
        print("TYPE: OPEN")
        return cv.morphologyEx(image, cv.MORPH_OPEN, kernal, iterations=i)

    if typ.lower().startswith('close'):
        print("TYPE: CLOSE")
        return cv.morphologyEx(image, cv.MORPH_CLOSE, kernal, iterations=i)

    if typ.lower().startswith('grad'):
        print("TYPE: GRADIENT")
        return cv.morphologyEx(image, cv.MORPH_GRADIENT, kernal, iterations=i)

    if typ.lower().startswith('top'):
        print("TYPE: TOPHAT")
        return cv.morphologyEx(image, cv.MORPH_TOPHAT, kernal, iterations=i)

    if typ.lower().startswith('black'):
        print("TYPE: BLACKHAT")
        return cv.morphologyEx(image, cv.MORPH_BLACKHAT, kernal, iterations=i)

    if typ.lower().startswith('dilate'):
        print("TYPE: DILATE")
        return cv.dilate(image, kernal, iterations=i)

    print("TYPE: ERODE")
    return cv.erode(image, kernal, iterations=i)

def mask(image, x, y, w, h):
    image = _convert_bw(image)

    mask = np.zeros(image.shape[:2], np.uint8)
    mask[y:(y+h), x:(x+w)] = 255
    return mask, cv.bitwise_and(image, image, mask=mask)

def histogram(image, args_mask):
    gray_image = _convert_bw(image) 
    
    g_hist = cv.calcHist([gray_image], [0], None, [256], [0,256])
    
    plt.plot(g_hist)

    if args_mask:
        m, m_image = mask(image, *args_mask)
        m_hist = cv.calcHist([m_image], [0], m, [256], [0,256])
        plt.plot(m_hist)

    plt.xlim([0,256])

    plt.show()

def contours(image):
    thresh = otsu_binarization(image)
    im, cnts, h = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    color_img = _convert_color(image)
    return cv.drawContours(color_img, cnts, -1, (0,255,0), 2)

def convolve(image):
    img = _convert_color(image)
    convolve = np.zeros(( int(img.shape[0] / 2), int(img.shape[1] / 2), img.shape[2] ), np.uint8)
    i = 0
    for x in img[::2]:
        j = 0
        for y in x[::2]:
            convolve[i,j] = y
            j += 1
        i += 1
    return convolve

def deskew(image):
    img = otsu_binarization(image)
    coords = np.column_stack(np.where(img > 0))
    pprint(coords)
    Ar = cv.minAreaRect(coords)
    pprint(Ar)
    angle = -(90 + Ar[-1])
    print(angle)
    return affine_rotate(image, angle, square=False)

def docu_display(document):
    clean = re.sub(r'\s+', ' ', document)
    sentences = clean.split('.')
    return '.\n'.join(sentences)

def docus(display):
    ds = {
        'bilateral_blur': bilateral_blur.__doc__,
        'otsu_binarization': otsu_binarization.__doc__,
        'average_blur_filter': average_blur_filter.__doc__,
        'gaussian_blur': gaussian_blur.__doc__,
        'median_blur': median_blur.__doc__,
        'morph': morph.__doc__
    }

    valid_method_names = ['bilateral', 'otsu', 'average', 'gauss', 'median', 'morph', 'all', 'blur']

    if display[0] == 'all':
        for k, v in ds.items():
            print(f"Method - {k}:\n")
            print(docu_display(v))
            print()
        return f"Valid METHOD Names: {valid_method_names}"

    for k, v in ds.items():
        for req in display:
            if req in k:
                print(f"Method - {k}:\n")
                print(docu_display(v))
                print()
                break
    return f"Valid METHOD Names: {valid_method_names}"

def run(args):

    if args.docs:
        print(docus(args.docs))
        return

    fname = 'react _lifecycle.png'
    
    if args.file:
        fname = args.file

    img = cv.imread(fname, cv.IMREAD_UNCHANGED)

    if args.histogram:
        histogram(img, args.mask)
        return

    print(f"ORIGINAL SHAPE: {img.shape}")
    res = None
    if args.otsu:
        res = otsu_binarization(img)
    elif args.box_blur:
        res = average_blur_filter(img, args.box_blur)
    elif args.gauss_blur:
        res = gaussian_blur(img, *args.gauss_blur)
    elif args.median_blur:
        res = median_blur(img, args.median_blur)
    elif args.bilateral_blur:
        res = bilateral_blur(img, *args.bilateral_blur)
    elif args.morph:
        res = morph(img, *args.morph)
    elif args.rotate:
        res = affine_rotate(img, args.rotate)
    elif args.bitwise:
        res = bitwise_operations(img, args.bitwise)
    elif args.mask:
        m, res = mask(img, *args.mask)
    elif args.adaptive_thresh:
        res = adaptive_threshold(img, *args.adaptive_thresh)
    elif args.contours:
        res = contours(img)
    elif args.deskew:
        res = deskew(img)
    elif args.rect:
        res = _draw_rectangle(img, *args.rect)
    else:
        res = convolve(img)

    res_view = cv.resize(res, None, fx=0.25, fy=0.25)
    cv.imshow('image', res_view)
    cv.waitKey(0)
    cv.destroyAllWindows()
    if args.save:
        # Same as os.path.join(os.getcwd(), *path). 
        fname = abspath(f"{args.save}.{args.format}")
        cv.imwrite(fname, res)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Image File location.',
        default=False
        )

    parser.add_argument(
        '-o',
        '--otsu',
        action='store_true',
        help="Run the otsu binarization which is an adaptive image threshold algorithm.",
        default=False
        )

    parser.add_argument(
        '-b',
        '--box-blur',
        nargs=2,
        help="Create a basic kernal and then blur an image with the kernal.",
        metavar=('BOX_SIZE', 'NORMALIZE'),
        default=False
        )

    parser.add_argument(
        '-g',
        '--gauss-blur',
        nargs=2,
        help="Perform a gaussian blur on the image.",
        metavar=("'W,H'", "'X,Y'"),
        default=False
        )

    parser.add_argument(
        '-m',
        '--median-blur',
        type=int,
        help="Blur using the median of the kernals.",
        metavar=("BOX_SIZE"),
        default=False
        )

    parser.add_argument(
        '-l',
        '--bilateral-blur',
        type=int,
        nargs=3,
        help="Blur an image using more advance gauss filters.",
        metavar=("FILTER_DIAMETER", "SIGMA_COLOR", "SIGMA_SPACE"),
        default=False
        )

    parser.add_argument(
        '-M',
        '--morph',
        nargs=4,
        help="Transform components in the image using kernal convolution.",
        metavar=("TYPE", "KSHAPE", "'W,H'", "ITER"),
        default=False
        )

    parser.add_argument(
        '-d',
        '--docs',
        nargs='+',
        help="Display extra documentation on some of the methods in this script.",
        metavar=('METHOD'),
        default=False
        )

    parser.add_argument(
        '-r',
        '--rotate',
        type=int,
        help=affine_rotate.__doc__,
        metavar=('ANGLE'),
        default=False
        )

    parser.add_argument(
        '-w',
        '--bitwise',
        type=str,
        help=bitwise_operations.__doc__,
        metavar=('OPR_IMG'),
        default=False
        )

    parser.add_argument(
        '-s',
        '--save',
        type=str,
        help="Save the image modifications with the provided name.",
        metavar=('NAME'),
        default=False
        )

    parser.add_argument(
        '-F',
        '--format',
        type=str,
        help="Image format, defualt is 'jpeg'.",
        choices=('jpeg', 'png', 'tiff'),
        default='jpeg'
        )

    parser.add_argument(
        '-H',
        '--histogram',
        action='store_true',
        help="Find histogram of image.",
        default=False
        )

    parser.add_argument(
        '-a',
        '--mask',
        type=int,
        nargs=4,
        help="Get mask of image.",
        metavar=('X', 'Y', 'W', 'H'),
        default=False
        )

    parser.add_argument(
        '-T',
        '--adaptive-thresh',
        type=int,
        nargs=3,
        help="Apply Adaptive threshold on the image.",
        metavar=('TYPE', 'KSIZE', 'CONST'),
        default=False
        )

    parser.add_argument(
        '-c',
        '--contours',
        action='store_true',
        help="Find contours of image.",
        default=False
        )

    parser.add_argument(
        '-D',
        '--deskew',
        action='store_true',
        help="Deskew the image.",
        default=False
        )

    parser.add_argument(
        '-R',
        '--rect',
        type=int,
        nargs=4,
        help="Draw a rectangle.",
        metavar=('X', 'Y', 'W', 'H'),
        default=False
        )

    args = parser.parse_args()
    run(args)

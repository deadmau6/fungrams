from .image import Image
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from pprint import pprint
import re

class ImageController:

    def __init__(self):
        self.opr_re = re.compile(r'(?P<opr>\w+)\((?P<args>[\[\]\(\){}\s\w,=:\"\']*)\)')
        self.int_re = re.compile(r'\d+')
        self.float_re = re.compile(r'\d+\.\d+')
        self.tuple_re = re.compile(r'\([\w,]+\)')
        self.list_re = re.compile(r'\[[\w,]+\]')
        self.obj_re = re.compile(r'{[\w:,]*}')

    def read_file(self, fname):
        return cv.imread(fname, cv.IMREAD_UNCHANGED)

    def _value_check(self, value):
        if re.match(self.float_re, value):
            return float(value)
        if re.match(self.int_re, value):
            return int(value, 10)
        if re.match(self.tuple_re, value):
            clean = value.strip(')(') # kinda looks like boobs
            val_list = [self._value_check(x) for x in clean.split(',')]
            return tuple(val_list)
        if re.match(self.list_re, value):
            clean = value.strip('[]')
            return [self._value_check(x) for x in clean.split(',')]
        if re.match(self.obj_re, value):
            obj = {}
            clean = value.strip('}{')
            for entry in clean.split(','):
                k, v = entry.split(':')
                obj[k] = self._value_check(v)
            return obj
        if value == 'true':
            return True
        if value == 'false':
            return False
        # Value must be string
        return value

    def _args_object(self, args_list):
        args_obj = {}
        for a in args_list:
            k, v = a.split('=')
            args_obj[k] = self._value_check(v)
        return args_obj

    def _operation_object(self, opr_string):
        # convert the opr_string to the opr_object
        # string format?: 'operation(arg1, arg2, arg3=val)'
        m = re.match(self.opr_re, opr_string)
        
        opr = m.group('opr').lower()
        
        args = {}
        if m.group('args'):
            arg_list = [re.sub(r'\s+', '', x) for x in m.group('args').split(', ')]
            args = self._args_object(arg_list)

        if opr == 'convert_color':
            return 'image', opr, args
        if opr == 'histogram':
            return 'histogram', opr, args
            # check color
        if opr == 'blur':
            return 'image', opr, args
        if opr == 'bitwise':
            return 'image', opr, args
            # check color
        if opr == 'morph':
            return 'image', opr, args
        if opr == 'binarization':
            return 'image', opr, args
            # check color
        if opr == 'square':
            return 'image', opr, args
            # check color
        if opr == 'find_skew':
            return 'other', opr, args
            # check color binary
        if opr == 'rotate':
            return 'image', opr, args
        if opr == 'mask':
            return 'image', opr, args
            # check color grayscale
        if opr == 'contours':
            return 'image', opr, args
        if opr == 'canny':
            return 'image', opr, args

    def start(self, args):
        """Run image processing operations from the command line."""
        if not args.file:
            print('Done')
            return
        image = Image(self.read_file(args.file))
        if args.operations:
            ops =[self._operation_object(opr_string) for opr_string in args.operations]
            image.do_operations(ops)
        
        if args.ocr_data:
            pprint(image.get_ocr_data())

        if args.histogram:
            image.plot()
        elif args.resize:
            val = self._value_check(args.resize)
            if isinstance(val, tuple):
                image.show(rsize=val)
            else:
                image.show(fsize=val)
        elif args.ocr:
            print(image.ocr())
        elif args.method:
            #image.harraj_and_raissouni()
            image.crop_morphology()
        else:
            image.show()
        
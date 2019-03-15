
class Font:

    def __init__(self, pdfdoc, font_object):
        if font_object.pop('Type') != 'Font':
            raise Exception('Incorrect format, object is not a page.')

        self._document = pdfdoc
        # Required
        self.subtype = font_object.pop('Subtype')
        self.base_font = font_object.pop('BaseFont')
        # Optional
        self.first_char = font_object.get('FirstChar')
        self.last_char = font_object.get('LastChar')
        self.widths = font_object.get('Widths')
        self.descriptor = font_object.get('FontDescriptor')
        self.encoding = font_object.get('Encoding')
        self.to_unicode = font_object.get('ToUnicode')

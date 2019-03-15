
class Page:

    def __init__(self, pdfdoc, page_object):
        if page_object.pop('Type') != 'Page':
            raise Exception('Incorrect format, object is not a page.')
        self._document = pdfdoc
        # Required
        self._resources = page_object.pop('Resources')
        # Optional
        if 'Contents' in page_object:
            self._contents = page_object.pop('Contents')
        # Leftovers
        self._page_info = {}
        for k, v in page_object:
            self.page_info[k.lower()] = v

    def resources(self):
        if isinstance(self._resources, tuple):
            return self._document.get_object(self._resources)
        return self._resources

    def content(self):
        if self._contents:
            return self._document.get_object(self._contents, search_stream=True)
        return self._contents

    def get_info(self, key):
        return self._page_info.get(key.lower())

        
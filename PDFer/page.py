
class Page:

    def __init__(self, pdfdoc, page_object):
        if page_object.pop('Type') != 'Page':
            raise Exception('Incorrect format, object is not a page.')
        self._document = pdfdoc
        # Required
        self._resources = page_object.pop('Resources')
        # Optional
        self._contents = page_object.pop('Contents') if 'Contents' in page_object else None
        # Leftovers
        self._page_info = {}
        for k, v in page_object.items():
            self._page_info[k.lower()] = v

    def resources(self):
        if isinstance(self._resources, tuple):
            return self._document.get_object(self._resources)
        return self._resources

    def content(self):
        # TODO: handle if contents is an array
        if self._contents:
            return self._document.get_object(self._contents, search_stream=True)
        return self._contents

    def get_info(self, key):
        return self._page_info.get(key.lower())

    def toJSON(self):
        return {
            'resources': self._resources,
            'content': self._contents,
            'info': self._page_info
        }

        
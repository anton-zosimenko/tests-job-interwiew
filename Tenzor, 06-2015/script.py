# -*- encoding: utf-8 -*-

import sys
import re
import urllib2
import lxml.html as html
from lxml.html.clean import Cleaner
from PIL import Image
from StringIO import StringIO
from httplib import IncompleteRead
import os


configuration = {
    # http://stackoverflow.com/questions/7160737/
    'url_pattern':
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
    'css_title_selectors': ['title', ],
    'css_text_selectors': ['p', 'b', ],
    'css_text_special_selectors': ['a', ],
    'css_image_selectors': ['img', ],
    'special_block_markup_template': '[{0}]',
    'max_text_width': 80,
    'text_block_separator': '\n',
    'min_words_in_block': 4,
    'image_size_pattern': r'(\d{1,4})[xх×]{1,1}(\d{1,4})',
    'image_aspect_ratio': 3.0,
    'image_download_count': 1,
    'image_block_markup_template': '[{0}]',
    'image_block_separator': '',
    'data_directory': 'downloaded',
    'article_filename': 'article.txt',
}


class RegexValidator(object):
    _pattern = ''

    def __init__(self, pattern=''):
        self.pattern = pattern
        self._regex = re.compile(self.pattern, re.IGNORECASE)

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, new_patern):
        if self.pattern != new_patern:
            self._pattern = new_patern
            self._regex = re.compile(self.pattern, re.IGNORECASE)


class UrlValidator(RegexValidator):

    def __init__(self, pattern=''):
        super(UrlValidator, self).__init__(
            pattern or configuration['url_pattern']
        )

    def is_valid(self, url=''):
        return bool(re.match(self._regex, url))


class GetDataFromUrl(object):
    _response = ''
    _error = ''
    _encoding = ''
    _url = ''

    def __init__(self, url=''):
        self.url = url

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, new_url):
        if self._url != new_url:
            self._url = new_url

    @property
    def response_datastream(self):
        self._encoding = ''
        self._error = ''
        request = urllib2.Request(self.url)
        try:
            _response = urllib2.urlopen(request)
            # http://stackoverflow.com/questions/1020892/
            if 'charset=' in _response.headers.get('content-type'):
                self._encoding = _response.headers.get(
                    'content-type'
                ).split('charset=')[-1]
        except urllib2.HTTPError as exception:
            self._error = 'The server couldnt fulfill the request. ' \
                          'Error code: {}'.format(exception.code)
        except urllib2.URLError as exception:
            self._error = 'We failed to reach a server. ' \
                          'Reason: {}'.format(exception.reason)
        else:
            return _response

    @property
    def response(self):
        # https://docs.python.org/2/howto/urllib2.html
        self._response = ''
        resp = self.response_datastream
        if resp:
            # http://stackoverflow.com/questions/14149100/
            try:
                data = resp.read()
            except IncompleteRead as exception:
                data = exception.partial
            resp.close()
            if self._encoding:
                self._response = unicode(data, self._encoding)
            else:
                self._response = data
        return self._response

    @property
    def error(self):
        return self._error


class GetTextFromResponse(object):
    _data = ''
    _text = ''
    _header = ''
    _body = ''

    def __init__(self, data=''):
        if data:
            self.parse(data)

    def parse(self, data):
        self._data = data
        self._text = ''
        self._header = ''
        self._body = ''
        titles = []
        for title_selector in configuration['css_title_selectors']:
            titles += self._data.cssselect(title_selector)
        for title in titles:
            if title.text_content():
                self._header += \
                    (
                        '\n' + configuration['text_block_separator']
                        if self._header else ''
                    ) + self.format_string(title.text_content())
        text_blocks = []
        for text_selector in configuration['css_text_selectors']:
            text_blocks += self._data.cssselect(text_selector)
        for text_block in text_blocks:
            txt = text_block.text_content()
            if len(txt.strip().split()) < configuration['min_words_in_block']:
                continue
            special_blocks = []
            for special_selector in configuration[
                'css_text_special_selectors'
            ]:
                special_blocks += text_block.cssselect(special_selector)
            for special_block in special_blocks:
                ofst = txt.find(special_block.text_content()) + \
                    len(special_block.text_content())
                txt = txt[:ofst] + \
                    configuration[
                        'special_block_markup_template'
                    ].format(special_block.get('href')) + \
                    txt[ofst:]
            if txt:
                self._body += \
                    (
                        '\n' + configuration['text_block_separator']
                        if self._body else ''
                    ) + self.format_string(txt)
        return self

    @staticmethod
    def format_string(raw_str):
        words = raw_str.strip().split()
        result = ''
        line = ''
        for word in words:
            if len(line) + len(word) < configuration['max_text_width']:
                line += (' ' if line else '') + word
            else:
                if line:
                    result += ('\n' if result else '') + line
                line = word
        if line:
            result += ('\n' if result else '') + line
        return result

    @property
    def text(self):
        return self._header + \
            (
                '\n' + configuration['text_block_separator']
                if self._header else ''
            ) + self._body

    @property
    def header(self):
        return self._header

    @property
    def body(self):
        return self._body


class GetImageUrlFromResponse(RegexValidator):
    _data = ''
    _parsed_images = []

    def __init__(self, data=''):
        super(GetImageUrlFromResponse, self).__init__(
            configuration['image_size_pattern']
        )
        if data:
            self.parse(data)

    def parse(self, data):
        self._data = data
        self._parsed_images = []
        _images = []
        for image_selector in configuration['css_image_selectors']:
            _images += self._data.cssselect(image_selector)
        url_validator = UrlValidator()
        data_getter = GetDataFromUrl()
        for image in _images:
            size = (1, 1)
            img_src = image.get('src')
            if image.get('width') and image.get('height'):
                try:
                    w = int(image.get('width'))
                    h = int(image.get('height'))
                    size = w, h
                except ValueError:
                    pass
            else:
                search = re.search(self._regex, img_src)
                if search:
                    size = int(search.group(1)), int(search.group(2))
                else:
                    # http://bytes.com/topic/python/answers/514762-possible-
                    # get-image-size-before-without-downloading
                    if url_validator.is_valid(img_src):
                        data_getter.url = img_src
                        ds = data_getter.response_datastream
                        if ds:
                            # http://stackoverflow.com/questions/14149100/
                            try:
                                buf = StringIO(ds.read(512))
                            except IncompleteRead as exception:
                                buf = StringIO(exception.partial)
                            ds.close()
                            try:
                                size = Image.open(buf).size
                            except IOError:
                                pass
            if min(size) != 0 and \
                    1. * max(size) / min(size) < \
                    configuration['image_aspect_ratio']:
                img_area = size[0] * size[1]
            else:
                img_area = 1
            self._parsed_images.append((img_src, img_area))
        return self

    @property
    def images(self):
        return [
            image[0] for image in sorted(
                self._parsed_images,
                key=lambda x: x[1],
                reverse=True
            )[:configuration['image_download_count']]
        ]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: python {} url_to_parse'.format(__file__))
    validator = UrlValidator()
    if not validator.is_valid(sys.argv[1]):
        sys.exit('url "{}" not valid'.format(sys.argv[1]))
    if not os.path.exists(configuration['data_directory']):
        os.makedirs(configuration['data_directory'])
    subdir = configuration['data_directory'] + '/' + \
        sys.argv[1].replace('/', '_').replace(':', '_').replace('.', '_')
    if not os.path.exists(subdir):
        os.makedirs(subdir)
    getter_data = GetDataFromUrl(sys.argv[1])
    response = getter_data.response
    if getter_data.error:
        sys.exit(
            'cannot get data from url "{}", received error "{}"'.format(
                sys.argv[1],
                getter_data.error
            )
        )
    cleaner = Cleaner(
        page_structure=False,
        links=False
    )
    cleaned_html = cleaner.clean_html(response)
    parsed_body = html.fromstring(cleaned_html)
    img_parser = GetImageUrlFromResponse(parsed_body)
    img_block = ''
    for image_url in img_parser.images:
        if not validator.is_valid(image_url):
            continue
        getter_data.url = image_url
        img_filename = image_url.split('/')[-1]
        img = open(subdir + '/' + img_filename, 'w')
        img.write(getter_data.response)
        img.close()
        img_block += \
            (
                '\n' + configuration['image_block_separator']
                if img_block else ''
            ) + configuration[
                'image_block_markup_template'
            ].format(img_filename)
    text_parser = GetTextFromResponse(parsed_body)
    article_data = \
        text_parser.header + \
        (
            '\n' + configuration['text_block_separator']
            if text_parser.header else ''
        ) + \
        img_block + \
        (
            '\n' + configuration['text_block_separator']
            if img_block else ''
        ) + \
        text_parser.body
    article = open(subdir + '/' + configuration['article_filename'], 'w')
    article.write(article_data.encode('utf8'))
    article.close()

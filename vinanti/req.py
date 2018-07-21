"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of vinanti.

vinanti is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

vinanti is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with vinanti.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import urllib.parse

try:
    from vinanti.log import log_function
    from vinanti.formdata import Formdata
except ImportError:
    from log import log_function
    from formdata import Formdata
    
logger = log_function(__name__)

class RequestObject:
    
    def __init__(self, url, hdrs, method, backend, kargs):
        self.url = url
        self.hdrs = hdrs
        self.kargs = kargs
        self.html = None
        self.status = None
        self.info = None
        self.method = method
        self.error = None
        self.data = None
        self.backend = backend
        self.log = kargs.get('log')
        self.wait = kargs.get('wait')
        self.proxies = kargs.get('proxies')
        self.auth = kargs.get('auth')
        self.auth_digest = kargs.get('auth_digest')
        self.files = kargs.get('files')
        self.binary = kargs.get('binary')
        self.charset = kargs.get('charset')
        self.session = kargs.get('session')
        self.verify = kargs.get('verify')
        if not self.log:
            logger.disabled = True
        self.timeout = self.kargs.get('timeout')
        self.out = self.kargs.get('out')
        self.out_dir = None
        self.continue_out = self.kargs.get('continue_out')
        self.__init_extra__()
    
    def __init_extra__(self):
        self.data_old = None
        if self.out:
            path_name = self.url.rsplit('/', 1)[-1]
            if self.out == 'default' and path_name:
                self.out = path_name
            elif os.path.isdir(self.out) and path_name:
                self.out_dir = self.out
                self.out = os.path.join(self.out, path_name)
            if os.path.isfile(self.out) and self.continue_out:
                sz = os.stat(self.out).st_size
                self.hdrs.update({'Range':'bytes={}-'.format(sz)})
        if not self.hdrs:
            self.hdrs = {"User-Agent":"Mozilla/5.0"}
        if not self.method:
            self.method = 'GET'
        if not self.timeout:
            self.timeout = None
        if self.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            self.data = self.kargs.get('data')
            if self.data:
                self.data_old = self.data
                if self.backend == 'urllib':
                    self.data = urllib.parse.urlencode(self.data)
                    self.data = self.data.encode('utf-8')
        elif self.method == 'GET':
            payload = self.kargs.get('params')
            if payload:
                payload = urllib.parse.urlencode(payload)
                self.url = self.url + '?' + payload
        if self.files and self.backend == 'urllib':
            if self.data:
                mfiles = Formdata(self.data_old, self.files)
            else:
                mfiles = Formdata({}, self.files)
            data, hdr = mfiles.create_content()
            for key, value in hdr.items():
                self.hdrs.update({key:value})
            self.data = data
                                   

class Response:
    
    def __init__(self, url, method=None, error=None,
                 session_cookies=None, charset=None,
                 info=None, status=None, content_type=None,
                 content_encoding=None, html=None,
                 out_file=None, out_dir=None, binary=None):
        self.method = method
        self.error = error
        self.session_cookies = session_cookies
        self.charset = charset
        self.html = html
        self.info = info
        self.status = status
        self.url = url
        self.content_type = content_type
        self.content_encoding = content_encoding
        self.out_file = out_file
        self.out_dir = out_dir
        self.binary = binary
        self.request_object = None
        self.dstorage = None

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
import sys

try:
    import aiohttp
except ImportError:
    pass
    
import asyncio
import mimetypes

try:
    from vinanti.req import *
    from vinanti.log import log_function
except ImportError:
    from req import *
    from log import log_function
    
logger = log_function(__name__)


class RequestObjectAiohttp(RequestObject):
    
    def __init__(self, url, hdrs, method, kargs):
        super().__init__(url, hdrs, method, 'aiohttp', kargs)
        self.readable_format = [
                'text/plain', 'text/html', 'text/css',
                'text/javascript', 'application/xhtml+xml',
                'application/xml', 'application/json',
                'application/javascript', 'application/ecmascript'
                ]
        
    async def process_aio_request(self, session):
        
        func = self.get_aio_request_func(session)
        ret_obj = None
        async with func as resp:
            rsp = Response(self.url, method=self.method,
                           out_file=self.out, out_dir=self.out_dir)
            rsp.info = resp.headers
            rsp.content_type = rsp.info.get('content-type')
            sz = rsp.info.get('content-length')
            rsp.status = resp.status
            if sz:
                sz = round(int(sz)/(1024*1024), 2)
            if rsp.status in [200, 206]:
                rsp.url = str(resp.url)
                path_name = rsp.url.rsplit('/', 1)[-1]
                human_readable = False
                for i in self.readable_format:
                    if i in rsp.content_type.lower():
                        human_readable = True
                        break
                text = None
                if self.method != 'HEAD':
                    if self.out:
                        print_count = 0
                        if self.continue_out:
                            mode = 'ab'
                        else:
                            mode = 'wb'
                        with open(self.out, mode) as fd:
                            while True:
                                chunk = await resp.content.read(1024)
                                if not chunk:
                                    break
                                fd.write(chunk)
                                print_count += 1
                                if (print_count) % 200 == 0:
                                    count = print_count * len(chunk)
                                    dwn = round(int(count)/(1024*1024), 2)
                                    sys.stdout.write('\r')
                                    sys.stdout.write('{} M / {} M : {}'.format(dwn, sz, self.out))
                                    sys.stdout.flush()
                            sys.stdout.write('\r')
                            sys.stdout.write('{} M / {} M : {}'.format(sz, sz, self.out))
                            sys.stdout.flush()
                            text = 'file saved to:: {}'.format(self.out)
                            if not human_readable:
                                rsp.binary = True
                    elif self.binary:
                        text = await resp.read()
                    elif self.charset and human_readable:
                        text = await resp.text(encoding=self.charset)
                    elif human_readable:
                        text = await resp.text(encoding='utf-8')
                    else:
                        text = 'Content {} not human readable.'.format(rsp.content_type)
                rsp.html = text
                rsp.status = resp.status
                cj_arr = []
                for c in session.cookie_jar:
                    cj_arr.append('{}={}'.format(c.key, c.value))
                rsp.session_cookies = ';'.join(cj_arr)
        return rsp
        
    def get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
    def add_formfields(self):
        self.data = aiohttp.FormData()
        if isinstance(self.data_old, dict):
            for key, value in self.data_old.items():
                self.data.add_field(key, value)
        elif isinstance(self.data_old, tuple):
            for td in self.data_old:
                if isinstance(td, tuple):
                    self.data.add_field(td[0], td[1])
        if isinstance(self.files, str):
            content_type = self.get_content_type(self.files)
            filename = os.path.basename(self.files)
            self.data.add_field(filename, open(self.files, 'rb'),
                                content_type=content_type)
        elif isinstance(self.files, tuple):
            for file_name in self.files:
                content_type = self.get_content_type(file_name)
                filename = os.path.basename(file_name)
                self.data.add_field(filename, open(file_name, 'rb'),
                                    content_type=content_type)
        elif isinstance(self.files, dict):
            for file_title, file_name in self.files.items():
                content_type = self.get_content_type(file_name)
                self.data.add_field(file_title, open(file_name, 'rb'),
                                    content_type=content_type)
                                    
    def get_aio_request_func(self, session):
        if self.files:
            self.add_formfields()
        if self.method == 'GET':
            func = session.get
        elif self.method == 'POST':
            func = session.post
        elif self.method == 'PUT':
            func = session.put
        elif self.method == 'PATCH':
            func = session.patch
        elif self.method == 'DELETE':
            func = session.delete
        elif self.method == 'HEAD':
            func = session.head
        elif self.method == 'OPTIONS':
            func = session.options
        if self.timeout is None:
            self.timeout = 300
        if self.verify is False:
            verify = False
        else:
            verify = True
        http_proxy = None
        if self.proxies:
            http_proxy = self.proxies.get('http')
            if not http_proxy:
                http_proxy = self.proxies.get('https')
        new_func = func(self.url, headers=self.hdrs, timeout=self.timeout,
                        ssl=verify, proxy=http_proxy, data=self.data)
    
        return new_func
        

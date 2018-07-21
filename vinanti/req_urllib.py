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

import re
import ssl
import gzip
import time
import shutil
import base64
import urllib.parse
import urllib.request
import http.cookiejar
from io import StringIO, BytesIO

try:
    from vinanti.req import *
    from vinanti.log import log_function
except ImportError:
    from req import *
    from log import log_function
    
logger = log_function(__name__)

class RequestObjectUrllib(RequestObject):
    
    def __init__(self, url, hdrs, method, kargs):
        super().__init__(url, hdrs, method, 'urllib', kargs)
        
    def process_request(self):
        opener = None
        cj = None
        if self.verify is False:
            opener = self.handle_https_context(opener, False)
        if self.proxies:
            opener = self.add_proxy(opener)
        if self.session:
            opener, cj = self.enable_cookies(opener)
            
        req = urllib.request.Request(self.url, data=self.data,
                                     headers=self.hdrs,
                                     method=self.method)
        if self.auth:
            opener = self.add_http_auth(self.auth, 'basic', opener)
        elif self.auth_digest:
            opener = self.add_http_auth(self.auth_digest, 'digest', opener)
        try: 
            if opener:
                r_open = opener.open(req, timeout=self.timeout)
            else:
                r_open = urllib.request.urlopen(req, timeout=self.timeout)
        except Exception as err:
            r_open = None
            self.error = str(err)
            logger.error(err)
        ret_obj = ResponseUrllib(self, r_open, cj)
        return ret_obj
                
    def add_http_auth(self, auth_tuple, auth_type, opener=None):
        logger.info(auth_type)
        usr = auth_tuple[0]
        passwd = auth_tuple[1]
        if len(auth_tuple) == 2:
            realm = None
        elif len(auth_tuple) == 3:
            realm = auth_tuple[2]
        password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(realm, self.url, usr, passwd)
        if auth_type == 'basic':
            auth_handler = urllib.request.HTTPBasicAuthHandler(password_manager)
        else:
            auth_handler = urllib.request.HTTPDigestAuthHandler(password_manager)
        if opener:
            logger.info('Adding Handle to Existing Opener')
            opener.add_handler(auth_handler)
        else:
            opener = urllib.request.build_opener(auth_handler)
        return opener
        """
        credentials = '{}:{}'.format(usr, passwd)
        encoded_credentials = base64.b64encode(bytes(credentials, 'utf-8'))
        req.add_header('Authorization', 'Basic {}'.format(encoded_credentials.decode('utf-8')))
        return req
        """
    
    def handle_https_context(self, opener, verify):
        context = ssl.create_default_context()
        if verify is False:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        https_handler = urllib.request.HTTPSHandler(context=context)
        if opener:
            logger.info('Adding HTTPS Handle to Existing Opener')
            opener.add_handler(https_handler)
        else:
            opener = urllib.request.build_opener(https_handler)
        return opener
    
    def enable_cookies(self, opener):
        cj = http.cookiejar.CookieJar()
        cookie_handler = urllib.request.HTTPCookieProcessor(cj)
        if opener:
            logger.info('Adding Cookie Handle to Existing Opener')
            opener.add_handler(cookie_handler)
        else:
            opener = urllib.request.build_opener(cookie_handler)
        return opener, cj
        
    def add_proxy(self, opener):
        logger.info('proxies {}'.format(self.proxies))
        proxy_handler = urllib.request.ProxyHandler(self.proxies)
        if opener:
            logger.info('Adding Proxy Handle to Existing Opener')
            opener.add_handler(proxy_handler)
        else:
            opener = urllib.request.build_opener(proxy_handler)
        return opener


class ResponseUrllib(Response):
    
    def __init__(self, parent=None, req=None, cj=None):
        super().__init__(parent.url, error=parent.error,
                         method=parent.method, out_file=parent.out,
                         out_dir=parent.out_dir)
        if req:
            self.request_object = req
            self.set_information(req, parent)
            self.set_session_cookies(cj)
            
    def set_information(self, req, parent):
        self.info = req.info()
        self.url = req.geturl()
        self.status = req.getcode()
        self.content_encoding = self.info.get('content-encoding')
        self.content_type = self.info.get('content-type')
        
        if not self.content_type:
            self.content_type = 'Not Available'
        else:
            charset_s = re.search('charset[^;]*', self.content_type.lower())
            if charset_s:
                charset_t = charset_s.group()
                charset_t = charset_t.replace('charset=', '')
                self.charset = charset_t.strip()
        if parent.charset:
            self.charset = parent.charset
        
        self.readable_format = [
            'text/plain', 'text/html', 'text/css', 'text/javascript',
            'application/xhtml+xml', 'application/xml', 'application/json',
            'application/javascript', 'application/ecmascript'
            ]
        human_readable = False
        for i in self.readable_format:
            if i in self.content_type.lower():
                human_readable = True
                break
        if not human_readable:
            self.binary = True
        dstorage = None
        if self.content_encoding == 'gzip':
            try:
                storage = BytesIO(req.read())
                dstorage = gzip.GzipFile(fileobj=storage)
            except Exception as err:
                logger.error(err)
        self.dstorage = dstorage
        if parent.method == 'HEAD':
            self.html = 'None'
        elif parent.out:
            if parent.continue_out:
                mode = 'ab'
            else:
                mode = 'wb'
            with open(parent.out, mode) as out_file:
                if dstorage is None:
                    shutil.copyfileobj(req, out_file)
                else:
                    shutil.copyfileobj(dstorage, out_file)
            self.html = 'file saved to:: {}'.format(parent.out)
        else:
            self.read_html(parent, req, dstorage, human_readable)
        
    def save(self, req, out_file, continue_out=False):
        mode = 'wb'
        if continue_out:
            mode = 'ab'
        if req:
            with open(out_file, mode) as out_file:
                if self.dstorage is None:
                    shutil.copyfileobj(req, out_file)
                else:
                    shutil.copyfileobj(dstorage, out_file)
            
    def read_html(self, parent, req, dstorage, human_readable):
        try:
            decoding_required = False
            if dstorage is None and human_readable and not parent.binary:
                self.html = req.read()
                decoding_required = True
            elif dstorage and human_readable and not parent.binary:
                self.html = dstorage.read()
                decoding_required = True
            elif parent.binary:
                self.html = req.read()
            else:
                self.html = ('not human readable content: content-type is {}'
                             .format(self.content_type))
            if decoding_required:
                if self.charset:
                    try:
                        self.html = self.html.decode(self.charset)
                    except Exception as err:
                        logger.error(err)
                        self.html = self.html.decode('utf-8')
                else:
                    self.html = self.html.decode('utf-8')
        except Exception as err:
            logger.error(err)
            self.html = str(err)
    
    def set_session_cookies(self, cj):
        if cj:
            cj_arr = []
            for i in cj:
                cj_arr.append('{}={}'.format(i.name, i.value))
            self.session_cookies = ';'.join(cj_arr)
        else:
            for i in self.info.walk():
                cookie_list = i.get_all('set-cookie')
                cookie_jar = []
                if cookie_list:
                    for i in cookie_list:
                        cookie = i.split(';')[0]
                        cookie_jar.append(cookie)
                    if cookie_jar:
                        cookies = ';'.join(cookie_jar)
                        self.session_cookies = cookies

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

try:
    from vinanti.req_urllib import RequestObjectUrllib
    from vinanti.log import log_function
except ImportError:
    from req_urllib import RequestObjectUrllib
    from log import log_function
    
logger = log_function(__name__)


def complete_function_request(func, kargs):
    req_obj = func(*kargs)
    return req_obj


def get_request(backend, url, hdrs, method, kargs):
    req_obj = None
    if backend == 'urllib':
        req = RequestObjectUrllib(url, hdrs, method, kargs)
        req_obj = req.process_request()
    return req_obj
    

class URL:
    
    def __init__(self, url, depth=0):
        self.url = url
        self.depth = depth
        self.title = ''

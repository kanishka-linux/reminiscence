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
import uuid
import mimetypes

class Formdata:
    
    def __init__(self, form_dict, file_dict):
        self.form_dict = form_dict
        self.file_dict = file_dict
        self.final_list = []
        boundary = str(uuid.uuid4())
        boundary = boundary.replace('-', '')
        self.boundary = '----------' + boundary
    
    def get_content_type(self, filename):
        return mimetypes.guess_type (filename)[0] or 'application/octet-stream'
    
    def arrange_files(self, file_title, file_path, boundary, new_boundary=None):
        file_type = self.get_content_type(file_path)
        file_name = os.path.basename(file_path)
        if new_boundary:
            self.final_list.append(bytes(new_boundary, 'utf-8'))
        else:
            self.final_list.append(bytes(boundary, 'utf-8'))
        if new_boundary:
            hdr = 'Content-Disposition: file; filename="{}"'.format('files', file_name)
        else:
            hdr = 'Content-Disposition: form-data; name="{}"; filename="{}"'.format(file_title, file_name)
        self.final_list.append(bytes(hdr, 'utf-8'))
        hdr = 'Content-Type: {}'.format(file_type)
        self.final_list.append(bytes(hdr, 'utf-8'))
        self.final_list.append(b'')
        with open(file_path, 'rb') as f:
            content = f.read()
            self.final_list.append(content)
        
    def create_content(self):
        boundary = '--' + self.boundary
        if isinstance(self.form_dict, (dict, tuple)):
            for key_val in self.form_dict:
                if isinstance(self.form_dict, dict):
                    key = key_val
                    value = self.form_dict.get(key)
                else:
                    key, value = key_val
                self.final_list.append(bytes(boundary, 'utf-8'))
                hdr = 'Content-Disposition: form-data; name="{}"'.format(key)
                self.final_list.append(bytes(hdr, 'utf-8'))
                self.final_list.append(b'')
                self.final_list.append(bytes(value, 'utf-8'))
        if self.file_dict and isinstance(self.file_dict, str):
            self.arrange_files('filedata', self.file_dict, boundary)
        elif self.file_dict and isinstance(self.file_dict, tuple):
            for i, value in enumerate(self.file_dict):
                title = 'filedata-{}'.format(i)
                self.arrange_files(title, value, boundary)
        elif self.file_dict and isinstance(self.file_dict, dict):
            for key, value in self.file_dict.items():
                self.arrange_files(key, value, boundary)
        self.final_list.append(bytes(boundary+'--', 'utf-8'))
        self.final_list.append(b'')
        body = b'\r\n'.join (self.final_list)
        hdrs = {
            'Content-Type': 'multipart/form-data; boundary={}'.format(self.boundary),
            'Content-Length': str(len(body))
            }
        return body, hdrs
        

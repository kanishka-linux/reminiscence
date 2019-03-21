"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of Reminiscence.

Reminiscence is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reminiscence is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Reminiscence.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import logging
from django import forms
from django.utils import timezone
from .models import Library
from .dbaccess import DBAccess as dbxs

logger = logging.getLogger(__name__)


class AddDir(forms.Form):
    
    create_directory = forms.CharField(
        max_length=2048, required=True,
        widget=forms.TextInput(attrs={'placeholder':'Create New Directory'})
        )
    DEFAULT_DIRECTORY = 'Bookmarks'
    
    def clean_and_save_data(self, usr):
        dirname = self.cleaned_data.get('create_directory')
        http = re.match(r'^(?:http)s?://(?!/)', dirname)
        if http:
            url = dirname
            qdir = Library.objects.filter(usr=usr,
                                          directory=self.DEFAULT_DIRECTORY)
            logger.info('adding {} to Bookmark'.format(url))
            if not qdir and len(url) > 9:
                Library.objects.create(usr=usr, directory=self.DEFAULT_DIRECTORY, timestamp=timezone.now()).save()
                dbxs.process_add_url(usr, url, self.DEFAULT_DIRECTORY, False)
                logger.debug('add--bookmark')
            elif qdir and len(url) > 9:
                nqdir = qdir.filter(url=url)
                if not nqdir:
                    dbxs.process_add_url(usr, url, self.DEFAULT_DIRECTORY, False)
        else:
            dirname = re.sub(r'/|:|#|\?|\\\\|\%', '-', dirname)
            if dirname:
                qdir = Library.objects.filter(usr=usr, directory=dirname)
                if not qdir:
                    Library.objects.create(usr=usr, directory=dirname, timestamp=timezone.now()).save()
        
        
class AddURL(forms.Form):
    add_url = forms.URLField(
        max_length=2048, required=True,
        widget=forms.TextInput(attrs={'placeholder':'Enter URL'})
    )
    
    
class RenameDir(forms.Form):
    rename_directory = forms.CharField(
        max_length=200, required=True,
        widget=forms.TextInput(attrs={'placeholder':'Enter New Name'})
    )
    
    def clean_and_rename(self, usr, directory):
        ren_dir = self.cleaned_data.get('rename_directory')
        if ren_dir and ren_dir != directory:
            ren_dir = re.sub(r'/|:|#|\?|\\\\|\%', '-', ren_dir)
            if '/' in directory:
                dbxs.remove_subdirectory_link(usr, directory, ren_dir)
                pdir, _ = directory.rsplit('/', 1)
                ren_dir = pdir + '/' + ren_dir
            Library.objects.filter(usr=usr, directory=directory).update(directory=ren_dir)
            qlist = Library.objects.filter(usr=usr, directory__istartswith=directory+'/')
            for row in qlist:
                row.directory = re.sub(directory, ren_dir, row.directory, 1)
                row.save()


class RemoveDir(forms.Form):
    CHOICES = (
        (False, 'Do Not Remove'),
        (True, 'Remove')
    )
    remove_directory = forms.BooleanField(widget=forms.Select(choices=CHOICES))
    
    def check_and_remove_dir(self, usr, directory):
        rem_dir = self.cleaned_data.get('remove_directory', '')
        if rem_dir is True:
            qlist = Library.objects.filter(usr=usr, directory=directory)
            for row in qlist:
                dbxs.remove_url_link(usr, row=row)
            qlist = Library.objects.filter(usr=usr, directory__istartswith=directory+'/')
            for row in qlist:
                dbxs.remove_url_link(usr, row=row)
        if '/' in directory:
            dbxs.remove_subdirectory_link(usr, directory)
            

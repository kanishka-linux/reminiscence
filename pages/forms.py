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
                print('add--bookmark')
            elif qdir and len(url) > 9:
                nqdir = qdir.filter(url=url)
                print(nqdir, 'nq')
                if not nqdir:
                    dbxs.process_add_url(usr, url, self.DEFAULT_DIRECTORY, False)
        else:
            if '/' in dirname or ':' in dirname:
                dirname = re.sub(r'/|:', '-', dirname)
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
    
    
class RemoveDir(forms.Form):
    CHOICES = (
        ('no', 'Do Not Remove'),
        ('yes', 'Remove')
    )
    remove_directory = forms.BooleanField(widget=forms.Select(choices=CHOICES))
    

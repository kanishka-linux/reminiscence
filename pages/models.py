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

from django.db import models
from django.contrib.auth.models import User


class UserSettings(models.Model):
    
    WHITE = 0
    DARK = 1
    LIGHT = 2
    GRAY = 3
    
    READER_CHOICES = (
        (WHITE, 'default'),
        (DARK, 'dark'),
        (LIGHT, 'light'),
        (GRAY, 'gray')
    )
    
    usrid =  models.ForeignKey(User, related_name='usr_settings',
                               on_delete=models.CASCADE)
    autotag = models.BooleanField(default=False)
    auto_summary = models.BooleanField(default=False)
    auto_archive = models.BooleanField(default=False)
    total_tags = models.PositiveSmallIntegerField(default=5)
    public_dir = models.CharField(max_length=2048, null=True)
    group_dir = models.CharField(max_length=2048, null=True)
    save_pdf = models.BooleanField(default=False)
    save_png = models.BooleanField(default=False)
    png_quality = models.PositiveSmallIntegerField(default=85)
    pagination_value = models.PositiveSmallIntegerField(default=100)
    buddy_list = models.CharField(max_length=8192, null=True)
    download_manager = models.CharField(max_length=8192, default='wget {iurl} -O {output}')
    media_streaming = models.BooleanField(default=False)
    reader_theme = models.PositiveSmallIntegerField(choices=READER_CHOICES, default=WHITE)
    
    def __str__(self):
        return self.usrid
        
class Library(models.Model):
    
    PUBLIC = 0
    PRIVATE = 1
    GROUP = 2
    ACCESS_CHOICES = (
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
        (GROUP, 'Group')
    )
    
    usr = models.ForeignKey(User, related_name='usr', on_delete=models.CASCADE)
    directory = models.CharField(max_length=2048)
    url = models.CharField(max_length=4096, null=True)
    icon_url = models.CharField(max_length=4096, null=True)
    title = models.CharField(max_length=2048, null=True)
    timestamp = models.DateTimeField(null=True)
    media_path = models.CharField(max_length=4096, null=True)
    access = models.PositiveSmallIntegerField(choices=ACCESS_CHOICES, default=PRIVATE)
    summary = models.TextField(null=True)
    tags = models.CharField(max_length=4096, null=True)
    media_element = models.BooleanField(default=False)
    subdir = models.CharField(max_length=8192, null=True)
    reader_mode = models.PositiveSmallIntegerField(choices=UserSettings.READER_CHOICES,
                                                   default=UserSettings.WHITE)
    
    def __str__(self):
        return self.usr.username


class Tags(models.Model):
    
    tag = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.tag


class URLTags(models.Model):
    
    usr_id  = models.ForeignKey(User, related_name='usr_tag',
                                on_delete=models.CASCADE)
    url_id = models.ForeignKey(Library,
                               related_name='url_library',
                               on_delete=models.CASCADE)
    tag_id = models.ForeignKey(Tags, related_name='tag_name',
                               on_delete=models.CASCADE)
                               
    def __str__(self):
        return '{}, {}'.format(self.url_id, self.tag_id)


class GroupTable(models.Model):
    
    user_set = models.ForeignKey(UserSettings, related_name='usr_set',
                                 on_delete=models.CASCADE)
    buddy = models.ForeignKey(User, related_name='usr_buddy',
                              on_delete=models.CASCADE)
    

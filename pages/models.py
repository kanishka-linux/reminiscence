from datetime import datetime
from django.db import models
from django.contrib.auth.models import User


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
    title = models.CharField(max_length=2048, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)
    media_path = models.CharField(max_length=4096, null=True)
    access = models.PositiveSmallIntegerField(choices=ACCESS_CHOICES, default=PRIVATE)
    summary = models.TextField(null=True)
    
    def __str__(self):
        return '{}. {}'.format(self.id, self.title)

        
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
        return '{}, {}'.format(url_id, tag_id)

        
class UserSettings(models.Model):
    
    usrid =  models.ForeignKey(User, related_name='usr_settings',
                               on_delete=models.CASCADE)
    autotag = models.BooleanField(default=False)
    auto_summary = models.BooleanField(default=False)


class GroupTable(models.Model):
    
    user_set = models.ForeignKey(UserSettings, related_name='usr_set',
                                 on_delete=models.CASCADE)
    buddy = models.ForeignKey(User, related_name='usr_buddy',
                              on_delete=models.CASCADE)
    

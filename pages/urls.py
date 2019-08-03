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

from django.urls import path
from django.urls import re_path as url
from .views import *
from accounts.views import signup
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', dashboard, name='home'),
    path('signup/', signup, name='signup'),
    path('annotate/annotations', create_annotations, name='ann_create'),
    path('annotate/annotations/<int:annot_id>', modify_annotations, name='ann_modify'),
    path('annotate/', annotation_root, name='ann_root'),
    url(r'^annotate/search', search_annotations, name='ann_s'),
    url(r'^settings/password/$',
        auth_views.PasswordChangeView.as_view(template_name='password_change.html'),
        name='password_change'),
    url(r'^settings/password/done/$',
        auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
        name='password_change_done'),
    url(r'^logout/', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^(?P<username>[\w\d.@+-]+)/?$', dashboard, name='home_page'),
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-]+)/epub-bookmark/(?P<epub_loc>[\d]+\/(epubcfi)(.?)*)', navigate_directory, name='navigate_directory_epub'),
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-]+)/?$', navigate_directory, name='navigate_directory'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-]+)/(?P<url_id>[\d]+)/archive/EPUBDIR/(?P<meta_path>(.?)*)', perform_epub_operation, name='epub_meta'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-]+)/(?P<url_id>[\d]+)/archive/EPUBDIR/read-epub$', perform_epub_operation, name='epub_read_file'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/subdir/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<url_id>[\d]+)/archive/EPUBDIR/(?P<meta_path>(.?)*)', perform_epub_operation, name='subdir_epub_meta'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/subdir/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<url_id>[\d]+)/archive/EPUBDIR/read-epub', perform_epub_operation, name='subdir_epub_read_file'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/subdir/(?P<directory>[\w\d\s.&@+-\/]+)/epub-bookmark/(?P<epub_loc>[\d]+\/(epubcfi)(.?)*)', navigate_subdir, name='navigate_subdir_epub'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/subdir/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<url_id>[\d]+)/(?P<rel_path>(.?)*\.(png|jpeg|jpg))', get_relative_resources, name='nav_subdir_resources'),
    url(r'^(?P<username>[\w\d.@+-]+)/subdir/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<mode>(readhtml|readcustom|readpdf))(?P<html_pos>(-[\d]+)+)$', record_reading_position, name='record_subdir_pos'),
    url(r'^(?P<username>[\w\d.@+-]+)/subdir/(?P<directory>[\w\d\s.&@+-\/]+)$', navigate_subdir, name='navigate_subdir'),
    url(r'^(?P<username>[\w\d.@+-]+)/tag/(?P<tagname>[\w\d\s.&@+-]+)/?$', navigate_directory, name='navigate_tag'),
    path('<username>/api/request', api_points, name='api_points'),
    path('<username>/profile/public', public_profile, name='public_profile'),
    path('<username>/profile/group', group_profile, name='group_profile'),
    url(r'^(?P<username>[\w\d.@+-]+)/getarchivedvideo/(?P<video_id>[\w\d\_\-]+)/?$', get_archived_video_link, name='get_video'),
    url(r'^(?P<username>[\w\d.@+-]+)/getarchivedplaylist/(?P<directory>[\w\d\s.&@+-\/]+)/playlist/(?P<playlist_id>[\w\d\_\-]+)/?$', get_archived_playlist, name='get_playlist'),
    path('<username>/<str:directory>/rename', rename_operation, name='rename_operation'),
    path('<username>/<str:directory>/remove', remove_operation, name='remove_operation'),
    path('<username>/<str:directory>/<int:url_id>/archive', perform_link_operation, name='archive_request'),
    path('<username>/<str:directory>/<int:url_id>/archived-note', perform_link_operation, name='archive_note_request'),
    path('<username>/<str:directory>/<int:url_id>/archived-note-save', perform_link_operation, name='archive_note_request_save'),
    path('<username>/<str:directory>/<int:url_id>/remove', perform_link_operation, name='remove_operation_link'),
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<url_id>[\d]+)/(?P<mode>(readpdf|readcustom|readhtmtl|pdf-annotpdf))(?P<html_pos>(\-[\d]+)+)$', record_reading_position, name='record_pos'),
    path('<username>/<str:directory>/<int:url_id>/read', perform_link_operation, name='read_link'),
    path('<username>/<str:directory>/<int:url_id>/read-dark', perform_link_operation, name='read_dark'),
    path('<username>/<str:directory>/<int:url_id>/read-light', perform_link_operation, name='read_light'),
    path('<username>/<str:directory>/<int:url_id>/read-default', perform_link_operation, name='read_default'),
    path('<username>/<str:directory>/<int:url_id>/read-gray', perform_link_operation, name='read_gray'),
    path('<username>/<str:directory>/<int:url_id>/read-pdf', perform_link_operation, name='read_pdf'),
    path('<username>/<str:directory>/<int:url_id>/pdf-annot', perform_link_operation, name='pdf_annot'),
    path('<username>/<str:directory>/<int:url_id>/read-png', perform_link_operation, name='read_png'),
    path('<username>/<str:directory>/<int:url_id>/read-html', perform_link_operation, name='read_html'),
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-]+)/(?P<url_id>[\d]+)/resources/', get_resources, name='navigate_resources'),
    
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<url_id>[\d]+)/resources/', get_resources, name='navigate_resources_subdir'),
    path('<username>/<str:directory>/<int:url_id>/edit-bookmark', perform_link_operation, name='edit_bookmark'),
    path('<username>/<str:directory>/<int:url_id>/move-bookmark', perform_link_operation, name='move_bookmark'),
    url('^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/move-bookmark-multiple$', perform_link_operation, name='move_bookmark_multiple'),
    url('^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/archive-bookmark-multiple$', perform_link_operation, name='archive_bookmark_multiple'),
    url('^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/merge-bookmark-with$', perform_link_operation, name='merge_bookmark_with'),
    url('^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/edit-tags-multiple$', perform_link_operation, name='edit_tags_multiple'),
    url(r'^(?P<username>[\w\d.@+-]+)/(?P<directory>[\w\d\s.&@+-\/]+)/(?P<url_id>[\d]+)/(?P<rel_path>(.?)*)', get_relative_resources, name='navigate_url_resources')
]

#url(r'^.*$', default_dest, name='catch_all')

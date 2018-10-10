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

import os
import re
import json
import time
import shutil
import pickle
import logging
from functools import reduce
from itertools import chain
from urllib.parse import urlparse
from datetime import datetime, timedelta
from mimetypes import guess_extension, guess_type
from collections import Counter
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.decorators import login_required
from django.conf import settings

from vinanti import Vinanti
from bs4 import BeautifulSoup

from .models import Library, Tags, URLTags, UserSettings
from .forms import AddDir, RenameDir, RemoveDir, AddURL
from .custom_read import CustomRead as cread
from .dbaccess import DBAccess as dbxs
from .summarize import Summarizer
from .utils import ImportBookmarks


logger = logging.getLogger(__name__)


@login_required
def dashboard(request, username=None, directory=None):
    usr = request.user
    if username and username != usr.username:
        return redirect('/'+usr.username)
    if request.method == 'POST':
        form = AddDir(request.POST)
        if form.is_valid():
            form.clean_and_save_data(usr)
    form = AddDir()
    usr_list = Library.objects.filter(usr=usr).only('directory').order_by('directory')
    usr_list = [i.directory for i in usr_list if i.directory]
    usr_list = Counter(usr_list)
    nlist = []
    index = 1
    for key, value in usr_list.items():
        base_dir = '/{}/{}'.format(usr, key)
        base_remove = base_dir + '/remove'
        base_rename = base_dir + '/rename'
        nlist.append([index, key, value-1, base_dir, base_rename, base_remove])
        index += 1
    response = render(request, 'home.html', {'usr_list': nlist, 'form':form})
    return response


@login_required
def rename_operation(request, username, directory):
    usr = request.user
    if username and usr.username != username:
        return redirect('logout')
    elif directory:
        if request.method == 'POST':
            form = RenameDir(request.POST)
            if form.is_valid():
                form.clean_and_rename(usr, directory)
            else:
                logger.debug('invalid values {}'.format(request.POST))
            return redirect('home')
        else:
            form = RenameDir()
            base_dir = '/{}/{}'.format(usr, directory)
            base_remove = base_dir + '/remove'
            base_rename = base_dir + '/rename'
            nlist = [[1, directory, 'N/A', base_dir, base_rename, base_remove]]
            return render(request, 'home.html', {'usr_list': nlist, 'form':form})
    else:
        return redirect('logout')
        

@login_required
def remove_operation(request, username, directory):
    usr = request.user
    if username and usr.username != username:
        return redirect('logout')
    elif directory:
        if request.method == 'POST':
            form = RemoveDir(request.POST)
            if form.is_valid():
                form.check_and_remove_dir(usr, directory)
            else:
                logger.debug('invalid values {}'.format(request.POST))
            return redirect('home')
        else:
            form = RemoveDir()
            base_dir = '/{}/{}'.format(usr, directory)
            base_remove = base_dir + '/remove'
            base_rename = base_dir + '/rename'
            nlist = [[1, directory, 'N/A', base_dir, base_rename, base_remove]]
            return render(request, 'home.html', {'usr_list': nlist, 'form':form})
    else:
        return redirect('logout')


@login_required
def get_resources(request, username, directory, url_id):
    usr = request.user
    logger.info(request.path_info)
    if username and usr.username != username:
        return HttpResponse('Not Allowed')
    elif directory and url_id:
        if request.method == 'GET':
            resource_dir = os.path.join(settings.ARCHIVE_LOCATION, 'resources', str(url_id))
            loc = request.path_info.rsplit('/', 1)[1]
            if loc.endswith('.css'):
                content_type = 'text/css'
            else:
                content_type = 'image/jpeg'
            resource_loc = os.path.join(resource_dir, loc)
            logger.debug('resource-loc: {}'.format(resource_loc))
            if os.path.exists(resource_loc):
                response = FileResponse(open(resource_loc, 'rb'))
                response['content-type'] = content_type
                response['content-length'] = os.stat(resource_loc).st_size
                return response
            else:
                logger.debug('resource: {} not available'.format(resource_loc))
    return HttpResponse('Not Found')

@login_required
def perform_link_operation(request, username, directory, url_id=None):
    usr = request.user
    logger.info(request.path_info)
    if username and usr.username != username:
        return HttpResponse('Not Allowed')
    elif directory and url_id:
        if request.method == 'POST':
            if request.path_info.endswith('remove'):
                rem_lnk = request.POST.get('remove_url', '')
                logger.debug('{} , {}'.format(url_id, request.POST))
                if rem_lnk == 'yes':
                    dbxs.remove_url_link(usr, url_id=url_id)
                return HttpResponse('Deleted')
            elif request.path_info.endswith('move-bookmark'):
                msg = dbxs.move_bookmarks(usr, request, url_id)
                return HttpResponse(msg)
            elif request.path_info.endswith('edit-bookmark'):
                msg = dbxs.edit_bookmarks(usr, request, url_id)
                return HttpResponse(msg)
            else:
                return HttpResponse('Wrong command')
        elif request.method == 'GET':
            if request.path_info.endswith('archive'):
                return cread.get_archived_file(usr, url_id, mode='archive', req=request)
            elif request.path_info.endswith('read'):
                return cread.read_customized(usr, url_id)
            elif request.path_info.endswith('read-pdf'):
                return cread.get_archived_file(usr, url_id, mode='pdf')
            elif request.path_info.endswith('read-png'):
                return cread.get_archived_file(usr, url_id, mode='png')
            elif request.path_info.endswith('read-html'):
                return cread.get_archived_file(usr, url_id, mode='html')
        else:
            return HttpResponse('Method not Permitted')
    elif directory and request.method == 'POST':
        msg = 'nothing'
        if request.path_info.endswith('move-bookmark-multiple'):
            msg = dbxs.move_bookmarks(usr, request, single=False)
        elif request.path_info.endswith('archive-bookmark-multiple'):
            msg = dbxs.group_links_actions(usr, request, directory, mode='archive')
        elif request.path_info.endswith('merge-bookmark-with'):
            msg = dbxs.group_links_actions(usr, request, directory, mode='merge')
        elif request.path_info.endswith('edit-tags-multiple'):
            msg = dbxs.group_links_actions(usr, request, directory, mode='tags')
        return HttpResponse(msg)
    else:
        return HttpResponse('What are you trying to accomplish!')


@login_required
def default_dest(request):
    return redirect('home')

def public_profile(request, username):
    qlist = User.objects.filter(username=username)
    if qlist:
        usr = qlist[0]
        qlist = UserSettings.objects.filter(usrid=usr)
        if qlist:
            public_dir = qlist[0].public_dir
            if public_dir:
                usr_list = dbxs.get_rows_by_directory(usr, directory=public_dir)
                nlist = dbxs.populate_usr_list(usr, usr_list)
                base_dir = '/{}/{}'.format(usr, public_dir)
                return render(
                            request, 'public.html',
                            {
                                'usr_list': nlist, 'form':"",
                                'base_dir':base_dir, 'dirname':public_dir
                            }
                        )
    return HttpResponse('No Public Profile Available')

@login_required
def group_profile(request, username):
    group_usr = request.user
    qlist = User.objects.filter(username=username)
    if qlist:
        usr = qlist[0]
        qlist = UserSettings.objects.filter(usrid=usr)
        if qlist:
            buddy_list = qlist[0].buddy_list
            group_dir = qlist[0].group_dir
            if buddy_list and group_dir:
                nbuddy = [i.strip() for i in buddy_list.split(',') if i.strip()]
                if group_usr.username in nbuddy:
                    usr_list = dbxs.get_rows_by_directory(usr, directory=group_dir)
                    nlist = dbxs.populate_usr_list(usr, usr_list)
                    base_dir = '/{}/{}'.format(usr, group_dir)
                    return render(
                                request, 'home_dir.html',
                                {
                                    'usr_list': nlist, 'form':"",
                                    'base_dir':base_dir, 'dirname':group_dir,
                                    'refresh': 'no'
                                }
                            )
    return HttpResponse('No Group Profile Available')
    
@login_required
def navigate_directory(request, username, directory=None, tagname=None):
    usr = request.user
    base_dir = '/{}/{}'.format(usr, directory)
    usr_list = []
    if username and usr.username != username:
        return redirect('/'+usr.username)
    add_url = 'no'
    if directory or tagname:
        place_holder = 'Enter URL'
        if request.method == 'POST' and directory:
            form = AddURL(request.POST)
            url_name = request.POST.get('add_url', '')
            if form.is_valid() or (url_name and url_name.startswith('md:')):
                row = UserSettings.objects.filter(usrid=usr)
                dbxs.add_new_url(usr, request, directory, row)
                add_url = 'yes'
            else:
                place_holder = 'Wrong Input, Enter URL'
        form = AddURL()
        form.fields['add_url'].widget.attrs['placeholder'] = place_holder
        if directory:
            usr_list = dbxs.get_rows_by_directory(usr, directory=directory)
        else:
            directory = 'tag'
            usr_list = dbxs.get_rows_by_tag(usr, tagname)
            if usr_list is None:
                return redirect('home')
        nlist = dbxs.populate_usr_list(usr, usr_list)
        
        page = request.GET.get('page', 1)
        row = UserSettings.objects.filter(usrid=usr)
        if row and row[0].pagination_value:
            paginator = Paginator(nlist, row[0].pagination_value)
        else:
            paginator = Paginator(nlist, 100)
        try:
            dirlist = paginator.page(page)
        except PageNotAnInteger:
            dirlist = paginator.page(1)
        except EmptyPage:
            dirlist = paginator.page(paginator.num_pages)
        
        base_dir = '/{}/{}'.format(usr, directory)
        return render(
                    request, 'home_dir.html',
                    {
                        'usr_list': dirlist, 'form':form,
                        'base_dir':base_dir, 'dirname':directory,
                        'refresh':add_url
                    }
                )
    else:
        return redirect('home')

def get_archived_video_link(request, username, video_id):
    if video_id and '-' in video_id:
        _, video_id = video_id.rsplit('-', 1)
    if os.path.isfile(cread.CACHE_FILE):
        with open(cread.CACHE_FILE, 'rb') as fd:
            cread.VIDEO_ID_DICT = pickle.load(fd)
    return cread.get_archived_video(request, username, video_id)

@login_required
def get_archived_playlist(request, username, directory, playlist_id):
    plfile = os.path.join(settings.TMP_LOCATION, playlist_id)
    pls_txt = ''
    if os.path.isfile(plfile):
        with open(plfile, 'rb') as fd:
            pls_txt = pickle.load(fd)
        os.remove(plfile)
    response = HttpResponse()
    response['Content-Type'] = 'audio/mpegurl'
    response['Content-Disposition'] = 'attachment; filename={}.m3u'.format(directory)
    response.write(bytes(pls_txt, 'utf-8'))
    return response

@login_required
def api_points(request, username):
    usr = request.user
    default_dict = {'status':'none'}
    if username and usr.username != username:
        return redirect('/'+usr.username)
    if request.method == 'POST':
        req_list = request.POST.get('listdir', '')
        req_search = request.POST.get('search', '')
        req_archive = request.POST.get('archive', '')
        req_get_settings = request.POST.get('get_settings', '')
        req_set_settings = request.POST.get('set_settings', '')
        req_summary = request.POST.get('req_summary', '')
        req_import = request.POST.get('import-bookmark', '')
        req_upload = request.POST.get('upload-binary', '')
        req_chromium_backend = request.POST.get('chromium-backend', '')
        req_media_path = request.POST.get('get-media-path', '')
        req_media_playlist = request.POST.get('generate-media-playlist', '')
        logger.debug(req_import)
        logger.debug(request.FILES)
        if req_list and req_list == 'yes':
            q_list = Library.objects.filter(usr=usr)
            dir_list = set()
            for i in q_list:
                dirn = i.directory
                if dirn:
                    dir_list.add(dirn)
            dir_list = list(dir_list)
            dir_list.sort()
            dir_dict = {'dir':dir_list}
            return HttpResponse(json.dumps(dir_dict))
        elif req_media_path and req_media_path == 'yes':
            url_id = request.POST.get('url_id', '')
            if url_id and url_id.isnumeric():
                return_path = cread.get_archived_file(usr, url_id, mode='archive',
                                                      req=request, return_path=True)
                return HttpResponse(json.dumps({'link':return_path}))
        elif req_media_playlist and req_media_playlist == 'yes':
            directory = request.POST.get('directory', '')
            ip = request.POST.get('ip', '')
            logger.debug('{} {}'.format(directory, ip))
            pls_path = cread.generate_archive_media_playlist(ip, usr, directory)
            return HttpResponse(pls_path)
        elif req_import and req_import == 'yes':
            req_file = request.FILES.get('file-upload', '')
            if req_file:
                filename = req_file.name
                logger.info(filename)
                mime_type = guess_type(filename)[0]
                logger.info(mime_type)
                if mime_type in ['text/html', 'text/htm']:
                    content = req_file.read().decode('utf-8')
                    qlist = UserSettings.objects.filter(usrid=usr)
                    if qlist:
                        settings_row = qlist[0]
                    else:
                        settings_row = None
                    ImportBookmarks.import_bookmarks(usr, settings_row,
                                                     content, mode='content')
            return HttpResponse('OK')
        elif req_upload and req_upload == 'yes':
            dirname = request.POST.get('dirname', '')
            if not dirname:
                dirname = 'Uploads'
                qdir = Library.objects.filter(usr=usr, directory=dirname)
                if not qdir:
                    Library.objects.create(usr=usr, directory=dirname, timestamp=timezone.now()).save()
            dbxs.save_in_binary_format(usr, request, dirname)
            return HttpResponse('OK')
        elif req_search and len(req_search) > 2:
            tag_list = []
            if req_search.startswith('tag:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'tag'
            elif req_search.startswith('url:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'url'
            elif req_search.startswith('dir:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'dir'
            elif req_search.startswith('sum:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'summary'
            elif req_search.startswith('tag-wall:'):
                qlist = Library.objects.filter(usr=usr)
                tagset = set()
                mode = 'tag-wall'
                if qlist:
                    tags = [row.tags.split(',') for row in qlist if row.tags]
                    fun = lambda *x : set(chain(*x))
                    tag_list = list(reduce(fun, tags))
                    tag_list.sort()
            else:
                search_term = req_search
                mode = 'title'
            if mode == 'tag-wall':
                usr_list = [('Total Tags', '', '', timezone.now(), tag_list, 'Tag-Wall', '', '')]
            else:
                logger.info('{}->{}'.format(mode, search_term))
                usr_list = dbxs.get_rows_by_directory(usr, search_mode=mode, search=search_term)
            ndict = dbxs.populate_usr_list(usr, usr_list, create_dict=True)
            return HttpResponse(json.dumps(ndict))
        elif req_summary and req_summary == 'yes':
            ndict = {}
            reqid = request.POST.get('url_id', '')
            summary = 'not available'
            if reqid and reqid.isnumeric():
                qlist = Library.objects.filter(usr=usr, id=int(reqid))
                if qlist:
                    row = qlist[0]
                    summary = row.summary
                    if not summary:
                        media_path = row.media_path
                        if media_path and os.path.exists(media_path):
                            content = ''
                            with open(media_path, mode='r', encoding='utf-8') as fd:
                                content = fd.read()
                            if content:
                                summary, tags_list = Summarizer.get_summary_and_tags(content, 2)
                    if not summary:
                        summary = ('Automatic Summary not generated!\
                                    First enable automatic summary generation\
                                    from settings. Remove this link and add it again.')
                        summary = re.sub(' +', ' ', summary)
            ndict.update({'summary':summary})
            return HttpResponse(json.dumps(ndict))
        elif req_summary and req_summary == 'modify':
            reqid = request.POST.get('url_id', '')
            summary = request.POST.get('modified_summary', '')
            msg = "no modied"
            logger.debug(summary)
            if reqid and reqid.isnumeric() and summary:
                qlist = Library.objects.filter(usr=usr, id=int(reqid)).update(summary=summary)
                msg = 'modified summary'
            return HttpResponse(msg)
        elif req_get_settings and req_get_settings == 'yes':
            qlist = UserSettings.objects.filter(usrid=usr)
            if qlist:
                row = qlist[0]
                if row.public_dir:
                    public_dir = row.public_dir
                else:
                    public_dir = ""
                if row.group_dir:
                    group_dir = row.group_dir
                else:
                    group_dir = ""
                ndict = {
                    'autotag': row.autotag,
                    'auto_summary':row.auto_summary,
                    'total_tags': row.total_tags,
                    'public_dir': public_dir,
                    'group_dir': group_dir,
                    'save_pdf': row.save_pdf,
                    'save_png': row.save_png,
                    'png_quality': row.png_quality,
                    'auto_archive': row.auto_archive,
                    'pagination_value': row.pagination_value,
                    'download_manager': row.download_manager,
                    'media_streaming': row.media_streaming
                }
                if row.buddy_list:
                    ndict.update({'buddy':row.buddy_list})
                else:
                    ndict.update({'buddy':''})
            else:
                ndict = {
                    'autotag': False,
                    'auto_summary': False,
                    'total_tags': 5,
                    'buddy': "",
                    'public_dir': "",
                    'group_dir': "",
                    'save_pdf': False,
                    'save_png': False,
                    'png_quality': 85,
                    'auto_archive': False,
                    'pagination_value': 100,
                    'download_manager': 'wget {iurl} -O {output}',
                    'media_streaming': False
                }
            return HttpResponse(json.dumps(ndict))
        elif req_set_settings and req_set_settings == 'yes':
            autotag = request.POST.get('autotag', 'false')
            auto_summary = request.POST.get('auto_summary', 'false')
            total_tags = request.POST.get('total_tags', '5')
            buddy_list = request.POST.get('buddy_list', '')
            public_dir = request.POST.get('public_dir', '')
            group_dir = request.POST.get('group_dir', '')
            save_pdf = request.POST.get('save_pdf', '')
            save_png = request.POST.get('save_png', '')
            png_quality = request.POST.get('png_quality', '')
            auto_archive = request.POST.get('auto_archive', '')
            pagination_value = request.POST.get('pagination_value', '100')
            media_streaming = request.POST.get('media_streaming', 'false')
            dm_str = 'wget {iurl} -O {output}'
            download_manager = request.POST.get('download_manager', dm_str)
            if autotag == 'true':
                autotag = True
            else:
                autotag = False
            if auto_summary == 'true':
                auto_summary = True
            else:
                auto_summary = False
            if total_tags.isnumeric():
                total_tags = int(total_tags)
            else:
                total_tags = 5
            if pagination_value.isnumeric():
                pagination_value = int(pagination_value)
            else:
                pagination_value = 100
            if save_pdf == 'true':
                save_pdf = True
            else:
                save_pdf = False
            if save_png == 'true':
                save_png = True
            else:
                save_png = False
            if auto_archive == 'true':
                auto_archive = True
            else:
                auto_archive = False
            if media_streaming == 'true':
                media_streaming = True
            else:
                media_streaming = False
            if png_quality and png_quality.isnumeric():
                png_quality = int(png_quality) if int(png_quality) in range(0, 101) else 85
            else:
                png_quality = 85
            if buddy_list:
                buddy_list = [i.strip() for i in buddy_list.split(',') if i.strip()]
                buddy_list = ','.join(buddy_list)
            qlist = UserSettings.objects.filter(usrid=usr)
            if qlist:
                row = qlist[0]
                row.autotag = autotag
                row.auto_summary = auto_summary
                row.total_tags = total_tags
                row.buddy_list = buddy_list
                row.public_dir = public_dir
                row.group_dir = group_dir
                row.save_pdf = save_pdf
                row.save_png = save_png
                row.png_quality = png_quality
                row.auto_archive = auto_archive
                row.pagination_value = pagination_value
                row.media_streaming = media_streaming
                row.download_manager = download_manager
                row.save()
            else:
                row = UserSettings.objects.create(usrid=usr, autotag=autotag,
                                                  auto_summary=auto_summary,
                                                  total_tags=total_tags,
                                                  buddy_list=buddy_list,
                                                  public_dir=public_dir,
                                                  group_dir=group_dir,
                                                  save_pdf=save_pdf,
                                                  save_png=save_png,
                                                  png_quality=png_quality,
                                                  auto_archive=auto_archive,
                                                  pagination_value=pagination_value,
                                                  media_streaming=media_streaming,
                                                  download_manager=download_manager)
                row.save()
            if (autotag or auto_summary) and not os.path.exists(settings.NLTK_DATA_PATH):
                dbxs.vnt_task.function(Summarizer.check_data_path)
            ndict = {'status':'ok'}
            return HttpResponse(json.dumps(ndict))
        elif req_chromium_backend and req_chromium_backend == 'yes':
            url_id = request.POST.get('url_id', '')
            mode = request.POST.get('mode', '')
            if mode and mode in ['pdf', 'dom']:
                qlist = UserSettings.objects.filter(usrid=usr)
                if qlist:
                    settings_row = qlist[0]
                else:
                    settings_row = None
                qset = Library.objects.filter(usr=usr, id=url_id)
                if qset:
                    row = qset[0]
                    if row.media_path:
                        media_path_parent, _ = os.path.split(row.media_path)
                        dbxs.convert_html_pdf_with_chromium(media_path_parent,
                                                            settings_row, row,
                                                            row.url, row.media_path,
                                                            mode=mode)
                return HttpResponse('OK')
        elif req_archive and req_archive in ['yes', 'force']:
            url_id = request.POST.get('url_id', '')
            dirname = request.POST.get('dirname', '')
            logger.debug('{}, {}'.format(url_id, dirname))
            if url_id and url_id.isnumeric() and dirname:
                qset = Library.objects.filter(usr=usr, id=url_id)
                if qset:
                    row = qset[0]
                    media_path = row.media_path
                    url_ar = '/{}/{}/{}/archive'.format(usr.username, dirname, url_id)
                    dict_val = {'url': url_ar}
                    if media_path and os.path.exists(media_path) and req_archive == 'yes':
                        dict_val.update({'status':'already archived'})
                    else:
                        qlist = UserSettings.objects.filter(usrid=usr)
                        if qlist:
                            set_row = qlist[0]
                        else:
                            set_row = None
                        dbxs.process_add_url(usr, row.url, dirname,
                                             archive_html=True, row=row,
                                             settings_row=set_row)
                        dict_val.update({'status':'ok'})
                    return HttpResponse(json.dumps(dict_val))
                        
    return HttpResponse(json.dumps(default_dict))
    

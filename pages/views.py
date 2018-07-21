import os
import json
import shutil
import logging

from urllib.parse import urlparse
from datetime import datetime, timedelta
from mimetypes import guess_extension
from collections import Counter

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.conf import settings

from vinanti import Vinanti
from bs4 import BeautifulSoup

from .models import Library, Tags, URLTags
from .forms import AddDir, RenameDir, RemoveDir, AddURL
from .custom_read import CustomRead as cread
from .dbaccess import DBAccess as dbxs

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
    usr_list = Library.objects.filter(usr=usr)
    usr_list = [i.directory for i in usr_list if i.directory]
    usr_list.sort()
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
            ren_dir = request.POST.get('rename_directory', '')
            if ren_dir and ren_dir != directory:
                Library.objects.filter(usr=usr, directory=directory).update(directory=ren_dir)
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
            rem_dir = request.POST.get('remove_directory', '')
            if rem_dir == 'yes':
                Library.objects.filter(usr=usr, directory=directory).delete()
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
def perform_link_operation(request, username, directory, url_id):
    usr = request.user
    print(request.path_info)
    if username and usr.username != username:
        return HttpResponse('Not Allowed')
    elif directory and url_id:
        if request.method == 'POST':
            if request.path_info.endswith('remove'):
                rem_lnk = request.POST.get('remove_url', '')
                print(url_id, request.POST)
                if rem_lnk == 'yes':
                    dbxs.remove_url_link(url_id)
                return HttpResponse('Deleted')
            elif request.path_info.endswith('move-bookmark'):
                msg = dbxs.move_bookmarks(usr, request, url_id)
                return HttpResponse(msg)
            elif request.path_info.endswith('move-bookmark-multiple'):
                move_to_dir, move_links_list = dbxs.move_bookmarks(usr, request, single=False)
                return HttpResponse(msg)
            elif request.path_info.endswith('edit-bookmark'):
                msg = dbxs.edit_bookmarks(usr, request, url_id)
                return HttpResponse(msg)
            else:
                return HttpResponse('Wrong command')
        elif request.method == 'GET':
            if request.path_info.endswith('archieve'):
                return cread.get_archieved_file(url_id)
            elif request.path_info.endswith('read'):
                return cread.read_customized(url_id)
        else:
            return HttpResponse('Method not Permitted')
    else:
        return HttpResponse('What are you trying to accomplish!')


@login_required
def default_dest(request):
    return redirect('home')


@login_required
def navigate_directory(request, username, directory=None, tagname=None):
    usr = request.user
    base_dir = '/{}/{}'.format(usr, directory)
    usr_list = []
    if username and usr.username != username:
        return redirect('/'+usr.username)
    if directory or tagname:
        place_holder = 'Enter URL'
        if request.method == 'POST' and directory:
            form = AddURL(request.POST)
            if form.is_valid():
                dbxs.add_new_url(usr, request, directory)
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
        base_dir = '/{}/{}'.format(usr, directory)
        return render(
                    request, 'home_dir.html',
                    {
                        'usr_list': nlist, 'form':form,
                        'base_dir':base_dir, 'dirname':directory
                    }
                )
    else:
        return redirect('home')
    
    
@login_required
def api_points(request, username):
    usr = request.user
    default_dict = {'status':'none'}
    if username and usr.username != username:
        return redirect('/'+usr.username)
    if request.method == 'POST':
        req_list = request.POST.get('listdir', '')
        req_search = request.POST.get('search', '')
        req_archieve = request.POST.get('archieve', '')
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
        elif req_search and len(req_search) > 2:
            if req_search.startswith('tag:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'tag'
            elif req_search.startswith('url:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'url'
            elif req_search.startswith('dir:'):
                search_term = req_search.split(':', 1)[1]
                mode = 'dir'
            else:
                search_term = req_search
                mode = 'title'
            print(mode, search_term)
            usr_list = dbxs.get_rows_by_directory(usr, search_mode=mode, search=search_term)
            ndict = dbxs.populate_usr_list(usr, usr_list, create_dict=True)
            return HttpResponse(json.dumps(ndict))
        elif req_archieve and req_archieve in ['yes', 'force']:
            url_id = request.POST.get('url_id', '')
            dirname = request.POST.get('dirname', '')
            logger.debug('{}, {}'.format(url_id, dirname))
            if url_id and url_id.isnumeric() and dirname:
                qset = Library.objects.filter(id=url_id)
                if qset:
                    row = qset[0]
                    media_path = row.media_path
                    url_ar = '/{}/{}/{}/archieve'.format(usr.username, dirname, url_id)
                    dict_val = {'url': url_ar}
                    if media_path and os.path.exists(media_path) and req_archieve == 'yes':
                        dict_val.update({'status':'already archieved'})
                    else:
                        dbxs.process_add_url(usr, row.url, dirname, archieve_html=True, row=row)
                        dict_val.update({'status':'ok'})
                    return HttpResponse(json.dumps(dict_val))
                        
    return HttpResponse(json.dumps(default_dict))
    

import re
import os
import html
from .models import Library
from .dbaccess import DBAccess as dbxs
from datetime import datetime
from mimetypes import guess_type, guess_extension
from django.conf import settings
from vinanti import Vinanti

class ImportBookmarks:

    @classmethod
    def import_bookmarks(cls, usr, settings_row, import_file, mode='file'):
        book_dict = cls.convert_bookmark_to_dict(import_file, mode=mode)
        insert_links_list = []
        insert_dir_list = []
        for dirname in book_dict:
            if '/' in dirname or ':' in dirname:
                dirname = re.sub(r'/|:', '-', dirname)
            if dirname:
                qdir = Library.objects.filter(usr=usr, directory=dirname)
                if not qdir:
                    dirlist = Library(usr=usr, directory=dirname)
                    insert_dir_list.append(dirlist)
        if insert_dir_list:
            Library.objects.bulk_create(insert_dir_list)
            """
            for link in links:
                dbxs.process_add_url(usr, link, dirname,
                                     archieve_html=False, 
                                     settings_row=settings_row)
            """
        for dirname, links in book_dict.items():
            for val in links:
                url, icon_u, add_date, title, descr = val
                print(val)
                add_date = datetime.fromtimestamp(int(add_date))
                lib = Library(usr=usr, directory=dirname, url=url,
                              icon_url=icon_u,
                              title=title, summary=descr)
                insert_links_list.append(lib)
                
        if insert_links_list:
            Library.objects.bulk_create(insert_links_list)
            
        qlist = Library.objects.filter(usr=usr)
        row_list = []
        for row in qlist:
            icon_url = row.icon_url
            row_id = row.id
            url = row.url
            if url:
                row.media_path = cls.get_media_path(url, row_id)
            final_favicon_path = os.path.join(settings.FAVICONS_STATIC, str(row_id) + '.ico')
            row_list.append((row.icon_url, final_favicon_path))
            row.save()
        for iurl, dest in row_list:
            if iurl and iurl.startswith('http'):
                dbxs.vnt.get(iurl, out=dest)
        
    @staticmethod
    def get_media_path(url, row_id):
        content_type = guess_type(url)[0]
        if content_type and content_type == 'text/plain':
           ext = '.txt' 
        elif content_type:
            ext = guess_extension(content_type)
        else:
            ext = '.htm'
        out_dir = ext[1:].upper()
        out_title = str(row_id) + str(ext)
        media_dir = os.path.join(settings.ARCHIEVE_LOCATION, out_dir)
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
        
        media_path_parent = os.path.join(media_dir, str(row_id))
        if not os.path.exists(media_path_parent):
            os.makedirs(media_path_parent)
                
        media_path = os.path.join(media_path_parent, out_title)
        return media_path
        
    @staticmethod
    def convert_bookmark_to_dict(import_file, mode='file'):
        links_dict = {}
        if mode == 'file':
            content = ""
            with open(import_file, 'r', encoding='utf-8') as fd:
                content = fd.read()
        else:
            content = import_file
        if content:
            content = re.sub('ICON="(.*?)"', "", content)
            ncontent = re.sub('\n', " ", content)
            links_group = re.findall('<DT><H3(.*?)/DL>', ncontent)
            nsr = 0
            nlinks = []
            for i, j in enumerate(links_group):
                j = j + '<DT>'
                nlinks.clear()
                k = re.search('>(?P<dir>.*?)</H3>', j)
                dirname = k.group('dir')
                links = re.findall('A HREF="(?P<url>.*?)"(?P<extra>.*?)<DT>', j)
                for url, extra in links:
                    dt = re.search('ADD_DATE="(?P<add_date>.*?)"', extra)
                    add_date = dt.group('add_date')
                    dt = re.search('ICON_URI="(?P<icon>.*?)"', extra)
                    if dt:
                        icon_u = dt.group('icon')
                    else:
                        icon_u = ''
                    dt = re.search('>(?P<title>.*?)</A>', extra)
                    title = dt.group('title')
                    dt = re.search('<DD>(?P<descr>.*?)(<DT>)?', extra)
                    if dt:
                        descr = html.unescape(dt.group('descr'))
                    else:
                        descr = 'Not Available'
                    nlinks.append((url, icon_u, add_date, title, descr))
                if dirname in links_dict:
                    dirname = '{}-{}'.format(dirname, nsr)
                    nsr += 1
                links_dict.update({dirname:nlinks.copy()})
        return links_dict
    


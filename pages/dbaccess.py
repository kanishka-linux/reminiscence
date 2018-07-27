import os
import json
import shutil
import logging
from urllib.parse import urlparse
from mimetypes import guess_extension

from django.conf import settings
from vinanti import Vinanti
from bs4 import BeautifulSoup
from .models import Library, Tags, URLTags, UserSettings
from .summarize import Summarizer

import subprocess
from celery.decorators import task

logger = logging.getLogger(__name__)


class DBAccess:
    
    vnt = Vinanti(block=True, hdrs={'User-Agent':settings.USER_AGENT})
    
    @classmethod
    def add_new_url(cls, usr, request, directory, row):
        url_name = request.POST.get('add_url', '')
        if url_name:
            if url_name.startswith('ar:'):
                url_name = url_name[3:].strip()
                archieve_html = True
            else:
                archieve_html = False
            if row:
                settings_row = row[0]
            else:
                settings_row = None
            url_list = Library.objects.filter(usr=usr,
                                              directory=directory,
                                              url=url_name)
            if not url_list and url_name:
                cls.process_add_url(usr, url_name,
                                    directory, archieve_html, 
                                    settings_row=settings_row)
                                
    @classmethod
    def process_add_url(cls, usr, url_name, directory,
                        archieve_html, row=None,
                        settings_row=None):
        ext = None
        save = False
        save_text = False
        favicon_link = None
        summary = 'none'
        req = cls.vnt.get(url_name)
        tags_list = []
        if req and req.content_type:
            if ';' in req.content_type:
                content_type = req.content_type.split(';')[0].strip()
            else:
                content_type = req.content_type
            if content_type == 'text/plain':
                ext = '.txt'
            else:
                ext = guess_extension(content_type)
            print(content_type, '------', ext)
        if req and req.html and not req.binary:
            if 'text/html' in req.content_type:
                soup = BeautifulSoup(req.html, 'html.parser')
                title = soup.title.text
                ilink = soup.find('link', {'rel':'icon'})
                slink = soup.find('link', {'rel':'shortcut icon'})
                if ilink:
                    favicon_link = cls.format_link(ilink.get('href'), url_name)
                elif slink:
                    favicon_link = cls.format_link(slink.get('href'), url_name)
                else:
                    for link in soup.find_all('link'):
                        rel = link.get('href')
                        if (rel and (rel.endswith('.ico') or '.ico' in rel)):
                            favicon_link = cls.format_link(rel, url_name)
                        
                if archieve_html:
                    save_text = True
                if settings_row and (settings_row.autotag or settings_row.auto_summary):
                    summary, tags_list = Summarizer.get_summary_and_tags(req.html,
                                                                         settings_row.total_tags)
            else:
                title = url_name.rsplit('/')[-1]
                save_text = True
        elif req and req.binary:
            title = url_name.rsplit('/')[-1]
            save = True
        else:
            ext = '.bin'
            title = url_name.rsplit('/', 1)[-1]
        if row is None:
            row = Library.objects.create(usr=usr,
                                         directory=directory,
                                         url=url_name, title=title,
                                         summary=summary)
        else:
            print('row - exists')
        if ext and ext.startswith('.'):
            out_dir = ext[1:].upper()
        else:
            out_dir = str(ext).upper()
        if not ext:
            print(req.content_type)
        out_title = str(row.id) + str(ext)
        media_dir = os.path.join(settings.ARCHIEVE_LOCATION, out_dir)
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
        media_path_parent = os.path.join(media_dir, str(row.id))
        final_favicon_path = os.path.join(settings.FAVICONS_STATIC, str(row.id) + '.ico')
        media_path = os.path.join(media_path_parent, out_title)
        row.media_path = media_path
        row.save()
        if not os.path.exists(final_favicon_path) and favicon_link:
            cls.vnt.get(favicon_link, out=final_favicon_path)
        print(favicon_link, final_favicon_path)
        if save or save_text:
            if not os.path.exists(media_path_parent):
                os.makedirs(media_path_parent)
            if save:
                req.save(req.request_object, media_path)
            else:
                with open(media_path, 'w') as fd:
                    fd.write(req.html)
            if settings_row:
                cls.convert_html_pdf(media_path_parent, settings_row, row, url_name)
        if settings_row and tags_list:
            cls.edit_tags(usr, row.id, ','.join(tags_list), '')
        return row.id
    
    @classmethod
    def convert_html_pdf(cls, media_path_parent, settings_row, row, url_name):
        if settings_row.save_pdf:
            pdf = os.path.join(media_path_parent, str(row.id)+'.pdf')
            cmd = ['wkhtmltopdf', url_name, pdf]
            if settings.USE_CELERY:
                cls.convert_to_pdf_png.delay(cmd)
            else:
                subprocess.Popen(cmd)
        if settings_row.save_png:
            png = os.path.join(media_path_parent, str(row.id)+'.png')
            cmd = ['wkhtmltoimage', '--quality', '85', url_name, png]
            if settings.USE_CELERY:
                cls.convert_to_pdf_png.delay(cmd)
            else:
                subprocess.Popen(cmd)
        
    @task(name="convert-to-pdf-png")
    def convert_to_pdf_png(cmd):
        subprocess.call(cmd)
    
    @staticmethod
    def get_rows_by_directory(usr, directory=None, search=None, search_mode='title'):
        #usr_list = URLTags.objects.filter(url_id__usr=usr).select_related()
        
        usr_list = []
        
        if search and search_mode != 'dir':
            url_list = URLTags.objects.filter(usr_id=usr).select_related('url_id').order_by('url_id')
            url_id_list = [i.url_id.id for i in url_list]
            if search_mode == 'title':
                usr_list = Library.objects.filter(
                                usr=usr, title__icontains=search
                            ).exclude(id__in=url_id_list)
            elif search_mode == 'url':
                usr_list = Library.objects.filter(
                                usr=usr, url__icontains=search
                            ).exclude(id__in=url_id_list)
        else:
            if not directory and search and search_mode == 'dir':
                directory = search
            url_list = URLTags.objects.filter(usr_id=usr).select_related('url_id').order_by('url_id')
            url_id_list = [i.url_id.id for i in url_list]
            usr_list = Library.objects.filter(
                            usr=usr, directory=directory
                        ).exclude(id__in=url_id_list)
                        
        tag_no_list = [
                (
                    i.title, i.url, i.id, i.timestamp,
                    [], i.directory, i.media_path
                ) for i in usr_list if i.url
            ]
        udict = {}
        for i in url_list:
            url = i.url_id.url
            tagname = i.tag_id.tag
            dirname = i.url_id.directory
            title = i.url_id.title
            media_path = i.url_id.media_path
            update_udict = False
            if (search and ((search_mode == 'title' and search in title.lower())
                    or (search_mode == 'url' and search in url.lower())
                    or (search_mode == 'tag' and search == tagname))):
                update_udict = True
            if url in udict:
                udict[url][-3] = udict[url][-3] + [tagname]
            elif (directory and directory == dirname) or update_udict:
                udict.update(
                    {
                        url:[
                            title, url, i.url_id.id,
                            i.url_id.timestamp, [tagname],
                            dirname, media_path
                        ]
                    }
                )
        list_with_tag = [tuple(value) for key, value in udict.items()]
        usr_list = list_with_tag + tag_no_list
        
        return usr_list

    @staticmethod
    def get_rows_by_tag(usr, tagname):
        tagobj = Tags.objects.filter(tag=tagname)
        directory = 'tag'
        usr_list = []
        if tagobj:
            usr_list = URLTags.objects.select_related('url_id').filter(usr_id=usr,
                                                                       tag_id=tagobj[0])
            udict = {}
            tag_list = [tagname]
            for i in usr_list:
                uid = i.url_id.url
                dirname = i.url_id.directory
                udict.update(
                    {
                        uid:[
                            i.url_id.title, uid, i.url_id.id,
                            i.url_id.timestamp, [tagname],
                            dirname, i.url_id.media_path
                        ]
                    }
                )
            usr_list = [tuple(value) for key, value in udict.items()]
            return usr_list
        else:
            return None

    @staticmethod
    def populate_usr_list(usr, usr_list, create_dict=False):
        if create_dict:
            nlist = {}
        else:
            nlist = []
        index = 1
        username = usr.username
        for title, url, idd, timestamp, tag, directory, media_path in usr_list:
            base_dir = '/{}/{}/{}'.format(usr, directory, idd)
            base_remove = base_dir + '/remove'
            base_et = base_dir + '/edit-bookmark'
            move_single = base_dir + '/move-bookmark'
            move_multiple = base_dir + '/move-bookmark-multiple'
            base_eu = base_dir + '/edit-url'
            read_url = base_dir + '/read'
            if media_path and os.path.exists(media_path):
                archieve_media = base_dir + '/archieve'
            else:
                archieve_media = url
            netloc = urlparse(url).netloc
            if len(netloc) > 20:
                netloc = netloc[:20]+ '..'
            timestamp = timestamp.strftime("%d %b %Y")
            final_favicon_path = os.path.join(settings.FAVICONS_STATIC, str(idd) + '.ico')
            if os.path.exists(final_favicon_path):
                fav_path = settings.STATIC_URL + 'favicons/{}.ico'.format(idd)
            else:
                fav_path = ""
            if create_dict:
                nlist.update(
                        {
                            index:{
                                'title':title, 'netloc':netloc, 'url':url,
                                'edit-bookmark':base_et, 'remove-url':base_remove,
                                'timestamp': timestamp, 'tag':tag,
                                'move-bookmark':move_single, 
                                'move-multi': move_multiple, 'usr':username,
                                'archieve-media':archieve_media, 'directory':directory,
                                'read-url':read_url, 'id': idd, 'fav-path': fav_path
                            }
                        }
                    )
            else:
                nlist.append(
                    [
                        index, title, netloc, url, base_et, base_remove,
                        timestamp, tag, move_single, move_multiple,
                        archieve_media, directory, read_url, idd, fav_path
                    ]
                )
            index += 1
        return nlist
    
    @staticmethod
    def format_link(lnk, url):
        ourl = urlparse(url)
        ourld = ourl.scheme + '://' + ourl.netloc
        if lnk and lnk != '#':
            if lnk.startswith('//'):
                lnk = ourl.scheme + ':' + lnk
            elif lnk.startswith('/'):
                lnk = ourld + lnk
            elif lnk.startswith('./'): 
                lnk = ""
            elif lnk.startswith('../'):
                lnk = ""
            elif not lnk.startswith('http'):
                lnk = ourld + '/' + lnk
        return lnk
    
    @staticmethod
    def remove_url_link(url_id):
        qlist = Library.objects.filter(id=url_id)
        if qlist:
            row = qlist[0]
            media_path = row.media_path
            if media_path and os.path.exists(media_path):
                base_dir_url, file_name = os.path.split(media_path)
                base_dir_id, dir_id = os.path.split(base_dir_url)
                if dir_id.isnumeric():
                    ndir_id = int(dir_id)
                    if ndir_id == url_id:
                        shutil.rmtree(base_dir_url)
                        print('removing {}'.format(base_dir_url))
            qlist.delete()

    @staticmethod
    def move_bookmarks(usr, request, url_id=None, single=True):
        msg = 'Nothing Moved'
        if single and url_id:
            move_to_dir = request.POST.get('move_to_dir', '')
            print(url_id, request.POST)
            if move_to_dir:
                Library.objects.filter(id=url_id).update(directory=move_to_dir)
            msg = 'Moved to {}'.format(move_to_dir)
        elif not single:
            move_to_dir = request.POST.get('move_to_dir', '')
            move_links = request.POST.get('move_links', '')
            if move_links:
                move_links_list = [i.strip() for i in move_links.split(',') if i.strip()]
            else:
                move_links_list = []
            if move_to_dir and move_links_list:
                for link in move_links_list:
                    if link.isnumeric():
                        link_id = int(link)
                        Library.objects.filter(id=link_id).update(directory=move_to_dir)
            msg = 'Moved {} links to {}'.format(move_to_dir, len(move_links_list))
        return msg

    @staticmethod
    def edit_bookmarks(usr, request, url_id):
        title = request.POST.get('new_title', '')
        nurl = request.POST.get('new_url', '')
        tags = request.POST.get('new_tags', '')
        tags_old = request.POST.get('old_tags', '')
        print(url_id, request.POST)
        msg = 'Edited'
        if title and nurl:
            Library.objects.filter(id=url_id).update(title=title, url=nurl)
            msg = msg + ' Title and Link'
        elif title:
            Library.objects.filter(id=url_id).update(title=title)
            msg = msg + ' Title'
        elif nurl:
            Library.objects.filter(id=url_id).update(url=nurl)
            msg = msg + ' Link'
        if tags or tags_old:
            msg = DBAccess.edit_tags(usr, url_id, tags, tags_old) 
        return msg
        
    @staticmethod
    def edit_tags(usr, url_id, tags, tags_old):
        tags_list = [i.lower().strip() for i in tags.split(',')]
        tags_list_old = [i.lower().strip() for i in tags_old.split(',')]
        tags_list = [i for i in tags_list if i]
        tags_list_old = [i for i in tags_list_old if i]
        all_tags = Tags.objects.all()
        
        tags_new_add = set(tags_list) - set(tags_list_old)
        tags_old_delete = set(tags_list_old) - set(tags_list)
        insert_list = []
        for tag in tags_list:
            if not all_tags.filter(tag=tag).exists():
                insert_list.append(Tags(tag=tag))
            else:
                logger.info('Tag: {} exists'.format(tag))
        if insert_list:
            Tags.objects.bulk_create(insert_list)
            
        lib_list = Library.objects.filter(id=url_id)
        lib_obj = lib_list[0]
        tagins_list = []
        for tag in tags_new_add:
            tag_obj = Tags.objects.filter(tag=tag)
            tagid = URLTags.objects.filter(usr_id=usr,
                                           url_id=lib_obj,
                                           tag_id=tag_obj[0])
            if not tagid:
                row = tagins_list.append(
                        URLTags(
                            usr_id=usr,
                            url_id=lib_obj,
                            tag_id=tag_obj[0]
                        )
                )
        if tagins_list:
            URLTags.objects.bulk_create(tagins_list)
            
        for tag in tags_old_delete:
            tag_obj = Tags.objects.filter(tag=tag)
            tagid = URLTags.objects.filter(usr_id=usr,
                                           url_id=lib_obj,
                                           tag_id=tag_obj[0])
            if tagid:
                URLTags.objects.filter(usr_id=usr,
                                       url_id=lib_obj,
                                       tag_id=tag_obj[0]).delete()
        msg = ('Edited Tags: new-tags-addition={}::old-tags-delete={}'
               .format(tags_new_add, tags_old_delete))
        return msg

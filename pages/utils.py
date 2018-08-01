import re
from .models import Library
from .dbaccess import DBAccess as dbxs


class ImportBookmarks:

    @classmethod
    def import_bookmarks(cls, usr, settings_row, import_file, mode='file'):
        book_dict = cls.convert_bookmark_to_dict(import_file, mode=mode)
        for dirname, links in book_dict.items():
            if '/' in dirname or ':' in dirname:
                dirname = re.sub(r'/|:', '-', dirname)
            if dirname:
                qdir = Library.objects.filter(usr=usr, directory=dirname)
                if not qdir:
                    Library.objects.create(usr=usr, directory=dirname).save()
            for link in links:
                dbxs.process_add_url(usr, link, dirname,
                                     archieve_html=False, 
                                     settings_row=settings_row)
        
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
            content = re.sub('ICON(_URI)?="[^"]*"', "", content)
            ncontent = re.sub('\n', " ", content)
            links_group = re.findall('<DT><H3(.*?)/DL>', ncontent)
            nsr = 0
            for i, j in enumerate(links_group):
                nlinks = []
                k = re.search(r'>(?P<title>.*?)</H3>', j)
                title = k.group('title')
                links = re.findall('A HREF="(.*?)"', j)
                for sr, href in enumerate(links):
                    if href.startswith('http'):
                        nlinks.append(href)
                if title in links_dict:
                    title = '{}-{}'.format(title, nsr)
                    nsr += 1
                links_dict.update({title:nlinks.copy()})
        return links_dict
    


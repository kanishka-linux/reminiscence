import os
import re
import logging
from urllib.parse import urlparse
from mimetypes import guess_type

from django.http import HttpResponse
from django.conf import settings
from vinanti import Vinanti
from bs4 import BeautifulSoup
from readability import Document
from .models import Library
from .dbaccess import DBAccess as dbxs

logger = logging.getLogger(__name__)


class CustomRead:
    
    readable_format = [
        'text/plain', 'text/html', 'text/htm',
        'text/css', 'application/xhtml+xml',
        'application/xml', 'application/json',
    ]
    mtype_list = [
        'text/htm', 'text/html', 'text/plain'
    ]
    vnt = Vinanti(block=True, hdrs={'User-Agent':settings.USER_AGENT})
    fav_path = settings.FAVICONS_STATIC
    
    @classmethod
    def get_archieved_file(cls, url_id, mode='html'):
        qset = Library.objects.filter(id=url_id)
        if qset:
            row = qset[0]
            media_path = row.media_path
            if mode in ['pdf', 'png'] and media_path:
                fln, ext = media_path.rsplit('.', 1)
                if mode == 'pdf':
                    media_path = fln + '.pdf'
                elif mode == 'png':
                    media_path = fln + '.png'
            if media_path and os.path.exists(media_path):
                mtype = guess_type(media_path)[0]
                if not mtype:
                    mtype = 'application/octet-stream'
                ext = media_path.rsplit('.')[-1]
                if ext:
                    filename = row.title + '.' + ext
                    if '.' in row.title:
                        file_ext = row.title.rsplit('.', 1)[-1]
                        if ext == file_ext:
                            filename = row.title
                else:
                    filename = row.title + '.bin'
                if mtype in ['text/html', 'text/htm']:
                    data = cls.format_html(row, media_path)
                else:
                    with open(media_path, 'rb') as fd:
                        data = fd.read()
                response = HttpResponse()
                response['mimetype'] = mtype
                response['content-type'] = mtype
                filename = filename.replace(' ', '.')
                print(filename, mtype)
                if not cls.is_human_readable(mtype):
                    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
                response.write(data)
                return response
            else:
                return HttpResponse('<html>File has not been archieved in this format</html>')
        else:
            return HttpResponse('<html>No url exists for this query</html>')
    
    @classmethod
    def read_customized(cls, url_id):
        qlist = Library.objects.filter(id=url_id).select_related()
        data = b"<html>Not Available</html>"
        mtype = 'text/html'
        if qlist:
            row = qlist[0]
            media_path = row.media_path
            if media_path and os.path.exists(media_path):
                mtype = guess_type(media_path)[0]
                
                if mtype in cls.mtype_list:
                    data = cls.format_html(row, media_path,
                                           custom_html=True)
                    if mtype == 'text/plain':
                        mtype = 'text/html'
            elif row.url:
                data = cls.get_content(row, url_id, media_path)
        response = HttpResponse()
        response['mimetype'] = mtype
        response['content-type'] = mtype
        response.write(data)
        return response
    
    @classmethod
    def get_content(cls, row, url_id, media_path):
        data = ""
        req = cls.vnt.get(row.url)
        if req and req.content_type and req.html:
            mtype = req.content_type.split(';')[0].strip()
            if mtype in cls.mtype_list:
                content = req.html
                data = cls.format_html(
                    row, media_path, content=content,
                    custom_html=True
                )
                fav_nam = str(url_id) + '.ico'
                final_favicon_path = os.path.join(cls.fav_path, fav_nam)
                if not os.path.exists(final_favicon_path):
                    cls.get_favicon_link(req.html, row.url,
                                         final_favicon_path)
        return data
                    
    @classmethod
    def format_html(cls, row, media_path, content=None, custom_html=False):
        if not content:
            content = ""
            with open(media_path, encoding='utf-8', mode='r') as fd:
                content = fd.read()
        soup = BeautifulSoup(content, 'lxml')
        for script in soup.find_all('script'):
            script.decompose()
        ourl = urlparse(row.url)
        ourld = ourl.scheme + '://' + ourl.netloc
        link_list = soup.find_all(['a', 'link', 'img'])
        for link in link_list:
            if link.name == 'img':
                lnk = link.get('src', '')
            else:
                lnk = link.get('href', '')
            if lnk and lnk != '#':
                if lnk.startswith('//'):
                    if link.name == 'img':
                        link['src'] = ourl.scheme + ':' + lnk
                    else:
                        link['href'] = ourl.scheme + ':' + lnk
                elif lnk.startswith('/'):
                    if link.name == 'img':
                        link['src'] = ourld + lnk
                    else:
                        link['href'] = ourld + lnk
                elif lnk.startswith('./'): 
                    pass
                elif lnk.startswith('../'):
                    pass
                elif not lnk.startswith('http'):
                    if link.name == 'img':
                        link['src'] = ourld + '/' + lnk
                    else:
                        link['href'] = ourld + '/' + lnk
        if custom_html:
            ndata = soup.prettify()
            if soup.title:
                title = soup.title.text
            else:
                title = row.url.rsplit('/')[-1]
            data = Document(ndata)
            data_sum = data.summary()
            if data_sum:
                nsoup = BeautifulSoup(data_sum, 'lxml')
                if nsoup.text.strip():
                    data = cls.custom_template(title, nsoup.prettify(), row)
                else:
                    data = cls.custom_soup(ndata, title, row)
            else:
                data = cls.custom_soup(ndata, title, row)
        else:
            data = soup.prettify()
        return bytes(data, 'utf-8')
        
    @staticmethod
    def custom_template(title, content, row):
        if row:
            base_dir = '/{}/{}/{}'.format(row.usr.username, row.directory, row.id)
            read_url = base_dir + '/read'
            read_pdf = base_dir + '/read-pdf'
            read_png = base_dir + '/read-png'
            read_html = base_dir + '/read-html'
        else:
            read_url = read_pdf = read_png = read_html = '#'
            
        template = """
        <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta name="referrer" content="no-referrer">
            </head>
        <body>
            <div class="container-fluid">
                <div class="row">
                    <div class="col-sm"></div>
                    <div class="col-sm">
                        <div class='card text-left bg-light mb-3'>
                            <div class='card-header'>
                                <ul class="nav nav-tabs card-header-tabs">
                                    <li class="nav-item">
                                        <a class="nav-link active" href="{read_url}">HTML</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="{read_html}">Original</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="{read_pdf}">PDF</a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="{read_png}">PNG</a>
                                    </li>
                                </ul>
                            </div>
                            <div class='card-body'>
                                <h5 class="card-title">{title}</h5>
                                {content}
                            </div>
                        </div>
                    </div>
                    <div class="col-sm"></div>
                </div>
            </div>
        </body>
        </html>
        """.format(title=title, content=content,
                   read_url=read_url, read_pdf=read_pdf,
                   read_png=read_png, read_html=read_html)
        return template

    @classmethod
    def custom_soup(cls, data, title, row=None):
        soup = BeautifulSoup(data, 'lxml')
        text_result = soup.find_all(text=True)
        final_result = []
        for elm in text_result:
            ntag = ''
            ptag = elm.parent.name
            if ptag == 'a':
                href = elm.parent.get('href')
                ntag = '<a href="{}">{}</a>'.format(href, elm)
            elif ptag in ['body', 'html', '[document]', 'img']:
                pass
            elif ptag == 'p':
                ntag = '<p class="card-text">{}</p>'.format(elm)
            elif ptag == 'span':
                ntag = '<span class="card-text">{}</span>'.format(elm)
            elif '\n' in elm:
                ntag = '</br>';
            else:
                tag = elm.parent.name
                ntag = '<{tag}>{text}</{tag}>'.format(tag=tag, text=elm)
            if ntag:
                final_result.append(ntag)
        result = ''.join(final_result)
        result = re.sub(r'(</br>)+', '', result)
        content = cls.custom_template(title, result, row)
        return content
    
    @classmethod
    def get_favicon_link(cls, data, url_name, final_favicon_path):
        soup = BeautifulSoup(data, 'lxml')
        favicon_link = ''
        if not os.path.exists(final_favicon_path):
            links = soup.find_all('link')
            ilink = soup.find('link', {'rel':'icon'})
            slink = soup.find('link', {'rel':'shortcut icon'})
            if ilink:
                favicon_link = dbxs.format_link(ilink.get('href'), url_name)
            elif slink:
                favicon_link = dbxs.format_link(slink.get('href'), url_name)
            else:
                for i in links:
                    rel = i.get('href')
                    if (rel and (rel.endswith('.ico') or '.ico' in rel)):
                        favicon_link = dbxs.format_link(rel, url_name)
            if favicon_link:
                cls.vnt.get(favicon_link, out=final_favicon_path)
    
    @classmethod
    def is_human_readable(cls, mtype):
        human_readable = False
        if mtype in cls.readable_format:
            human_readable = True
        return human_readable

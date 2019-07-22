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
import logging
import hashlib
import time
import uuid
import pickle
import subprocess
from zipfile import ZipFile
from urllib.parse import urlparse, quote
from mimetypes import guess_type
from collections import OrderedDict

from django.http import HttpResponse, FileResponse, StreamingHttpResponse
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils.text import slugify
from vinanti import Vinanti
from bs4 import BeautifulSoup
from readability import Document
from .models import Library, UserSettings
from .dbaccess import DBAccess as dbxs
from .utils import RangeFileResponse

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
    vnt_noblock = Vinanti(block=False, hdrs={'User-Agent':settings.USER_AGENT},
                  backend=settings.VINANTI_BACKEND,
                  max_requests=settings.VINANTI_MAX_REQUESTS)
    vnt = Vinanti(block=True, hdrs={'User-Agent':settings.USER_AGENT})
    fav_path = settings.FAVICONS_STATIC
    VIDEO_ID_DICT = OrderedDict()
    CACHE_FILE = os.path.join(settings.TMP_LOCATION, 'cache')
    ANNOTATION_SCRIPT = """
                var pageUri = function () {
            return {
            beforeAnnotationCreated: function (ann) {
                ann.uri = window.location.href;
            }
            };
            };
            
                var app = new annotator.App();
                var loc = '/annotate'
                var csrftoken = getCookie('csrftoken');
                app.include(annotator.ui.main, {element: document.body});
                app.include(annotator.storage.http, {prefix: loc, headers: {"X-CSRFToken": csrftoken} });
                app.include(pageUri);
                app.start().then(function () {
                app.annotations.load({uri: window.location.pathname});
                });

            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            };
    """
    
    @classmethod
    def get_archived_file(cls, usr, url_id, mode='html', req=None, return_path=False):
        qset = Library.objects.filter(usr=usr, id=url_id)
        streaming_mode = False
        if not os.path.exists(settings.TMP_LOCATION):
            os.makedirs(settings.TMP_LOCATION)
        if qset:
            row = qset[0]
            media_path = row.media_path
            if mode in ['pdf', 'png', 'html'] and media_path:
                fln, ext = media_path.rsplit('.', 1)
                if mode == 'pdf':
                    media_path = fln + '.pdf'
                elif mode == 'png':
                    media_path = fln + '.png'
                elif mode == 'html':
                    media_path = fln + '.htm'
            elif mode == 'archive' and media_path:
                mdir, _ = os.path.split(media_path)
                filelist = os.listdir(mdir)
                mlist = []
                extset = set(['pdf', 'png', 'htm', 'html', 'json'])
                for fl in filelist:
                    ext = fl.rsplit('.', 1)
                    if ext and ext[-1] not in extset and not fl.startswith("."):
                        mlist.append(os.path.join(mdir, fl))
                for mfile in mlist:
                    if os.path.isfile(mfile) and os.stat(mfile).st_size:
                        media_path = mfile
                        streaming_mode = True
                        break
                if streaming_mode and req:
                    qlist = UserSettings.objects.filter(usrid=usr)
                    if qlist and not qlist[0].media_streaming:
                        streaming_mode = False
                        
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
                    return HttpResponse(data)
                elif streaming_mode:
                    if os.path.isfile(cls.CACHE_FILE):
                        with open(cls.CACHE_FILE, 'rb') as fd:
                            cls.VIDEO_ID_DICT = pickle.load(fd)
                    uid = str(uuid.uuid4())
                    uid = uid.replace('-', '')
                    while uid in cls.VIDEO_ID_DICT:
                        logger.debug("no unique ID, Generating again")
                        uid = str(uuid.uuid4())
                        uid = uid.replace('-', '')
                        time.sleep(0.01)
                    cls.VIDEO_ID_DICT.update({uid:[media_path, time.time()]})
                    cls.VIDEO_ID_DICT.move_to_end(uid, last=False)
                    if len(cls.VIDEO_ID_DICT) > settings.VIDEO_PUBLIC_LIST:
                        cls.VIDEO_ID_DICT.popitem()
                    with open(cls.CACHE_FILE, 'wb') as fd:
                        pickle.dump(cls.VIDEO_ID_DICT, fd)
                    if return_path:
                        title_slug = slugify(row.title, allow_unicode=True)
                        if settings.ROOT_URL_LOCATION:
                            root_loc = settings.ROOT_URL_LOCATION
                            if root_loc.startswith('/'):
                                root_loc = root_loc[1:]
                            return '{}/{}/getarchivedvideo/{}-{}'.format(root_loc, usr.username, title_slug, uid)
                        else:
                            return '{}/getarchivedvideo/{}-{}'.format(usr.username, title_slug, uid)
                    else:
                        return cls.get_archived_video(req, usr.username, uid)
                else:
                    response = FileResponse(open(media_path, 'rb'))
                    mtype = 'video/webm' if mtype == 'video/x-matroska' else mtype
                    response['mimetype'] = mtype
                    response['content-type'] = mtype
                    response['content-length'] = os.stat(media_path).st_size
                    filename = filename.replace(' ', '.')
                    logger.info('{} , {}'.format(filename, mtype))
                    if not cls.is_human_readable(mtype) and not streaming_mode:
                        response['Content-Disposition'] = 'attachment; filename="{}"'.format(quote(filename))
                    return response
            else:
                back_path = req.path_info.rsplit('/', 1)[0] + '/read'
                return render(req, 'archive_not_found.html', {'path':back_path})
        else:
            return HttpResponse(status=404)
    
    @classmethod
    def get_archived_video(cls, request, username, video_id):
        if video_id in cls.VIDEO_ID_DICT:
            media_path, ltime = cls.VIDEO_ID_DICT.get(video_id)
            logger.debug('{} {}'.format(media_path, ltime))
            if time.time() - ltime <= settings.VIDEO_ID_EXPIRY_LIMIT*3600:
                if os.path.isfile(media_path):
                    mtype = guess_type(media_path)[0]
                    if not mtype:
                        mtype = 'application/octet-stream'
                    range_header = request.META.get('HTTP_RANGE', '').strip()
                    range_match = settings.RANGE_REGEX.match(range_header)
                    size = os.stat(media_path).st_size
                    if range_match:
                        first_byte, last_byte = range_match.groups()
                        first_byte = int(first_byte) if first_byte else 0
                        last_byte = int(last_byte) if last_byte else size - 1
                        if last_byte >= size:
                            last_byte = size - 1
                        length = last_byte - first_byte + 1
                        response = StreamingHttpResponse(
                            RangeFileResponse(open(media_path, 'rb'), offset=first_byte,
                            length=length), status=206, content_type=mtype
                        )
                        response['Content-Length'] = str(length)
                        response['Content-Range'] = 'bytes {}-{}/{}'.format(first_byte, last_byte, size)
                    else:
                        response = StreamingHttpResponse(FileResponse(open(media_path, 'rb')))
                        response['content-length'] = size
                    mtype = 'video/webm' if mtype == 'video/x-matroska' else mtype
                    response['content-type'] = mtype
                    response['mimetype'] = mtype
                    response['Accept-Ranges'] = 'bytes'
                    return response
        return HttpResponse(status=404)
    
    @classmethod
    def generate_archive_media_playlist(cls, server, usr, directory):
        qset = Library.objects.filter(usr=usr, directory=directory)
        pls_txt = '#EXTM3U\n'
        extset = set(['pdf', 'png', 'htm', 'html'])
        if not os.path.exists(settings.TMP_LOCATION):
            os.makedirs(settings.TMP_LOCATION)
        if os.path.isfile(cls.CACHE_FILE):
            with open(cls.CACHE_FILE, 'rb') as fd:
                cls.VIDEO_ID_DICT = pickle.load(fd)
        for row in qset:
            streaming_mode = False
            media_path = row.media_path
            media_element = row.media_element
            title = row.title
            if media_path and media_element:
                mdir, _ = os.path.split(media_path)
                filelist = os.listdir(mdir)
                mlist = []
                for fl in filelist:
                    ext = fl.rsplit('.', 1)
                    if ext and ext[-1] not in extset:
                        mlist.append(os.path.join(mdir, fl))
                for mfile in mlist:
                    if os.path.isfile(mfile) and os.stat(mfile).st_size:
                        media_path = mfile
                        streaming_mode = True
                        break
            if media_path and os.path.exists(media_path):
                mtype = guess_type(media_path)[0]
                if not mtype:
                    mtype = 'application/octet-stream'
                if streaming_mode:
                    uid = str(uuid.uuid4())
                    uid = uid.replace('-', '')
                    while uid in cls.VIDEO_ID_DICT:
                        logger.debug("no unique ID, Generating again")
                        uid = str(uuid.uuid4())
                        uid = uid.replace('-', '')
                        time.sleep(0.01)
                    cls.VIDEO_ID_DICT.update({uid:[media_path, time.time()]})
                    cls.VIDEO_ID_DICT.move_to_end(uid, last=False)
                    if len(cls.VIDEO_ID_DICT) > settings.VIDEO_PUBLIC_LIST:
                        cls.VIDEO_ID_DICT.popitem()
                    title_slug = slugify(title, allow_unicode=True)
                    if settings.ROOT_URL_LOCATION:
                        root_loc = settings.ROOT_URL_LOCATION
                        if root_loc.startswith('/'):
                            root_loc = root_loc[1:]
                        return_path = '{}/{}/{}/getarchivedvideo/{}-{}'.format(server, root_loc,
                                                                               usr.username,
                                                                               title_slug, uid)
                    else:
                        return_path = '{}/{}/getarchivedvideo/{}-{}'.format(server, usr.username, title_slug, uid)
                    pls_txt = pls_txt+'#EXTINF:0, {0}\n{1}\n'.format(title, return_path)
        with open(cls.CACHE_FILE, 'wb') as fd:
            pickle.dump(cls.VIDEO_ID_DICT, fd)
        uid = str(uuid.uuid4())
        uid = uid.replace('-', '')
        plfile = os.path.join(settings.TMP_LOCATION, uid)
        if not os.path.isfile(plfile):
            with open(plfile, 'wb') as fd:
                pickle.dump(pls_txt, fd)
        pls_path = '{}/{}/getarchivedplaylist/{}/playlist/{}'.format(settings.ROOT_URL_LOCATION, 
                                                            usr.username, directory, uid)
        logger.debug(pls_path)
        return pls_path

    @classmethod
    def read_epub(cls, usr, url_id, mode, req, rel_path):
        qlist = Library.objects.filter(usr=usr, id=url_id).select_related()
        data = b"<html>Not Available</html>"
        mtype = 'text/html'
        if qlist:
            row = qlist[0]
            media_path = row.media_path
            media_dir, media_file_with_ext = os.path.split(media_path)
            media_file_without_ext = media_file_with_ext.rsplit('.', 1)[0]
            media_epub = "{}/EPUBDIR/{}".format(media_dir, rel_path)
            if os.path.exists(media_epub):
                mtype = guess_type(media_epub)[0]
                if mtype in cls.mtype_list:
                    content = open(media_epub, "r").read()
                    data = bytes(content, "utf-8")
                    response = HttpResponse()
                    response['mimetype'] = mtype
                    response['content-type'] = mtype
                    response.write(data)
                else:
                    response = FileResponse(open(media_epub, 'rb'))
                    response['content-type'] = mtype
                    response['content-length'] = os.stat(media_epub).st_size
            else:
                response = HttpResponse("Something is wrong with the EPUB")
        return response

    @staticmethod
    def read_content(media_html):
        content = bytes("Empty", "utf-8")
        try:
            with open(media_html, encoding='utf-8', mode='r') as fd:
                content = fd.read()
        except Exception as err:
            logger.error(err)
            try:
                with open(media_html, encoding='ISO-8859-1', mode='r') as fd:
                    content = fd.read()
            except Exception as err:
                logger.error(err)
                with open(media_html, encoding='utf-8', mode='r', errors='ignore') as fd:
                    content = fd.read()
        return content
        
    @classmethod
    def read_customized(cls, usr, url_id, mode='read', req=None):
        qlist = Library.objects.filter(usr=usr, id=url_id).select_related()
        data = b"<html>Not Available</html>"
        mtype = 'text/html'
        if qlist:
            row = qlist[0]
            media_path = row.media_path
            if mode in ['read-default', 'read-dark', 'read-light', 'read-gray']:
                if mode == 'read-dark':
                    row.reader_mode = UserSettings.DARK
                elif mode == 'read-light':
                    row.reader_mode = UserSettings.LIGHT
                elif mode == 'read-gray':
                    row.reader_mode = UserSettings.GRAY
                else:
                    row.reader_mode = UserSettings.WHITE
                row.save()
            if media_path and os.path.exists(media_path):
                mtype = guess_type(media_path)[0]
                if mtype in cls.mtype_list or media_path.endswith(".bin") or media_path.endswith(".note"):
                    if media_path.endswith(".bin"):
                        html = media_path.rsplit(".", 1)[0] + ".htm"
                        if os.path.exists(html):
                            media_path = html
                            mtype = "text/html"
                    data = cls.format_html(row, media_path,
                                           custom_html=True)
                    if mtype == 'text/plain' or media_path.endswith(".bin") or media_path.endswith(".note"):
                        mtype = 'text/html'
                elif media_path.endswith(".pdf"):
                    media_dir, media_file_with_ext = os.path.split(media_path)
                    media_file_without_ext = media_file_with_ext.rsplit('.', 1)[0]
                    media_html = "{}/{}.html".format(media_dir, media_file_without_ext)
                    if not os.path.exists(media_html):
                        if hasattr(settings, "PDF_TO_HTML_CONVERTER"):
                            converter = settings.PDF_TO_HTML_CONVERTER
                        else:
                            converter = "pdftohtml"
                        if converter == "pdf2htmlEX":
                            cmd = ["pdf2htmlEX", "--dest-dir", media_dir, "--zoom", "1.5", media_path]
                        elif converter == "pdftohtml":
                            cmd = ["pdftohtml", "-p", "-c", "-noframes", "-zoom", "1.5", media_path, media_html]
                        if os.name == "posix":
                            subprocess.Popen(cmd)
                        else:
                            subprocess.Popen(cmd, shell=True)
                        mtype = "text/html"
                        data = bytes("<html>Wait for few seconds, pdf is being processed. Refresh page after 5-10 seconds</html>", "utf-8")
                    else:
                        mtype = "text/html"
                        content = cls.read_content(media_html)
                        src = '<script src="/static/js/jquery-3.3.1.min.js"></script></body>'
                        content = re.sub("&#160;|[ ]+", " ", content)
                        content = re.sub("</body>|</BODY>", src, content)
                        src = '<script src="/static/js/annotator.min.js"></script></body>'
                        content = re.sub("</body>", src, content)
                        src = '<script>{}</script></body>'.format(cls.ANNOTATION_SCRIPT)
                        content = re.sub("</body>", src, content)
                        data = bytes(content, "utf-8")
                elif media_path.endswith(".epub"):
                    media_dir, media_file_with_ext = os.path.split(media_path)
                    media_file_without_ext = media_file_with_ext.rsplit('.', 1)[0]
                    media_epub = "{}/EPUBDIR".format(media_dir)
                    epub_loc = os.path.join(media_dir, "epub_loc.txt")
                    epub_cfi = ""
                    if os.path.exists(epub_loc):
                        epub_cfi = open(epub_loc, "r").read()
                    if not os.path.exists(media_epub):
                        with ZipFile(media_path, "r") as zp:
                            zp.extractall(media_epub)
                    back_url = req.path_info.rsplit("/", 2)[0]
                    mtype = "text/html"
                    data = bytes("hello world", "utf-8")
                    row_url = req.path_info.rsplit('/', 1)[0] + '/archive'
                    html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                      <meta charset="utf-8">
                      <meta name="viewport" content="width=device-width, initial-scale=1">
                      <script src="/static/js/epub.min.js"></script>
                      <script src="/static/js/jquery-3.3.1.min.js"></script>
                      <link rel="stylesheet" href="/static/css/bootstrap.min.css">
                    </head>
                    <body>
                      <div class="container">
                          <div class="row">
                            <select id="toc" class="browser-default custom-select col-sm-4"></select>
                          </div>
                      </div>
                      <div id="viewer" class="spreads"></div>
                      <div class="container">
                          <div class="row">
                            <button id="next" class="col-sm-1 btn btn-sm">Next</button>
                            <button id="pages" class="col-sm-1 btn btn-sm"></button>
                            <button id="prev" class="col-sm-1 btn btn-sm">Prev</button>
                            <a href="{back_url}" id="backlink" class="btn btn-info btn-sm col-sm-1" role="button">Back</a>
                            
                          </div>
                      </div>
                      <script>
                        var book = ePub("{row_url}");
                        var rendition = book.renderTo("viewer", {{
                          width: "100%",
                          height: "100%",
                          method: "default",
                          flow: "paginated"
                        }});
                        var epub_cfi = "{epub_cfi}";
                        if (epub_cfi == ""){{
                            var displayed = rendition.display().then(function(){{
                                window.location.href = generateURL(rendition);
                                }});
                        }}else {{
                            var displayed = rendition.display(epub_cfi).then(function(){{
                                window.location.href = generateURL(rendition);
                            }});
                        }}
                            var next = document.getElementById("next");
                            next.addEventListener("click", function(){{
                              navigate("next");
                            }}, false);
                            var prev = document.getElementById("prev");
                            var toc_elem = document.getElementById("toc");
                            var bak_link = document.getElementById("backlink");
                            prev.addEventListener("click", function(){{
                              navigate("prev");
                            }}, false);
                            var keyListener = function(e){{
                              // Left Key
                              if ((e.keyCode || e.which) == 37) {{
                                navigate("prev");
                              }}
                              // Right Key
                              if ((e.keyCode || e.which) == 39) {{
                                navigate("next");
                              }}
                            }};
                            rendition.on("keyup", keyListener);
                            document.addEventListener("keyup", keyListener, false);

                            function navigate(val){{
                                if(val == "prev"){{
                                    rendition.prev().then(function(){{
                                    let x = rendition.currentLocation()
                                    hd = window.location.href.split("#")[0];
                                    cfi = x.start.href;
                                    elem = document.getElementById("pages");
                                    elem.innerHTML = x.start.displayed.page + "/" + x.start.displayed.total;
                                    window.location.href = hd + "#" + cfi;
                                    document.documentElement.scrollTop = 0;
                                    bak_link.href = bak_link.href.split("/epub-bookmark/")[0];
                                    bak_link.href = bak_link.href + "/epub-bookmark/{url_id}" + "/" + x.start.cfi; 
                                    }});
                                }}else if(val == "next"){{
                                    rendition.next().then(function(){{;
                                    let x = rendition.currentLocation();
                                    cfi = x.start.href;
                                    hd = window.location.href.split("#")[0];
                                    elem = document.getElementById("pages");
                                    elem.innerHTML = x.start.displayed.page + "/" + x.start.displayed.total;
                                    window.location.href = hd + "#" + cfi;
                                    document.documentElement.scrollTop = 0;
                                    selectIndex(cfi);
                                    bak_link.href = bak_link.href.split("/epub-bookmark/")[0];
                                    bak_link.href = bak_link.href + "/epub-bookmark/{url_id}" + "/" + x.start.cfi; 
                                    }})
                                }};
                            }};

                            function generateURL(rendition){{
                                let x = rendition.currentLocation()
                                hd = window.location.href.split("#")[0];
                                cfi = x.start.href;
                                url = hd + "#" + cfi;
                                return url;
                            }}

                            function selectIndex(cfi){{
                                index = toc_elem.selectedIndex;
                                if (index != undefined){{
                                    let url = toc_elem.options[index].ref.split("#")[0];
                                    if(url != cfi){{
                                        let elems  = toc_elem.options;
                                        for(var i=0; i<elems.length; i++){{
                                            let u = elems[i].ref.split("#")[0];
                                            if(cfi == u){{
                                                toc_elem.selectedIndex = i;
                                                break;
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                            
                            book.loaded.navigation.then(function(toc){{
                                console.log(toc);
                                var $select = document.getElementById("toc"),
                                        docfrag = document.createDocumentFragment();
                                toc.forEach(function(chapter) {{
                                    console.log(chapter);
                                    var option = document.createElement("option");
                                    option.textContent = chapter.label;
                                    option.ref = chapter.href;
                                    docfrag.appendChild(option);
                                }});
                                $select.appendChild(docfrag);
                                $select.onchange = function(){{
                                        var index = $select.selectedIndex,
                                        url = $select.options[index].ref;
                                        rendition.display(url);
                                        return false;
                                }};
                            }});
                            
                            
                            rendition.hooks.content.register(function (view) {{
                                      var adder = [
                                        ['.annotator-adder, .annotator-outer', ['position', 'fixed']]
                                        ];
                                          view.addScript("/static/js/annotator.min.js").
                                            then(function (){{
                                                        var pageUri = function () {{
                                                return {{
                                                beforeAnnotationCreated: function (ann) {{
                                                    //ann.uri = window.location.href;
                                                    z = window.location.href.split("#");
                                                    final_url = window.location.pathname;
                                                    
                                                    if (z.length == 2){{
                                                        final_url = final_url + "#" + z[1];
                                                        }}
                                                    ann.uri = final_url;
                                                }}
                                                }};
                                                }};
                                                
                                                    var app = new view.window.annotator.App();
                                                    var loc = '/annotate'
                                                    var csrftoken = getCookie('csrftoken');
                                                    app.include(view.window.annotator.ui.main, {{element: view.document.body}});
                                                    app.include(view.window.annotator.storage.http, {{prefix: loc, headers: {{"X-CSRFToken": csrftoken}} }});
                                                    app.include(pageUri);
                                                    app.start().then(function () {{
                                                    z = window.location.href.split("#");
                                                    final_url = window.location.pathname;
                                                    
                                                    if (z.length == 2){{
                                                        final_url = final_url + "#" + z[1];
                                                        }}
                                                    app.annotations.load({{uri: final_url}});
                                                    }});

                                                function getCookie(name) {{
                                                    var cookieValue = null;
                                                    if (document.cookie && document.cookie !== '') {{
                                                        var cookies = document.cookie.split(';');
                                                        for (var i = 0; i < cookies.length; i++) {{
                                                            var cookie = jQuery.trim(cookies[i]);
                                                            // Does this cookie string begin with the name we want?
                                                            if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                                                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                                                break;
                                                            }}
                                                        }}
                                                    }}
                                                    return cookieValue;
                                                }};

                                                          
                                            }})
                            }})
                            
                      </script>
                    </body>
                    </html>""".format(back_url=back_url, row_url=row_url, url_id=url_id, epub_cfi=epub_cfi)
                    data = bytes(html, "utf-8")
            elif row.url:
                data = cls.get_content(row, url_id, media_path)
        response = HttpResponse()
        response['mimetype'] = mtype
        response['content-type'] = mtype
        response.write(data)
        return response

    @classmethod
    def read_customized_note(cls, usr, url_id, mode='read-note', req=None):
        qlist = Library.objects.filter(usr=usr, id=url_id).select_related()
        data = b"<html>Not Available</html>"
        mtype = 'text/html'
        if qlist:
            row = qlist[0]
            media_path = row.media_path
            if media_path and os.path.exists(media_path):
                data = cls.format_note(row, media_path)
                mtype = 'text/html'
        response = HttpResponse()
        response['mimetype'] = mtype
        response['content-type'] = mtype
        response.write(data)
        return response

    @classmethod
    def save_customized_note(cls, usr, url_id, mode='read-note', req=None):
        text = req.POST.get('edited_note', '')
        qlist = Library.objects.filter(usr=usr, id=url_id).select_related()
        data = b"<html>Not Available</html>"
        mtype = 'text/html'
        if qlist:
            row = qlist[0]
            media_path = row.media_path
            if media_path and os.path.exists(media_path):
                with open(media_path, "w") as f:
                    f.write(text)
                mtype = 'text/html'
        response = HttpResponse()
        response['mimetype'] = mtype
        response['content-type'] = mtype
        response.write(bytes("Saved", "utf-8"))
        return response

    @staticmethod
    def format_note(row, media_path):
        content = open(media_path, "r").read()
        if row:
            if '/' in row.directory:
                base_dir = '{}/{}/subdir/{}/{}'.format(settings.ROOT_URL_LOCATION,
                                                       row.usr.username, row.directory,
                                                       row.id)
            else:
                base_dir = '{}/{}/{}/{}'.format(settings.ROOT_URL_LOCATION,
                                                row.usr.username, row.directory,
                                                row.id)
            read_url = base_dir + '/read'
            read_pdf = base_dir + '/read-pdf'
            read_png = base_dir + '/read-png'
            read_html = base_dir + '/read-html'
        else:
            read_url = read_pdf = read_png = read_html = '#'
        card_bg = ''
        card_tab = ''
        if row.reader_mode == UserSettings.DARK:
            card_bg = 'text-white bg-dark'
            card_tab = 'bg-dark border-dark text-white'
        elif row.reader_mode == UserSettings.LIGHT:
            card_bg = 'bg-light'
        elif row.reader_mode == UserSettings.GRAY:
            card_bg = 'text-white bg-secondary'
            card_tab = 'bg-secondary border-secondary text-white'
        template = """
        <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <link rel="stylesheet" href="/static/css/bootstrap.min.css">
                <link rel="stylesheet" href="/static/css/bootstrap.min.css.map">
                <script src="/static/js/jquery-3.3.1.min.js"></script>
                <script src="/static/js/popper.min.js"></script>
                <script src="/static/js/bootstrap.min.js"></script>
                <link rel="stylesheet" href="/static/css/summernote-bs4.css">
                <script src="/static/js/summernote-bs4.js"></script>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta name="referrer" content="no-referrer">
            </head>
        <body>
            <div class="row px-4" id="summernote"></div>
            <div class="row px-4 py-4">
                <button id="save" class="btn btn-primary" onclick="save()" type="button"> Save </button>
            </div>
            <script> $('#summernote').summernote({{placeholder: "Text..", tabsize: 10, height: 500}});
            $("#summernote").summernote("code", `{content}`);
            var save = function() {{
              var markup = $('#summernote').summernote('code');
              var formdata = new FormData;
                formdata.append('edited_note', markup);
                var csrftoken = getCookie('csrftoken');
                var client = new postRequestUpload();
                var api_link = window.location.href + '-save';
                client.post(api_link, formdata, csrftoken, function(response) {{
                    console.log(response);
                }})
            }};

            function getCookie(name) {{
                var cookieValue = null;
                if (document.cookie && document.cookie !== '') {{
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {{
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }}
                    }}
                }}
                return cookieValue;
            }};

            var postRequestUpload = function() {{
                this.post = function(url, params, token, callbak) {{
                    var http_req = new XMLHttpRequest();
                    http_req.onreadystatechange = function() {{ 
                        if (http_req.readyState == 4 && http_req.status == 200)
                            {{callbak(http_req.responseText);}}
                    }}
                    http_req.open( "POST", url, true );
                    http_req.setRequestHeader("X-CSRFToken", token);
                    http_req.send(params);
                }}
            }};
             </script>
            
        </body>
        </html>
        """.format(title="Notes", content=content)
        return template
    
    @classmethod
    def get_content(cls, row, url_id, media_path):
        data = ""
        req = cls.vnt.get(row.url)
        media_path_parent, _ = os.path.split(media_path)
        if not os.path.exists(media_path_parent):
            os.makedirs(media_path_parent)
        if req and req.content_type and req.html:
            mtype = req.content_type.split(';')[0].strip()
            if mtype in cls.mtype_list:
                content = req.html
                with open(media_path, 'w') as fd:
                    fd.write(content)
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
        media_dir, file_path = os.path.split(media_path)
        resource_dir = os.path.join(settings.ARCHIVE_LOCATION, 'resources', str(row.id))
        resource_link = '{}/{}/{}/{}/{}'.format(settings.ROOT_URL_LOCATION,
                                                row.usr.username, row.directory,
                                                str(row.id), 'resources')
        if not os.path.exists(resource_dir):
            os.makedirs(resource_dir)
        if not content:
            content = ""
            with open(media_path, encoding='utf-8', mode='r') as fd:
                content = fd.read()
        soup = BeautifulSoup(content, 'lxml')
        for script in soup.find_all('script'):
            script.decompose()
        url_path = row.url
        ourl = urlparse(url_path)
        ourld = ourl.scheme + '://' + ourl.netloc
        link_list = soup.find_all(['a', 'link', 'img'])
        for link in link_list:
            if link.name == 'img':
                lnk = link.get('src', '')
            else:
                lnk = link.get('href', '')
            if lnk and lnk != '#':
                if link.name == 'img' or (link.name == 'link' and '.css' in lnk):
                    lnk = dbxs.format_link(lnk, url_path)
                    lnk_bytes = bytes(lnk, 'utf-8')
                    h = hashlib.sha256(lnk_bytes)
                    lnk_hash = h.hexdigest()
                    if link.name == 'img':
                        link['src'] = resource_link + '/' + lnk_hash
                        if custom_html:
                            link['class'] = 'img-thumbnail'
                    else:
                        lnk_hash = lnk_hash + '.css'
                        link['href'] = resource_link + '/' + lnk_hash
                    file_image = os.path.join(resource_dir, lnk_hash)
                    if not os.path.exists(file_image):
                        cls.vnt_noblock.get(lnk, out=file_image)
                        logger.info('getting file: {}, out: {}'.format(lnk, file_image))
                elif lnk.startswith('http'):
                    pass
                else:
                    nlnk = dbxs.format_link(lnk, url_path)
                    if link.name == 'img':
                        link['src'] = nlnk
                        if custom_html:
                            link['class'] = 'img-thumbnail'
                    else:
                        link['href'] = nlnk
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
            new_tag = soup.new_tag("script", src="/static/js/jquery-3.3.1.min.js")
            soup.find("body").append(new_tag)
            new_tag = soup.new_tag("script", src="/static/js/annotator.min.js")
            soup.find("body").append(new_tag)
            new_tag = soup.new_tag("script")
            new_tag.append(cls.ANNOTATION_SCRIPT)
            soup.find("body").append(new_tag)
            data = soup.prettify()
        return bytes(data, 'utf-8')
        
    
    @classmethod
    def custom_template(cls, title, content, row):
        if row:
            if '/' in row.directory:
                base_dir = '{}/{}/subdir/{}/{}'.format(settings.ROOT_URL_LOCATION,
                                                        row.usr.username, row.directory,
                                                        row.id)
            else:
                base_dir = '{}/{}/{}/{}'.format(settings.ROOT_URL_LOCATION,
                                                row.usr.username, row.directory,
                                                row.id)
            read_url = base_dir + '/read'
            read_pdf = base_dir + '/read-pdf'
            read_png = base_dir + '/read-png'
            read_html = base_dir + '/read-html'
        else:
            read_url = read_pdf = read_png = read_html = '#'
        card_bg = ''
        card_tab = ''
        if row.reader_mode == UserSettings.DARK:
            card_bg = 'text-white bg-dark'
            card_tab = 'bg-dark border-dark text-white'
        elif row.reader_mode == UserSettings.LIGHT:
            card_bg = 'bg-light'
        elif row.reader_mode == UserSettings.GRAY:
            card_bg = 'text-white bg-secondary'
            card_tab = 'bg-secondary border-secondary text-white'
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
                    <div class="col-sm {card_bg}">
                        <div class='card text-left {card_bg} mb-3'>
                            <div class='card-header'>
                                <ul class="nav nav-tabs card-header-tabs">
                                    <li class="nav-item">
                                        <a class="nav-link {card_tab} active" href="{read_url}">HTML</a>
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
                </div>
            </div>
        <script src="/static/js/jquery-3.3.1.min.js"></script>
        <script src="/static/js/annotator.min.js"></script>
        <script>{annot_script}</script>
        </body>
        </html>
        """.format(title=title, content=content,
                   read_url=read_url, read_pdf=read_pdf,
                   read_png=read_png, read_html=read_html,
                   card_bg=card_bg, card_tab=card_tab,
                   annot_script=cls.ANNOTATION_SCRIPT)
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
                if not favicon_link:
                    urlp = urlparse(url_name)
                    favicon_link = urlp.scheme + '://' + urlp.netloc + '/favicon.ico'
            if favicon_link:
                cls.vnt_noblock.get(favicon_link, out=final_favicon_path)
    
    @classmethod
    def is_human_readable(cls, mtype):
        human_readable = False
        if mtype in cls.readable_format:
            human_readable = True
        return human_readable

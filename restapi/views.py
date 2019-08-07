import re
from collections import Counter
from django.shortcuts import render
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from pages.dbaccess import DBAccess as dbxs
from pages.models import Library, Tags, URLTags, UserSettings


class AddURL(APIView):
    
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        usr = request.user
        url = request.POST.get("url")
        media_link = request.POST.get("media_link")
        if media_link and media_link == "yes":
            is_media_link = True
        else:
            is_media_link = False
        directory = request.POST.get("directory")
        if directory and directory.startswith("/"):
            directory = directory[1:]
        save_favicon = request.POST.get("save_favicon")
        if save_favicon and save_favicon == "no":
            save_favicon = False
        else:
            save_favicon = True
        row = UserSettings.objects.filter(usrid=request.user)
        if url:
            http = re.match(r'^(?:http)s?://', url)
        else:
            http = None
        
        if http and directory:
            if self.check_dir_and_subdir(usr, directory):
                dbxs.add_new_url(usr, request, directory, row, is_media_link=is_media_link,
                                 url_name=url, save_favicon=save_favicon)
                content = {"url": url, "is_media_link": is_media_link, "directory": directory, "status": "added"}
            else:
                content = {"msg": "Maybe required directory not found. So please create directories before adding url"}
        else:
            content = {"msg": "wrong url format or directory"}

        return Response(content)

    def check_dir_and_subdir(self, usr, dirname):
        if dirname.startswith("/"):
            dirname = dirname[1:]
        if '/' in dirname:
            pdir, subdir = dirname.rsplit('/', 1)
            if self.verify_parent_directory(usr, pdir):
                self.verify_or_create_subdirectory(usr, pdir, subdir)
                return True
            else:
                return False
        else:
            self.verify_or_create_parent_directory(usr, dirname)
            return True
            
    def verify_or_create_subdirectory(self, usr, pdir, subdir):
        if pdir and subdir:
            dirname = re.sub(r'/|:|#|\?|\\\\|\%', '-', subdir)
            if dirname:
                dirname = pdir+'/'+dirname
                qdir = Library.objects.filter(usr=usr, directory=dirname)
                if not qdir:
                    Library.objects.create(usr=usr, directory=dirname, timestamp=timezone.now()).save()
                    qlist = Library.objects.filter(usr=usr, directory=pdir, url__isnull=True).first()
                    if qlist:
                        if qlist.subdir:
                            slist = qlist.subdir.split('/')
                            if subdir not in slist:
                                qlist.subdir = '/'.join(slist + [subdir])
                                qlist.save()
                        else:
                            qlist.subdir = subdir
                            qlist.save()
                        
    def verify_parent_directory(self, usr, dirname):
        qdir = Library.objects.filter(usr=usr, directory=dirname)
        if not qdir:
            return False
        else:
            return True
            
    def verify_or_create_parent_directory(self, usr, dirname):
        dirname = re.sub(r'/|:|#|\?|\\\\|\%', '-', dirname)
        if dirname and not self.verify_parent_directory(usr, dirname):
            Library.objects.create(usr=usr, directory=dirname, timestamp=timezone.now()).save()


class ListDirectories(APIView):
    
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        usr_list = Library.objects.filter(usr=request.user).only('directory').order_by('directory')
        usr_list = [i.directory for i in usr_list if i.directory and i.url]
        usr_list = Counter(usr_list)
        return Response(usr_list)


class ListURL(APIView):
    
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        usr = request.user
        dirname = request.POST.get("directory")
        if dirname and dirname.startswith("/"):
            dirname = dirname[1:]
        if dirname:
            usr_list = dbxs.get_rows_by_directory(usr, directory=dirname)
            nlist = dbxs.populate_usr_list(usr, usr_list, create_dict=True, short_dict=True)
            return Response(nlist)
        else:
            return Response({"msg": "invalid directory"})


class Logout(APIView):
    
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, format=None):
        request.user.auth_token.delete()
        return Response(status=200)

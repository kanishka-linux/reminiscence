# Reminiscence

Self-hosted Bookmark and Archive manager

Table of Contents
=================

* [Features](#features)

* [Installation](#installation)

    * [Normal Method](#installation)

    * [Using Docker](#using-docker)

* [Documentation](#documentation)
    
    * [Adding Directories and Links](#adding-directories-and-links)
    
    * [Automatic Tagging and Summarization](#automatic-tagging-and-summarization)
    
    * [Reader Mode](#reader-mode)
    
    * [Generating PDF and Full-Page Screenshot](#generating-pdf-and-png)

    * [Archiving Media Elements](#archiving-media-elements)
    
    * [Public, Private and Group Directories](#public-private-group-directories)
    
    * [Searching Bookmarks](#searching-bookmarks)
    
    * [About Database](#about-database)

    * [Understanding Settings files](#understanding-settings-files)
    
    * [Gunicorn plus Nginx setup](#gunicorn-plus-nginx-setup)
    
    * [Handling Background Tasks](#handling-background-tasks-without-using-celery-or-other-external-task-queue-manager)

* [Future Roadmap](#future-roadmap)

* [Motivation](#motivation)

# Features

* Bookmark links and edit its metadata (like title, tags, summary) via web-interface.

* Archive links content in HTML, PDF or full-page PNG format.

* Automatic archival of links to non-html content like pdf, jpg, txt etc..

    **i.e.** Bookmarking links to pdf, jpg etc.. via web-interface will automatically save those files on server.

* Supports archival of media elements of a web-page using third party download managers (from v0.2+ onwards).
 
* Directory based categorization of bookmarks

* Automatic tagging of HTML links.

* Automatic summarization of HTML content. 

* Special readability mode.

* Search bookmarks according to url, title, tags or summary.

* Supports multiple user accounts.

* Supports public and group directory for every user.

* Upload any file from web-interface for archieving.

* Easy to use admin interface for managing multiple users.

* Import bookmarks from Netscape Bookmark HTML file format.

* Supports streaming of archived media elements.


# Installation

1. First make sure that **python 3.5.2+** (recommended version is 3.6.5+) is installed on system and install following packages using native package manager.

        1. virtualenv
    
        2. wkhtmltopdf (for html to pdf/png conversion)
    
        3. redis-server (optional)

        4. chromium (optional from 0.2+)
    
2. Installation of above dependencies in Arch or Arch based distros

        $ sudo pacman -S python-virtualenv wkhtmltopdf redis chromium
    
3. Installation of above dependencies in Debian or Ubuntu based distros

        $ sudo apt install virtualenv wkhtmltopdf redis-server chromium-browser

**Note:** Name of above dependencies may change depending on distro or OS, so install accordingly. Once above dependencies are installed, execute following commands, which are distro/platform independent. 
    
#### Now execute following commands in terminal.

    $ mkdir reminiscence
    
    $ cd reminiscence
    
    $ virtualenv -p python3 venv
    
    $ source venv/bin/activate
    
    $ cd venv
    
    $ git clone https://github.com/kanishka-linux/reminiscence.git
    
    $ cd reminiscence
    
    $ pip install -r requirements.txt
    
    $ mkdir logs archive tmp
    
    $ python manage.py generatesecretkey
    
    $ python manage.py nltkdownload
    
    $ python manage.py migrate
    
    $ python manage.py createsuperuser

    $ python manage.py runserver 127.0.0.1:8000 
    
    open 127.0.0.1:8000 using any browser, login and start adding links
    
    **Note:** replace localhost address with local ip address of your server
            
              to access web-interface from anywhere on the local network

    Admin interface available at: /admin/
              

#### Setting up Celery (optional):

1. Generating PDFs and PNGs are resource intesive and time consuming. We can delegate these tasks to celery, in order to execute them in the background. 
    
        Edit reminiscence/settings.py file and set USE_CELERY = True
    
2. Now open another terminal in the same topmost project directory and execute following commands:
    
        $ cd venv
    
        $ source bin/activate
    
        $ cd venv/reminiscence
    
        $ celery -A reminiscence worker --loglevel=info
    
3. launch redis-server from another terminal
    
        $ redis-server
        
## Using Docker

Using docker is convenient compared to normal installation method described above. It will take care of configuration and setting up of gunicorn, nginx and also postgresql database. (Setting and running up these three things can be a bit cumbersome, if done manually, which is described below in separate section.) It will also automatically download headless version of wkhtmltopdf from official github repository (Since, many distros do not package wkhtmltopdf with headless feature) and nltk data set, apart from installing python based dependencies.

1. Install docker and docker-compose

2. Enable/start docker service. Instructions for enabling docker might be different in different distros. Sample instruction for enabling/starting docker will look like

        $ systemctl enable/start docker.service

3. clone github repository and enter directory

        $ git clone https://github.com/kanishka-linux/reminiscence.git

        $ cd reminiscence

4. build and start

        $ sudo docker-compose up --build

        Note: Above instruction will take some time when executed for the first time.

5. Above step will also create default user: 'admin' with default password: 'changepassword'

6. If IP address of server is '**192.168.1.2**' then admin interface will be available at 

        192.168.1.2/admin/

        Note: In this metod, there is no need to
              attach port number to IP address.

7. Change default admin password from admin interface and create new regular user. After that logout, and open '**192.168.1.2**'. Now login with regular user for regular activity.

8. For custom configuration, modify nginx.conf and dockerfiles available in the repository. After that execute step 4 again.

**Note:** If Windows users are facing problem in mounting data volume for Postgres, they are advised to refer this [issue](https://github.com/kanishka-linux/reminiscence/issues/1).

**Note:** Ubuntu 16.04 users might have to modify docker-compose.yml file and need to change version 3 to 2. [issue](https://github.com/kanishka-linux/reminiscence/issues/4)

# Documentation

## Adding Directories And Links

* **Creating Directory**

    Users first have to create directory from web interface.

    **Note:** Currently '/' and few other special characters are not allowed as characters in directory name. If users are facing problem when accessing directory, then they are advised to rename directory and remove special characters.

    ![reminiscence](/Images/default.png)
    
* **Adding Links**

    Users have to navigate to required directory and then need to add links to it. URLs are fetched asynchronously from the source for gathering metadata initially. Users have to wait for few seconds, after that page will refresh automatically showing new content. It may happen, nothing would show up after automatic page refresh (e.g. due to slow URL fetching) then try refreshing page manually by clicking on directory entry again. Maybe in future, I will have to look into django channels and websockets to enable real-time duplex communication between client and server.

    ![reminiscence](/Images/show_bookmarks.png)


## Automatic Tagging and Summarization

This feature has been implemented using NLTK library. The library has been used for proper tokenization and removing stopwords from sentence. Once stopwords are removed, top K high frequency words (where value of K is decided by user) are used as tags. In order to generate summary of HTML content, score is alloted to a sentence based on frequency of non-stopwords contained in it. After that highests score sentences (forming 1/3'rd of total content) are used to generate summary. It is one of the simplest methods for automatic tagging and summarization, hence not perfect. It can't tag group of meaningful words. e.g. It will not consider 'data structure' as a single tag. Supporting multi-word tags is in TODO list of the project.

About summarization, there are many advance methods which may give even more better results, which users can find in [this paper](https://arxiv.org/pdf/1707.02268.pdf). Both these feature needs to be activated from **Settings** box. It is off by default.

![reminiscence](/Images/settings.png)

## Reader mode

Once user will open link using inbuilt reader, the application will try to present text content, properly formatted for mobile devices whenever possible. In reader mode user will also find options **Original, PDF and PNG**, at the top header. These options will be available only when user has archived the link in those formats. Options for selecting archive file format is available in every user's **Settings** box.  If **Original**, format is selected then users can see the text content along with original stylesheet and linked images. Javascript will be removed from original file format due to security reasons. If page can't be displayed due to lack of javascript then users have to depend on either PDF or full-page PNG formats.

![reminiscence](/Images/reader.png)

## Generating PDF and PNG

PDF and full-page screenshot in PNG format of HTML page will be generated using wkhtmltopdf. It is headless tool but in some distro it might not be packaged with headless feature. In such cases, users have to run it using Xvfb. In order to use it headlessly using Xvfb, set **USE_XVFB = True** in reminiscence/settings.py file and then install xvfb using command line.

**Note:** Use Xvfb, only when wkhtmltopdf is not packaged with headless feature.

**Note:** Alternatively Users can also download official headless wkhtmltopdf for their resepctive distro/OS from [here](https://github.com/wkhtmltopdf/wkhtmltopdf/releases). Only problem is that, users will have to update the package manually on their own for every new update.

**Why not use Headless Chromium?** 

Currently headless chromium doesn't support full page screenshot, otherwise I might have used it blindly. There is another headless browser [hlspy](https://github.com/kanishka-linux/hlspy), based on QtWebEngine, which I built for my personal use. **hlspy** can generate entire html content, pdf document and full page screenshot in one single request and that too using just one single process. In both chromium and wkhtmltopdf, one has to execute atleast two separate processes for doing the same thing. The main problem with hlspy is that it is not completely headless, it can't run without X. It requires xvfb for running in headless environment. 

In future, I'll try to provide a way to choose between different backends (i.e. chromium, wkhtmltopdf or hlspy) for performing these tasks.

**Note:** From v0.2+ onwards, support for headless Chromium has been added for generating HTML and PDF content. Users can use this feature if default archived content has some discrepancies. Users need to install Chromium to use this feature.

## Archiving Media Elements

**Note:** This feature is available from v0.2+ onwards

1. In settings.py file add your favourite download manager to DOWNLOAD_MANAGERS_ALLOWED list. Default are curl and wget. In case of docker based method users have to make corresponding changes in dockersettings.py file.

2. open web-interface settings box and add command to Download Manager Field:
    
        ex: wget {iurl} -O {output}
    
        iurl -> input url
        output -> output path
    
3. Users should not substitute anything for {iurl} and {output} field, they should be kept as it is. In short, users should just write regular command with parameters and leave the {iurl} and {output} field untouched. (Note: do not even remove curly brackets).
    
4. Reminiscence server will take care of setting up of input url i.e. {iurl} and output path field i.e. {output}. 
    
5. If user is using youtube-dl as a download manager, then it is advisable to install ffmpeg along with it. In this case user has to take care of regular updating of youtube-dl on their own. In docker based installation, users have to add installation instructions for ffmpeg in Dockerfile; and then need to modify requirements.txt and add youtube_dl as dependency.

6. Web-interface settings box also contains, streaming option. If this option is enabled, then HTML5 compliant media files can be played inside browsers, otherwise they will be available for download on the client machine.

7. If users are upgrading from older version then they are advised to apply database migration using following commands, before using new features:

        python manage.py makemigrations

        python manage.py migrate

8. Finally, when adding url to any directory just prepend **md:** to url, so that the particular entry will be recognized by custom download manager.

        ex=> md:https://some-website-with-media-link.org/media-link

        Every entry added by this way will be treated as containing media.

9. Archived files are normally saved in **archive** folder. Users can change location of this folder via settings.py file. Users should note that in order to archive media files, the **archive** location should not contain any space.
e.g. archive location '/home/user/my downloads/archive' is not allowed. However location without space '/home/user/my_downloads/archive' is allowed.

10. By default, archived media links are not shared with anyone. However, users can create public links for some fixed time. Once a public link has been created, it will remain valid for 24 hours. Users can change this value by changing value of VIDEO_ID_EXPIRY_LIMIT in settings.py. These public links are also useful for playing non-HTML5 compliant archived media on regular media players like mpv/mplayer/vlc etc..It is also possible to generate a playlist in m3u format for a directory containing media links, which can be played by any popular media player. 

## Public-Private-Group directories

By default, all directories and all links are private and are not shared with anyone. However, users can select one public directory and one group directory from all available directories for sharing links. User can set public and group directory via settings. Links placed in public directory will be available for public viewing and links placed in group directory will be available for pre-determined list of users selected by account holder.

Public links of a user can be accesed at the url: 

        /username/profile/public

Group links of a user can be accesed by pre-determined group of users at the url: 

        /username/profile/group

## Searching Bookmarks

Bookmarks can be searched according to title, url, tag or summary by using search menu available at the top most navigation bar. By default bookmarks will be searched according to **title**. In order to search according to url, tag or summary, users have to prefix **url:**, **tag:**, or **sum:** to the search term, in the search box.

Note: Special search prefix **tag-wall:** will display all available tags.


## About Database

By default, reminiscence uses sqlite database, but users can replace it with any database supported by django ORM like postgresql. Some simple instructions for using postgresql with django are available [here](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04) . Users can also take a look at this [wiki](https://wiki.archlinux.org/index.php/PostgreSQL), for proper postgresql database setup. There might be some changes in the instructions depending on the OS and distributions you are using.

## Understanding Settings Files

reminiscence folder contains three settings files 

    1. settings.py

    2. defaultsettings.py

    3. dockersettings.py

* In normal installation procedure, settings.py file is used. If user will make changes in it then those changes will be reflected in normal installation method. 

* In docker based method dockersettings.py file is used. Settings of this file will be copied during docker installation method.

* defaultsettings.py is the backup file. If user has somehow corrupted settings files while manually editing, then original settings can be restored using this file.

## Gunicorn plus Nginx setup

**(optional)**

* Install gunicorn, if not installed. (pip install gunicorn)

* Instead of using **python manage.py runserver** command as mentioned in above installation instructions use following command. Users can change parameters according to need. Only make sure to keep value of **timeout** argument somewhat bigger. Larger timeout value is useful, if upload speed is slow and user want to upload relatively large body from web-interface.

        $ gunicorn --max-requests 1000 --worker-class gthread --workers 2 --thread 5 --timeout 300 --bind 0.0.0.0:8000 reminiscence.wsgi

* Install **nginx** using native package manager of distro and then make adjustments to nginx config files as given below. Following is sample configuration. Adjust it according to need, but pay special attention to **proxy_read_timeout** and **client_max_body_size** variables. Incorrect value of these two variables can make upload from web-interface impractical.

            worker_processes  2;
        
            events {
                worker_connections  1024;
            }
        
        
            http {
                include       mime.types;
                default_type  application/octet-stream;
            
                sendfile        on;
                sendfile_max_chunk 512k;
                keepalive_timeout  65;
                proxy_read_timeout 300s;
            
                server {
                listen       80;
                server_name  localhost;
                client_max_body_size 1024m;
                  
                location /static/ {
                        root /home/reminiscence/venv/reminiscence; # root of project directory
                        aio threads;
                    }
                location = /favicon.ico { access_log off; log_not_found off; }
                location / {
                    proxy_pass http://127.0.0.1:8000;
                    proxy_set_header Host $host;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    root /home/reminiscence/venv/reminiscence; #root of project directory
                }
        
                
                error_page   500 502 503 504  /50x.html;
                location = /50x.html {
                    root   /usr/share/nginx/html;
                }
                }
            }


* Once nginx config file is properly configured, start/enable nginx.service. For detailed instructions take a look at this [tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04) or refer this [wiki](https://wiki.archlinux.org/index.php/Nginx). There are some barebone instructions available [here](http://gunicorn.org/index.html#deployment), which users might find useful.

## Handling background tasks without using celery or other external task queue manager

* This application has to perform number of background tasks, like Fetching web-page, favicons and converting pages to pdf/png.  In order to do these tasks application uses [Vinanti](https://github.com/kanishka-linux/vinanti) library. I wrote this library as a simple easy to use async HTTP client which one can integrate with synchronous codebase of python. However, it can be used easily for executing some arbitrary function in the background (using either threads or processes) without having to worry about managing threads/processes manually. It was just an experiment, but it worked very well in this self-hosted application. 

* When importing list of bookmarks numbering 1500+, it has to make 1500 requests to bookmarked links in order to get web-page contents (for generating automatic tags/summary) and 1500+ more requests for fetching favicons. With aiohttp as backend for Vinanti, the application used only two threads for managing these 3000+ http requests aynchronously and at the same time allowed development server to remain responsive (without using gunicorn) for any incoming request. For executing pdf/png conversion tasks in the background, the task queue of Vinanti seemed sufficient for handling requests from few users at a time. 

* Making 3000 http requests in the background, archiving their output as per content-type, along with generating tags/summary using NLTK and database (postgresql) write (without converting pages to png/pdf), took somewhere along 12-13 minutes with aiohttp as backend and 50 async http requests at a time. By default, Vinanti does not use aiohttp in this project. In order to use aiohttp, user should set **VINANTI_BACKEND='aiohttp'** in settings.py file. Converting pages to png/pdf will be time consuming and might take hours depending on server and number of bookmarked links.

* Even though, this appraoch is working well for self-hosted application with limited number of users with limited tasks. For large number of tasks, it it better to use dedicated external task queue manager. That's why option has been provided to set up celery, if a user and his group has large number of bookmarked links which they want to convert to pdf/png format. Maybe in future, option may be provided for making http requests and postprocessing content to celery, if current setup with Vinanti won't deliver upto expectations.

# Future Roadmap

- [x] Allow people to write custom scripts or use third party tools for their unique archival needs. 

- [x] Provide an option to change headless browsers for PDF/PNG generation.

- [ ] Provide token-based authentication which will help in developing browser addons or mobile applications

- [ ] Support multi-word tagging

- [ ] Provide browser addons

- [ ] Document API 

- [ ] Support for text annotation

# Motivation

Till few years back, I used to think that once something has been published on the web, it is going to remain there forever in some form or other. But web of today is different. Now we never know, when some valuable web resource (like web-pages, images, text, pdf etc...) will disappear from the web completely. There might be variety of reasons for disappearance (e.g. author of resource lost interest in maintaining it, low traffic or some other political-economic reasons). I don't want to go into details, but there are plenty of reasons due to which web-resource that we savoured in the past, might become un-available in the future. If we are lucky, then we may find mirrors of popular sites of the past, archived by volunteers. But, the same can't be said true of obscure and rare web content.

So for quite some time, I was looking for saving personal memories of web effectively and in a well organized manner, which will remain with user and not with some third party. As I could not find suitable already existing solution meeting may taste (directory based organization, automatic tagging/summarization, archiving in various formats etc..), I decided develop one.

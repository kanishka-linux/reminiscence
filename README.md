# Reminiscence

Self-hosted Bookmark and Archive manager

Table of Contents
=================

* [Features](#features)

* [Installation](#installation)

* [Documentation](#documentation)

    * [Creating Directory](#creating-directing)
    
    * [Adding URLs](#adding-urls)
    
    * [Automatic Tagging and Summarization](#automatic-tagging-and-summarization)
    
    * [Reader Mode](#reader-mode)
    
    * [Generating PDF and Full-Page Screenshot](#generating-pdf-and-png)
    
    * [Public, Private and Group Directories](#public-private-group-directories)
    
    * [Searching Bookmarks](#searching-bookmarks)
    
    * [About Database](#about-database)
    
    * [Gunicorn plus Nginx setup](#gunicorn-plus-nginx-setup)
    
    * [Handling Background Tasks](#handling-background-tasks-without-using-celery-or-other-external-task-queue-manager)

* [Motivation](#motivation)

# Features

* Bookmark links and edit its metadata (like title, tags, summary) via web-interface.

* Archive links content in HTML, PDF or full-page PNG format.

* Automatic archival of links to non-html content like pdf, jpg, txt etc..

    **i.e.** Bookmarking links to pdf, jpg etc.. via web-interface will automatically save those files on server.
 
* Directory based categorization of bookmarks

* Automatic tagging of HTML links.

* Automatic summarization of HTML content. 

* Special readability mode.

* Search bookmarks according to url, title, tags or summary.

* Supports multiple user accounts.

* Supports public and group directory for every user, which can be shared with public or group of users.

* Upload any file from web-interface for archieving.

* Easy to use admin interface for managing multiple users.

* Import bookmarks from Netscape Bookmark HTML file format.

# Installation

1. First make sure that **python 3.5.2+** (recommended version is 3.6.5+) is installed on system and install following packages using native package manager.

        1. virtualenv
    
        2. wkhtmltopdf (for html to pdf/png conversion)
    
        3. redis-server (optional)
    
2. Installation of above dependencies in Arch or Arch based distros

        $ sudo pacman -S python-virtualenv wkhtmltopdf redis
    
3. Installation of above dependencies in Debian or Ubuntu based distros

        $ sudo apt install virtualenv wkhtmltopdf redis-server
    
    
#### Now execute following commands in terminal.

    $ mkdir reminiscence
    
    $ cd reminiscence
    
    $ virtualenv -p python3 venv
    
    $ source venv/bin/activate
    
    $ cd venv
    
    $ git clone https://github.com/kanishka-linux/reminiscence.git
    
    $ cd reminiscence
    
    $ pip install -r requirements.txt
    
    $ mkdir logs archive
    
    $ python manage.py generatesecretkey
    
    $ python manage.py nltkdownload
    
    $ python manage.py migrate
    
    $ python manage.py createsuperuser

    $ python manage.py runserver 127.0.0.1:8000 
    
    open 127.0.0.1:8000 using any browser, login and start adding links
    
    **Note:** replace localhost address with local ip address of your server
            
              to access web-interface from anywhere on the local network
              

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
        
            
# Documentation

## Creating Directory

Users first have to create directory from web interface

![reminiscence](/Images/default.png)
    
## Adding URLs

Users have to navigate to required directory and then need to add links to it. URLs are fetched asynchronously from the source for gathering metadata initially. Users have to wait for few seconds, after that page will refresh automatically showing new content. It may happen, nothing would show up after automatic page refresh, if URL fetching is slow due to various reasons, then try refreshing page manually by clicking on directory entry again. Maybe in future, I will have to look into django channels and websockets to enable real-time duplex communication between client and server.

![reminiscence](/Images/show_bookmarks.png)


## Automatic Tagging and Summarization

This feature has been implemented using NLTK library. The library has been used for proper tokenization and removing stopwords from sentence. Once stopwords are removed, top K high frequency words (where value of K is decided by user) are used as tags. In order to generate summary of HTML content, score is alloted to a sentence based on frequency of non-stopwords contained in it. After that highests score sentences (forming 1/3'rd of total content) are used to generate summary. It is one of the simplest methods for automatic tagging and summarization, hence not perfect. It can't tag group of meaningful words. e.g. It will not consider 'data structure' as a single tag. Supporting multi-word tags is in TODO list of the project.

About summarization, there are many advance methods which may give even more better results, which users can find in [this paper](https://arxiv.org/pdf/1707.02268.pdf). Both these feature needs to be activated from **Settings** box. It is off by default.

![reminiscence](/Images/settings.png)

## Reader mode

Once user will open document using inbuilt reader, the application will try to present text content, properly formatted for mobile devices whenever possible. In reader mode user will also find options **Original, PDF and PNG**, at the top header. These options will be available only when user has archived the link in those formats. Options for selecting archive file format is available in every user's **Settings** box.  If **Original**, format is selected then users can see the text content along with original stylesheet and linked images. Javascript will be removed from original file format due to security reasons. If page can't be displayed due to lack of javascript then users have to depend on either PDF or full-page PNG formats.

![reminiscence](/Images/reader.png)

## Generating PDF and PNG

PDF and full-page screenshot in PNG format of HTML page will be generated using wkhtmltopdf. It is headless tool but in some distro it might not be packaged with headless feature. In such cases, users have to run it using Xvfb. In order to use it headlessly using Xvfb, set **USE_XVFB = True** in reminiscence/settings.py file and then install xvfb using command line.

**Note:** Use Xvfb, only when wkhtmltopdf is not packaged with headless feature.

**Why not use Headless Chromium?** 

Currently headless chromium doesn't support full page screenshot, otherwise I might have used it blindly. There is another headless browser [hlspy](https://github.com/kanishka-linux/hlspy), based on QtWebEngine, which I built for my personal use. **hlspy** can generate entire html content, pdf document and full page screenshot in one single request and that too using just one single process. In both chromium and wkhtmltopdf, one has to execute atleast two separate processes for doing the same thing. The main problem with hlspy is that it is not completely headless, it can't run without X. It requires xvfb for running in headless environment. 

In future, I'll try to provide a way to choose between different backends (i.e. chromium, wkhtmltopdf or hlspy) for performing these tasks.

## Public-Private-Group directories

By default, all directories and all links are private and are not shared with anyone. However, users can select one public directory and one group directory from all available directories for sharing links. User can set public and group directory via settings. Links placed in public directory will be available for public viewing and links placed in group directory will be available for pre-determined list of users selected by account holder.

Public links of a user can be accesed at the url: **/username/profile/public**

Group links of a user can be accesed by pre-determined group of users at the url: **/username/profile/group**

## Searching Bookmarks

Bookmarks can be searched according to title, url, tag or summary by using search menu available at the top most navigation bar. By default bookmarks will be searched according to **title**. In order to search according to url, tag or summary, users have to prepend **url:**, **tag:**, or **sum:** to the search term, in the search box.


## About Database

By default, reminiscence uses sqlite database, but users can replace it with any database supported by django ORM like postgresql. Some simple instructions for using postgresql with django are available [here](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04) . Users can also take a look at this [wiki](https://wiki.archlinux.org/index.php/PostgreSQL), for proper postgresql database setup. There might be some changes in the instructions depending on the OS and distributions you are using.

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

# Motivation

Till few years back, I used to think that once something has been published on the web, it is going to remain there forever in some form or other. But web of today is different. Now we never know, when some valuable web resource (like web-pages, images, text, pdf etc...) will disappear from the web completely. There might be variety of reasons for disappearance (e.g. author of resource lost interest in maintaining it, low traffic or some other political-economic reasons). I don't want to go into details, but there are plenty of reasons due to which web-resource that we savoured in the past, might become un-available in the future. If we are lucky, then we may find mirrors of popular sites of the past, archived by volunteers. But, the same can't be said true of obscure and rare web content.

So for quite some time, I was looking for saving personal memories of web effectively and in a well organized manner, which will remain with user and not with some third party. As I could not find suitable already existing solution meeting may taste (directory based organization, automatic tagging/summarization, archiving in various formats etc..), I decided develop one.

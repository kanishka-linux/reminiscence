# Reminiscence

Self-hosted Bookmark and Archieve manager

# Features

* Bookmark links and edit its metadata via web-interface.

* Archieve links content in HTML, PDF or full-page PNG format.

* Automatic archival of links to non-html content like pdf, jpg, txt etc..
 
* Directory based categorization of bookmarks

* Automatic tagging of HTML content links. (supports manual tagging also)

* Automatic summarization of HTML content. 

* Special readability mode.

* Search bookmarks according to url, title or tags

* Supports multiple user accounts.

* Supports public and group directory of links which can be shared with public or group of users.

# Installation

First make sure that **python 3.5+** is installed on system and install following packages using native package manager.

    2. virtualenv
    
    3. wkhtmltopdf (for html to pdf/png conversion)
    
    4. redis-server (optional)
    
Installation of above dependencies in Arch or Arch based distros

    $ sudo pacman -S python-virtualenv wkhtmltopdf redis
    
Installation of above dependencies in Debian or Ubuntu based distros

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
    
    $ mkdir logs archieve archieve/favicons
    
    $ python manage.py generatesecretkey
    
    $ python manage.py migrate
    
    $ python manage.py createsuperuser

    $ python manage.py runserver 127.0.0.1:8000 
    
    open 127.0.0.1:8000 from any browser, login and start adding links
    
    **Note:** replace localhost address with local ip address of your server
            
              to access web-interface from anywhere on the local network
              
        
#### Setting up Celery (optional):

Generating PDF's and PNG's are resource intesive and time consuming. We can delegate these tasks to celery, in order to execute them in the background. 
    
    1. Edit reminiscence/settings.py file and set USE_CELERY = True
    
Now open another terminal in the same topmost project directory and execute following commands:
    
    $ cd venv
    
    $ source bin/activate
    
    $ cd venv/reminiscence
    
    $ celery -A reminiscence worker --loglevel=info
    
launch redis-server from another terminal
    
    $ redis-server
        
            


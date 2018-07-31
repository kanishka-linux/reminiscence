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

First make sure that python 3.5+ and python-setuptools are properly installed. Then execute following commands in terminal:

    1. sudo pip install virtualenv
    
    2. mkdir reminiscence
    
    3. cd reminiscence
    
    4. virtualenv -p python3 venv
    
    5. source venv/bin/activate
    
    6. cd venv
    
    7. git clone https://github.com/kanishka-linux/reminiscence.git
    
    8. cd reminiscence
    
    9. pip install -r requirements.txt
    
    10. python manage.py generatesecretkey
    
    11. python manage.py migrate
    
    12. python manage.py createsuperuser

    13. python manage.py runserver 127.0.0.1:8000 
    
    14. open 127.0.0.1:8000 from any browser, login and start adding links
    
    Note: replace localhost address with local ip address of your server to access web-interface from anywhere on the local network
    
PDF's and PNG's are generated using wkhtmltopdf, so install it using package manager of your distro.

    For Arch or arch-based distros

        $ sudo pacman -S wkhtmltopdf 
    
    For debian or ubuntu based distros
    
        $ sudo apt install wkhtmltopdf
        
Setting up Celery (optional):

    Generating PDF's and PNG's are resource intesive and time consuming. We can delegate these tasks to celery which will be then executed in the background and will release load on the application. 
    
    1. Edit reminiscence/settings.py file and set USE_CELERY = True
    
    Now open another terminal in the same project directory
    
    2. cd venv
    
    3. source bin/activate
    
    4. cd venv/reminiscence
    
    5. celery -A reminiscence worker --loglevel=info
    
    6. Install and launch redis-server
        
        (Arch) $ sudo pacman -S redis
        
        (Ubuntu) $ sudo apt install redis-server
        
        launch: redis-server from another separate terminal
            


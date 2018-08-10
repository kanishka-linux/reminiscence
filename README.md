# Reminiscence

Self-hosted Bookmark and Archive manager

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

1. First make sure that **python 3.5.2+** is installed on system and install following packages using native package manager.

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

1. Generating PDF's and PNG's are resource intesive and time consuming. We can delegate these tasks to celery, in order to execute them in the background. 
    
        Edit reminiscence/settings.py file and set USE_CELERY = True
    
2. Now open another terminal in the same topmost project directory and execute following commands:
    
        $ cd venv
    
        $ source bin/activate
    
        $ cd venv/reminiscence
    
        $ celery -A reminiscence worker --loglevel=info
    
3. launch redis-server from another terminal
    
        $ redis-server
        
            
# Documentation

1. **Creating Directory**

    Users first have to create directory from web interface

    ![reminiscence](/Images/default.png)
2. **Adding URLs**

    Users have to navigate to required directory and then need to add links to it. URLs are fetched asynchronously from the source for gathering metadata initially. Users have to wait for few seconds, after that page will refresh automatically showing new content. It may happen, nothing would show up after automatic page refresh, if URL fetching is slow due to various reasons, then try refreshing page manually by clicking on directory entry again. Maybe in future, I will have to look into django channels and websockets to enable real-time duplex communication between client and server.

    ![reminiscence](/Images/show_bookmarks.png)


3. **Automatic Tagging and Summarization**

    This feature has been implemented using NLTK library. The library has been used for proper tokenization and removing stopwords from sentence. Once stopwords are removed, top K high frequency words (where value of K is decided by user) are used as tags. In order to generate summary of HTML content, score is alloted to a sentence based on frequency of non-stopwords contained in it. After that highests score sentences (forming 1/3'rd of total content) are used to generate summary. It is one of the simplest methods for automatic tagging and summarization, and hence not perfect. There are many advance methods which may give even more better results which users can find in [this paper](https://arxiv.org/pdf/1707.02268.pdf). This feature needs to be activated from **Settings** box. It is off by default.

    ![reminiscence](/Images/settings.png)

4. **Reader mode.**

    Once user will open document using inbuilt reader, the application will try to present text content, properly formatted for mobile devices whenever possible. In reader mode user will also find options **Original, PDF and PNG**, at the top header. These options will be available only when user has archived the link in those formats. Options for selecting archive file format is available in every user's **Settings** box.  If **Original**, format is selected then users can see the text content along with original stylesheet and linked images. Javascript will be removed from original file format due to security reasons. If page can't be displayed due to lack of javascript then users have to depend on either PDF or full-page PNG formats.

    ![reminiscence](/Images/reader.png)

5. **Generating PDF and PNG**

    PDF and full-page PNG of HTML content will be generated using wkhtmltopdf. It is headless tool but in some distro it might not be packaged with headless feature. In such cases, users have to run it using Xvfb. In order to use it headlessly using Xvfb, set **USE_XVFB = True** in reminiscence/settings.py file and then install xvfb using command line.

    **Note:** Use Xvfb, only when wkhtmltopdf is not packaged with headless feature.

6. **Public, Private and Group directories**

    By default, all directories and all links are private and are not shared with anyone. However, users can select one public directory and one group directory from all available directories for sharing links. User can set public and group directory via settings. Links placed in public directory will be available for public viewing and links placed in group directory will be available for pre-determined list of users selected by account holder.

    Public links of a user can be accesed at the url: **/username/profile/public**

    Group links of a user can be accesed by pre-determined group of users at the url: **/username/profile/group**

7. **Searching Bookmarks**

    Bookmarks can be searched according to title, url, tag or summary by using search menu available at the top most navigation bar. By default bookmarks will be searched according to **title**. In order to search according to url, tag or summary, users have to prepend **url:**, **tag:**, or **sum:** to the search term, in the search box.


8. **About Databse**

    By default, reminiscence uses sqlite database, but users can replace it with any database supported by django ORM like postgresql. Some simple instructions for using postgresql with django are available [here](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04) and [here](https://wiki.archlinux.org/index.php/PostgreSQL). There might be some changes in the instructions depending on the OS and distributions you are using.








import urllib.parse
from urllib.parse import urlparse
from collections import OrderedDict
    
try:
    from bs4 import BeautifulSoup
except ImportError:
    pass

try:
    from vinanti.utils import URL
    from vinanti.log import log_function
except ImportError:
    from utils import URL
    from log import log_function
    
logger = log_function(__name__)

class CrawlObject:
    
    def __init__(self, vnt, url_obj, onfinished, all_domain,
                 domains_allowed, depth_allowed):
        url = url_obj.url
        self.url_obj = url_obj
        ourl = urllib.parse.urlparse(url)
        self.scheme = ourl.scheme
        self.netloc = ourl.netloc
        self.vnt = vnt
        self.base_url = url
        self.ourl = url
        if ourl.path and not url.endswith('/'):
            self.base_url, _ = self.base_url.rsplit('/', 1)
        self.crawl_dict = OrderedDict()
        self.onfinished = onfinished
        self.link_set = set()
        if not self.base_url.endswith('/'):
            self.base_url = self.base_url + '/'
        if all_domain:
            self.all_domain = True
        else:
            self.all_domain = False
        dms = []
        if domains_allowed:
            if isinstance(domains_allowed, str):
                self.domains_allowed = (self.netloc, domains_allowed)
            else:
                dms = [i for i in domains_allowed]
                self.domains_allowed = (self.netloc, *dms, )
        else:
            self.domains_allowed = (self.netloc,)
        if isinstance(depth_allowed, int) and depth_allowed > 0:
            self.depth_allowed = depth_allowed
        else:
            self.depth_allowed = 0
        
    def start_crawling(self, result, url_obj, session):
        depth = url_obj.depth
        url = url_obj.url
        if '#' in url:
            pre, ext = url.rsplit('#', 1)
            if '/' not in ext and pre:
                url = pre
        ourl = urllib.parse.urlparse(url)
        scheme = ourl.scheme
        netloc = ourl.netloc
        base_url = url
        
        if ourl.path and not url.endswith('/'):
            base_url, _ = base_url.rsplit('/', 1)
            
        if not base_url.endswith('/'):
            base_url = base_url + '/'
            
        if result and result.html:
            soup = BeautifulSoup(result.html, 'html.parser')
            if soup.title:
                url_obj.title = soup.title
            if self.depth_allowed > depth or self.depth_allowed <= 0:
                link_list = [
                    soup.find_all('a'), soup.find_all('link'),
                    soup.find_all('img')
                    ]
                for links in link_list:
                    for link in links:
                        if link.name == 'img':
                            lnk = link.get('src')
                        else:
                            lnk = link.get('href')
                        
                        if not lnk or lnk == '#':
                            continue
                        lnk = self.construct_link(ourl, scheme, netloc,
                                                  url, base_url, lnk)
                        if lnk:
                            self.crawl_next_link(lnk, session, base_url,
                                                 depth, result.out_dir)
                    
    def crawl_next_link(self, lnk, session, base_url, depth, out_dir):
        n = urllib.parse.urlparse(lnk)
        crawl_allow = False
        if len(self.domains_allowed) > 1:
            for dm in self.domains_allowed:
                if dm in n.netloc or n.netloc == dm:
                    crawl_allow = True
        if not self.crawl_dict.get(lnk) and lnk not in self.link_set:
            self.link_set.add(lnk)
            if lnk.startswith(base_url) or self.all_domain or crawl_allow:
                self.vnt.crawl(lnk, depth=depth+1, session=session,
                               method='CRAWL_CHILDREN',
                               crawl_object=self,
                               onfinished=self.onfinished,
                               out=out_dir)
        
    def construct_link(self, ourl, scheme,
                       netloc, url, base_url,
                       lnk):
        if lnk and '#' in lnk:
            pre, ext = lnk.rsplit('#', 1)
            if '/' not in ext and pre:
                lnk = pre
        if lnk and lnk.startswith('//'):
            lnk = scheme + ':' + lnk
        elif lnk and lnk.startswith('/'):
            lnk = lnk[1:]
            lnk = scheme+ '://' + netloc + '/' + lnk
        elif lnk and lnk.startswith('./'):
            lnk = lnk[2:]
            lnk = base_url + lnk
        elif lnk and lnk.startswith('../'):
            lnk = lnk[3:]
            lnk = url.rsplit('/', 2)[0] + '/' + lnk
        elif lnk and lnk.startswith('#'):
            lnk = url
        elif lnk and not lnk.startswith('http'):
            lnk = base_url + lnk
        return lnk

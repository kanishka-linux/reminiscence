"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of vinanti.

vinanti is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

vinanti is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with vinanti.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import time
import asyncio
import urllib.parse
import urllib.request
from functools import partial
from urllib.parse import urlparse
from threading import Thread, Lock
from collections import OrderedDict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

try:
    import aiohttp
except ImportError:
    pass

try:
    from vinanti.req import Response
    from vinanti.req_aio import RequestObjectAiohttp
    from vinanti.req_urllib import RequestObjectUrllib
    from vinanti.crawl import CrawlObject
    from vinanti.utils import *
    from vinanti.log import log_function
except ImportError:
    from req import Response
    from req_aio import RequestObjectAiohttp
    from req_urllib import RequestObjectUrllib
    from crawl import CrawlObject
    from utils import *
    from log import log_function
    
logger = log_function(__name__)


class Vinanti:
    
    def __init__(self, backend='urllib', block=False, log=False,
                 old_method=False, group_task=False, max_requests=10,
                 multiprocess=False, loop_forever=False, **kargs):
        self.backend = backend
        self.block = block
        self.tasks = OrderedDict()
        self.loop_nonblock_list = []
        self.log = log
        self.group_task = group_task
        if not self.log:
            logger.disabled = True
        self.global_param_list = ['method', 'hdrs', 'onfinished']
        if kargs:
            self.session_params = kargs
            self.method_global = self.session_params.get('method')
            self.hdrs_global = self.session_params.get('hdrs')
            self.onfinished_global = self.session_params.get('onfinished')
        else:
            self.session_params = {}
            self.method_global = 'GET'
            self.hdrs_global = None
            self.onfinished_global = None
        self.tasks_completed = {}
        self.tasks_timing = {}
        self.cookie_session = {}
        self.task_counter = 0
        self.lock = Lock()
        self.task_queue = deque()
        self.crawler_dict = OrderedDict()
        self.max_requests = max_requests
        self.multiprocess = multiprocess
        if self.multiprocess:
            self.executor = ProcessPoolExecutor(max_workers=max_requests)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_requests)
        self.executor_process = None
        logger.info(
            'multiprocess: {}; max_requests={}; backend={}'
            .format(multiprocess, max_requests, backend)
            )
        self.loop = None
        self.old_method = old_method
        self.sem = None
        self.loop_forever = loop_forever
        
    def clear(self):
        self.tasks.clear()
        self.tasks_completed.clear()
        self.loop_nonblock_list.clear()
        self.session_params.clear()
        self.method_global = 'GET'
        self.hdrs_global = None
        self.onfinished_global = None
        self.cookie_session.clear()
        self.task_queue.clear()
        self.task_counter = 0
        
    def loop_close(self):
        if self.loop:
            self.loop.stop()
            self.loop = None
            logger.info('All Tasks Finished: closing loop')
            self.sem = None
                
    def session_clear(self, netloc=None):
        if netloc:
            if self.cookie_session.get(netloc):
                del self.cookie_session[netloc]
        else:
            self.cookie_session.clear()
    
    def tasks_count(self):
        return len(self.tasks_completed)
    
    def tasks_done(self):
        return self.task_counter
        
    def tasks_remaining(self):
        return len(self.tasks_completed) - self.task_counter
        
    def __build_tasks__(self, urls, method, onfinished=None,
                        hdrs=None, options_dict=None):
        self.tasks.clear()
        if options_dict is None:
            options_dict = {}
        if self.session_params:
            global_params = [method, hdrs, onfinished, options_dict]
            method, onfinished, hdrs, options_dict = self.__set_session_params__(*global_params)
            
        if isinstance(options_dict, dict):
            backend = options_dict.get('backend')
            if not backend:
                backend = self.backend
        else:
            backend = self.backend
        
        if self.block:
            req = None
            logger.info(urls)
            if isinstance(urls, str):
                length_new = len(self.tasks_completed)
                session, netloc = self.__request_preprocess__(urls, hdrs, method, options_dict)
                req = get_request(backend, urls, hdrs, method, options_dict)
                if session and req and netloc:
                    self.__update_session_cookies__(req, netloc)
                self.tasks_completed.update({length_new:[True, urls]})
                self.task_counter += 1
                if onfinished:
                    onfinished(length_new, urls, req)
                return req
        else:
            task_dict = {}
            task_list = []
            more_tasks = OrderedDict()
            if not isinstance(urls, list):
                urls = [urls]
            for i, url in enumerate(urls):
                length = len(self.tasks)
                length_new = len(self.tasks_completed)
                task_list = [url, onfinished, hdrs, method, options_dict, length_new]
                self.tasks.update({length:task_list})
                self.tasks_completed.update({length_new:[False, url]})
                if not self.group_task:
                    if self.tasks_remaining() < self.max_requests:
                        if len(urls) == 1:
                            task_dict.update({i:task_list})
                            self.start(task_dict)
                        else:
                            more_tasks.update({i:task_list})
                    else:
                        self.task_queue.append(task_list)
                        logger.info('append task')
            if more_tasks:
                self.start(more_tasks)
                logger.info('starting {} extra tasks in list'.format(len(more_tasks)))
    
    def __set_session_params__(self, method, hdrs, onfinished, options_dict):
        if not method and self.method_global:
            method = self.method_global
        if not hdrs and self.hdrs_global:
            hdrs = self.hdrs_global.copy()
        if not onfinished and self.onfinished_global:
            onfinished = self.onfinished_global
        if isinstance(options_dict, dict):
            for key, value in self.session_params.items():
                if key not in options_dict and key not in self.global_param_list:
                    options_dict.update({key:value})
        return method, onfinished, hdrs, options_dict
    
    def get(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'GET', onfinished, hdrs, kargs)
    
    def post(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'POST', onfinished, hdrs, kargs)
        
    def head(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'HEAD', onfinished, hdrs, kargs)
    
    def put(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'PUT', onfinished, hdrs, kargs)
        
    def delete(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'DELETE', onfinished, hdrs, kargs)
        
    def options(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'OPTIONS', onfinished, hdrs, kargs)
        
    def patch(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'PATCH', onfinished, hdrs, kargs)
        
    def crawl(self, urls, onfinished=None, hdrs=None, **kargs):
        method =kargs.get('method')
        if not method:
            method = 'CRAWL'
        url_obj = []
        depth = kargs.get('depth')
        if not isinstance(depth, int):
            depth = 0
        if isinstance(urls, list):
            url_obj = [URL(i, depth) for i in urls]
        else:
            url_obj.append(URL(urls, depth))
        return self.__build_tasks__(url_obj, method, onfinished, hdrs, kargs)
    
    def function(self, urls, *args, onfinished=None):
        self.__build_tasks__(urls, 'FUNCTION', onfinished, None, args)
        
    def function_add(self, urls, *args, onfinished=None):
        length_new = len(self.tasks_completed)
        task_list = [urls, onfinished, None, 'FUNCTION', args, length_new]
        length = len(self.tasks)
        self.tasks.update({length:task_list})
        self.tasks_completed.update({length_new:[False, urls]})
        if self.tasks_remaining() < self.max_requests:
            self.tasks.update({length:task_list})
        else:
            self.task_queue.append(task_list)
            logger.info('queueing task')
    
    def add(self, urls, onfinished=None, hdrs=None, method=None, **kargs):
        if self.session_params:
            global_params = [method, hdrs, onfinished, kargs]
            method, onfinished, hdrs, kargs = self.__set_session_params__(*global_params)
        if isinstance(urls, str):
            length = len(self.tasks)
            length_new = len(self.tasks_completed)
            self.tasks_completed.update({length_new:[False, urls]})
            task_list = [urls, onfinished, hdrs, method, kargs, length_new]
            if self.tasks_remaining() < self.max_requests:
                self.tasks.update({length:task_list})
            else:
                self.task_queue.append(task_list)
                logger.info('queueing task')
                
    def __start_non_block_loop_old__(self, tasks_dict, loop):
        asyncio.set_event_loop(loop)
        if not self.sem:
            self.sem = asyncio.Semaphore(self.max_requests, loop=loop)
        tasks = []
        for key, val in tasks_dict.items():
            #url, onfinished, hdrs, method, kargs, length = val
            tasks.append(asyncio.ensure_future(self.__start_fetching__(*val, loop)))
        logger.debug('starting {} tasks in single loop'.format(len(tasks_dict)))
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

    def __start_non_block_loop__(self, tasks_dict, loop):
        asyncio.set_event_loop(loop)
        if not self.sem:
            self.sem = asyncio.Semaphore(self.max_requests, loop=loop)
        for key, val in tasks_dict.items():
            asyncio.ensure_future(self.__start_fetching__(*val, loop))
        loop.run_forever()
        
    def start(self, task_dict=None, queue=False):
        if self.group_task and not queue:
            task_dict = self.tasks
        if (not self.loop and task_dict) or (task_dict and self.old_method):
            if self.old_method:
                loop = asyncio.new_event_loop()
            else:
                self.loop = asyncio.new_event_loop()
            if self.old_method:
                loop_thread = Thread(target=self.__start_non_block_loop_old__, args=(task_dict, loop))
            else:
                loop_thread = Thread(target=self.__start_non_block_loop__, args=(task_dict, self.loop))
            self.loop_nonblock_list.append(loop_thread)
            self.loop_nonblock_list[len(self.loop_nonblock_list)-1].start()
        elif task_dict:
            for key, val in task_dict.items():
                self.loop.create_task(self.__start_fetching__(*val, self.loop))
            logger.info('queue = {}'.format(queue))
    
    def __update_hdrs__(self, hdrs, netloc):
        if hdrs:
            hdr_cookie = hdrs.get('Cookie')
        else:
            hdr_cookie = None
        cookie = self.cookie_session.get(netloc)
        if cookie and not hdr_cookie and hdrs:
            hdrs.update({'Cookie':cookie})
        elif cookie and hdr_cookie and hdrs:
            if hdr_cookie.endswith(';'):
                new_cookie = hdr_cookie + cookie
            else:
                new_cookie = hdr_cookie + ';' + cookie
            hdrs.update({'Cookie':new_cookie})
        return hdrs
    
    def __request_preprocess__(self, url, hdrs, method, kargs):
        n = urlparse(url)
        netloc = n.netloc
        old_time = self.tasks_timing.get(netloc)
        wait_time = kargs.get('wait')
        session = kargs.get('session')
        if session:
            hdrs = self.__update_hdrs__(hdrs, netloc)
        if old_time and wait_time:
            time_diff = time.time() - old_time
            while(time_diff < wait_time):
                logger.info('waiting in queue..{} for {}s'.format(netloc, wait_time))
                time.sleep(wait_time)
                time_diff = time.time() - self.tasks_timing.get(netloc)
        self.tasks_timing.update({netloc:time.time()})
        kargs.update({'log':self.log})
        return session, netloc
    
    async def __request_preprocess_aio__(self, url, hdrs, method, kargs):
        n = urlparse(url)
        netloc = n.netloc
        old_time = self.tasks_timing.get(netloc)
        wait_time = kargs.get('wait')
        session = kargs.get('session')
        if session:
            hdrs = self.__update_hdrs__(hdrs, netloc)
        if old_time and wait_time:
            time_diff = time.time() - old_time
            while(time_diff < wait_time):
                logger.info('waiting in queue..{} for {}s'.format(netloc, wait_time))
                await asyncio.sleep(wait_time)
                time_diff = time.time() - self.tasks_timing.get(netloc)
        self.tasks_timing.update({netloc:time.time()})
        kargs.update({'log':self.log})
        return session, netloc
    
    def __update_session_cookies__(self, req_obj, netloc):
        old_cookie = self.cookie_session.get(netloc)
        new_cookie = req_obj.session_cookies
        cookie = old_cookie
        if new_cookie and old_cookie:
            if new_cookie not in old_cookie:
                cookie = old_cookie + ';' + new_cookie
        elif not new_cookie and old_cookie:
            pass
        elif new_cookie and not old_cookie:
            cookie = new_cookie
        if cookie:
            self.cookie_session.update({netloc:cookie})
        
    def __finished_task_postprocess__(self, session, netloc,
                                      onfinished, task_num,
                                      url, backend, loop,
                                      crawl, crawl_object,
                                      url_obj, result):
        if self.old_method:
            self.lock.acquire()
            try:
                self.task_counter += 1
            finally:
                self.lock.release()
        else:
            self.task_counter += 1
        self.tasks_completed.update({task_num:[True, url]})
        if session and result and netloc:
            self.__update_session_cookies__(result, netloc)
        logger.info('\ncompleted: {}\n'.format(self.task_counter))
        if self.task_queue:
            if self.old_method:
                task_list = self.task_queue.popleft()
                task_dict = {'0':task_list}
                self.start(task_dict, True)
                logger.info('\nstarting--queued--task\n')
            else:
                task_count = len(self.task_queue)
                for task_list in self.task_queue:
                    self.loop.create_task(self.__start_fetching__(*task_list, self.loop))
                self.task_queue.clear()
                logger.info('\nAll remaining {} tasks given to event loop\n'
                            .format(task_count))
                logger.info('\nTask Queue now empty\n')
        if onfinished:
            logger.info('arranging callback, task {} {}'
                        .format(task_num, url))
            onfinished(task_num, url, result)
            logger.info('callback completed, task {} {}'
                        .format(task_num, url))
        if crawl and crawl_object and result:
            if not crawl_object.crawl_dict.get(url):
                crawl_object.crawl_dict.update({url:True})
                if result and result.url:
                    if url != result.url:
                        crawl_object.crawl_dict.update({result.url:True})
            if result.html and result.out_file:
                out_file = result.out_file
                if os.path.isfile(out_file) and not result.binary:
                    with open(out_file, mode='r', encoding='utf-8') as fd:
                        result.html = fd.read()
            crawl_object.start_crawling(result, url_obj, session)
        if not self.old_method:
            if self.tasks_remaining() == 0 and not self.loop_forever:
                self.loop.stop()
                self.loop = None
                self.sem = None
                logger.info('All Tasks Finished: closing loop')
                    
    async def __start_fetching__(self, url_obj, onfinished, hdrs,
                                 method, kargs, task_num, loop):
        async with self.sem:
            
            if isinstance(url_obj, URL):
                url = url_obj.url
            else:
                url = url_obj
            session = None
            netloc = None
            crawl_object = None
            crawl = False
            if method in ['CRAWL', 'CRAWL_CHILDREN']:
                if method == 'CRAWL':
                    all_domain = kargs.get('all_domain')
                    domains_allowed = kargs.get('domains_allowed')
                    depth_allowed = kargs.get('depth_allowed')
                    crawl_object = CrawlObject(self, url_obj, onfinished,
                                               all_domain, domains_allowed,
                                               depth_allowed)
                    self.crawler_dict.update({url_obj:crawl_object})
                else:
                    crawl_object = kargs.get('crawl_object')
                crawl = True
                method = 'GET'
                
            if isinstance(kargs, dict):
                backend = kargs.get('backend')
                if not backend:
                    backend = self.backend
                mp = kargs.get('multiprocess')
                if mp:
                    workers = kargs.get('max_requests')
                    if not workers:
                        workers = self.max_requests
                    if not self.executor_process:
                        self.executor_process = ProcessPoolExecutor(max_workers=workers)
                    executor = self.executor_process
                    logger.info('using multiprocess with max_workers={}'
                                .format(workers))
                else:
                    executor = self.executor
            else:
                backend = self.backend
                executor = self.executor
            logger.info('using backend: {} for url : {}'.format(backend, url))
            if backend == 'urllib' and isinstance(url, str):
                logger.info('\nRequesting url: {}\n'.format(url))
                session, netloc = await self.__request_preprocess_aio__(url, hdrs, method, kargs)
                future = loop.run_in_executor(executor, get_request,
                                              backend, url, hdrs, method,
                                              kargs)
                
                response = await future
            elif backend == 'aiohttp' and isinstance(url, str):
                session, netloc = await self.__request_preprocess_aio__(url, hdrs, method, kargs)
                req = None
                jar = None
                auth_basic = None
                cookie_unsafe = kargs.get('cookie_unsafe')
                if cookie_unsafe:
                    jar = aiohttp.CookieJar(unsafe=True)
                auth = kargs.get('auth')
                if auth:
                    auth_basic = aiohttp.BasicAuth(auth[0], auth[1])
                aio = aiohttp.ClientSession(cookie_jar=jar, auth=auth_basic, loop=loop)
                async with aio:
                    try:
                        response = await self.__fetch_aio__(url, aio, hdrs, method, kargs)
                    except Exception as err:
                        logger.error(err)
                        response = Response(url, error=str(err), method=method)
            elif backend == 'function' or not isinstance(url, str):
                future = loop.run_in_executor(executor,
                                              complete_function_request,
                                              url, kargs)
                response = await future
            
            self.__finished_task_postprocess__(session, netloc, onfinished,
                                               task_num, url, backend, loop,
                                               crawl, crawl_object, url_obj,
                                               response)
            
    async def __fetch_aio__(self, url, session, hdrs, method, kargs):
        req = RequestObjectAiohttp(url, hdrs, method, kargs)
        req_obj = await req.process_aio_request(session)
        return req_obj
        

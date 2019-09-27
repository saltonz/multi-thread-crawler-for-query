import datetime
import threading
import time
import re
import socket
import logging

from queue import Queue, PriorityQueue
from pybloom_live import ScalableBloomFilter
from threading import RLock
from bs4 import BeautifulSoup
from common.database import Database
from data.url import Url
from ssl import SSLError
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser


# initialize the lock for hash map
dict_lock = RLock()

# initialize the lock for site_count_map
site_lock = RLock()


class Crawler(object):
    def __init__(self, seed_list, _id, max_num):
        self.id = _id
        self.seed_list = seed_list
        self.max_num = max_num
        self.depth = 2
        self.count = 0
        socket.setdefaulttimeout(2)

    def __repr__(self):
        return "<Crawler {}>".format(self.id)

    @classmethod
    def get_crawler(cls, seed_list, _id, max_num):
        return cls(seed_list, _id, max_num)

    def start(self):
        """
        1. initilize queue
        2. get all the urls in the queue
        3. new urls added to the priority queue (more novel if encountered more times)
        4. transport from pq to queue
        5. next level iteration
        :return:
        """
        start_time = datetime.datetime.now()

        # initialize queue, hash map and priority queue
        bfs_queue = PriorityQueue()
        rank_queue = Queue()
        hash_map = {}
        site_count_map = {}

        # initialize the queue for the first time
        for seed in self.seed_list:
            bfs_queue.put(Url.get_url(60, seed, 1))
            hash_map[seed] = 1

        # initialize the lock for count
        count_queue = Queue()
        count_queue.put(0)
        global_count = 0

        # initialize the bloom filter
        bloom_filter = ScalableBloomFilter(initial_capacity=10000, error_rate=0.001,
                                           mode=ScalableBloomFilter.LARGE_SET_GROWTH)

        # main loop of crawler
        while global_count < self.max_num:
            print("Iteration Started")

            # start new threads to download pages and add url object to bfs_queue and rank_queue
            thread_pool = []
            temp_size = bfs_queue.qsize()
            if temp_size < 500:
                while not bfs_queue.empty():
                    temp_url = bfs_queue.get()
                    if temp_url.url not in bloom_filter:
                        bloom_filter.add(temp_url.url)
                        new_thread = Download(temp_url, bfs_queue, count_queue,
                                              rank_queue, hash_map, site_count_map, self.max_num)
                        thread_pool.append(new_thread)
                        new_thread.start()
            else:
                while bfs_queue.qsize() > temp_size/2 and len(thread_pool) < 2000:
                    temp_url = bfs_queue.get()
                    if temp_url.url not in bloom_filter:
                        new_thread = Download(temp_url, bfs_queue, count_queue,
                                              rank_queue, hash_map, site_count_map, self.max_num)
                        thread_pool.append(new_thread)
                        bloom_filter.add(temp_url.url)
                        new_thread.start()

            for thread in thread_pool:
                thread.join()

            # Start rank
            rank_thread_pool = []
            print("Start ranking")

            while not rank_queue.empty():
                """
                new_thread = Rank(rank_queue.get(), hash_map, site_count_map)
                rank_thread_pool.append(new_thread)
                new_thread.start()
                """
                url = rank_queue.get()
                splited_url = url.url.split('/')
                site = splited_url[2]

                # Use the times of a page occurrences in the sub graph to calculate the priority score
                dict_lock.acquire()
                try:
                    if url.url not in hash_map:
                        hash_map[url.url] = 1
                    else:
                        hash_map[url.url] = hash_map[url.url] + 1
                    if hash_map[url.url] > 20:
                        url.set_priority(url.priority + 1)
                    else:
                        url.set_priority(url.priority + 5)
                finally:
                    dict_lock.release()

                # Use the times of the same site appeared to calculate the novelty score.
                site_lock.acquire()
                try:
                    if site in site_count_map:
                        if site_count_map[site] > 20:
                            url.set_priority(url.priority - 4)
                        else:
                            url.set_priority(url.priority - 2)
                finally:
                    site_lock.release()

            for thread in rank_thread_pool:
                thread.join()

            global_count = count_queue.get()
            count_queue.put(global_count)
            time.sleep(1)

        # Print the statistics
        end_time = datetime.datetime.now()
        print("Crawler started from:   ", start_time)
        print("Crawler finished in:    ", end_time)
        print("Time Consumed: ", end_time - start_time)
        print("Number of Sites crawled: ", len(site_count_map))
        print("Number of pages crawled: ", self.max_num)


class Download(threading.Thread):
    def __init__(self, url, work_queue, count_queue, rank_queue, hash_map, site_count_map, max_num):
        threading.Thread.__init__(self)
        self.url = url
        self.work_queue = work_queue
        self.count_queue = count_queue
        self.rank_queue = rank_queue
        self.hash_map = hash_map
        self.site_count_map = site_count_map
        self.max_num = max_num

    def run(self):
        Download.down_url(self.url, self.work_queue, self.count_queue,
                          self.rank_queue, self.hash_map, self.site_count_map, self.max_num)

    @staticmethod
    def down_url(url, work_queue, count_queue, rank_queue, hash_map, site_count_map, max_num):
        # check the global id
        temp_count = count_queue.get()
        count_queue.put(temp_count)
        if temp_count > max_num:
            return

        rp = RobotFileParser()
        split_url = url.url.split('/')
        robot_url = split_url[0] + "//" + split_url[2]
        rp.set_url(robot_url)
        try:
            # check robot.txt
            try:
                rp.read()
                user_agent = 'GoodCrawler'
                if not rp.can_fetch(user_agent, url.url):
                    return
            except Exception:
                pass
                # logging.info(Exception)

            # download page
            response = urlopen(url.url, timeout=2)
            html = response.read().decode('utf-8')
            response_code = response.getcode()
            size = response.info()['Content-Length']
            response.close()

            # parse
            soup = BeautifulSoup(html, features='lxml')
            if soup.find('h1') is None:
                title = "default"
            else:
                title = soup.find('h1').get_text()

            # upgrade the global id
            temp_count = count_queue.get()
            count_queue.put(temp_count + 1)
            if temp_count > max_num:
                return

            # set url's value and save to MongoDB
            url.set_time(datetime.datetime.now())
            url.set_id(temp_count)
            url.set_title(title)
            url.set_reponse_code(response_code)
            url.set_size(size)

            print('count: ', temp_count, '    depth:', url.depth, "    priority:", url.priority, title,
                  '    url: ', url.url, '   size:', size, '  Response_Code:',
                  response_code, '    time: ', url.get_time())
            Database.insert("test", url.json())

            sub_urls = soup.find_all("a", {"href": re.compile("https://.*?")})

            # update the subgraph of network discovered to bfs Queue and Rank Queue
            for url_string in sub_urls:
                temp_url = Url.get_url(50, url_string["href"], url.depth + 1)
                temp_site = url_string["href"].split('/')[2]
                site_lock.acquire()
                try:
                    if temp_site not in site_count_map:
                        site_count_map[temp_site] = 1
                    else:
                        site_count_map[temp_site] += 1
                finally:
                    site_lock.release()
                dict_lock.acquire()
                try:
                    hash_map[temp_url.url] = 1
                finally:
                    dict_lock.release()
                rank_queue.put(temp_url)
                work_queue.put(temp_url)

            # synchronize data to the site-count map and hash map
            site_lock.acquire()
            try:
                if split_url[2] not in site_count_map:
                    site_count_map[split_url[2]] = 1
                else:
                    site_count_map[split_url[2]] += 1
            finally:
                site_lock.release()

            dict_lock.acquire()
            try:
                hash_map.pop(url.url)
            finally:
                dict_lock.release()
        except socket.gaierror:
            # logging.info("Encountered gai error")
            pass
        except HTTPError as err:
            # logging.info("Encountered exception on url: " + url.url)
            # logging.info("Error Info: ", err)
            pass
        except SSLError as err:
            # logging.info("Encountered SSL Error:", err)
            pass
        except Exception as e:
            # print(url.url, e)
            pass


class Rank(threading.Thread):
    def __init__(self, url, hash_map, site_count_map):
        threading.Thread.__init__(self)
        self.url = url
        self.hash_map = hash_map
        self.site_count_map = site_count_map

    def run(self):
        Rank.rank(self.url, self.hash_map, self.site_count_map)

    @staticmethod
    def rank(url, hash_map, site_count_map):
        splited_url = url.url.split('/')
        site = splited_url[2]
        dict_lock.acquire()
        try:
            if url.url not in hash_map:
                hash_map[url.url] = 1
            else:
                hash_map[url.url] = hash_map[url.url] + 1
                if hash_map[url.url] > 20:
                    url.set_priority(url.priority + 1)
                else:
                    url.set_priority(url.priority + 5)
        finally:
            dict_lock.release()

        site_lock.acquire()
        try:
            if site in site_count_map:
                if site_count_map[site] > 20:
                    url.set_priority(url.priority - 4)
                else:
                    url.set_priority(url.priority - 2)
        finally:
            site_lock.release()




import socket
import threading
from crawler.download import Download

from queue import Queue, PriorityQueue
from data.url import Url
from pybloom_live import ScalableBloomFilter
from threading import RLock

# initialize the lock for hash map
dict_lock = RLock()


class Crawler(object):
    def __init__(self, seed_list, _id, max_depth):
        self.id = _id
        self.seed_list = seed_list
        self.max_depth = max_depth
        self.depth = 2
        self.count = 0
        socket.setdefaulttimeout(3)

    def __repr__(self):
        return "<Crawler {}>".format(self.id)

    @classmethod
    def get_crawler(cls, seed_list, _id, max_depth):
        return cls(seed_list, _id, max_depth)

    def start(self):
        """
        1. initilize queue
        2. get all the urls in the queue
        3. new urls added to the priority queue (more novel if encountered more times)
        4. transport from pq to queue
        5. next level iteration
        :return:
        """
        # initialize queue, hash map and priority queue
        bfs_queue = Queue()
        next_priority_queue = PriorityQueue()
        next_hash_table = {}

        # initialize the queue for the first time
        for seed in self.seed_list:
            bfs_queue.put(Url.get_url(50, seed, 1))

        # initialize the lock for count
        count_queue = Queue()
        count_queue.put(0)

        # initialize the bloom filter
        bloom_filter = ScalableBloomFilter(initial_capacity=10000, error_rate=0.001,
                                           mode=ScalableBloomFilter.LARGE_SET_GROWTH)

        # main loop of crawler
        while self.depth < self.max_depth:
            print("Iteration Started, num = ", self.depth)
            next_hash_table.clear()
            for i in range(bfs_queue.qsize()):
                url_input_list = []
                for j in range(500):
                    if bfs_queue.empty():
                        break
                    url_input_list.append(bfs_queue.get())
                    i += 1

                # Start new threads to download pages
                url_queue = Queue()
                thread_pool = []
                for url in url_input_list:
                    if url.url not in bloom_filter:
                        thread_pool.append(Download(url,  url_queue, count_queue))
                        thread_pool[-1].start()
                        bloom_filter.add(url.url)

                # for thread in thread_pool:
                #    thread.start()

                for thread in thread_pool:
                    thread.join()

                rank_thread_pool = []
                print("Start ranking")
                while not url_queue.empty():
                    crawled_url = url_queue.get()
                    if crawled_url not in bloom_filter:
                        rank_thread_pool.append(Rank(crawled_url, next_hash_table,
                                                     next_priority_queue, bfs_queue, self.depth))
                        rank_thread_pool[-1].start()
                        """
                        if crawled_url not in next_hash_table:
                            next_hash_table[crawled_url['href']] = 50
                        else:
                            next_hash_table[crawled_url['href']] = next_hash_table[crawled_url['href']] + 1
                        if len(next_hash_table) >= 500:
                            Crawler.load_from_hash_table_to_priority_queue(next_hash_table, next_priority_queue, self.depth)
                            Crawler.load_from_priority_queue_to_queue(bfs_queue, next_priority_queue)
                        """

                for thread in rank_thread_pool:
                    thread.join()

            Crawler.load_from_hash_table_to_priority_queue(next_hash_table, next_priority_queue, self.depth)
            Crawler.load_from_priority_queue_to_queue(bfs_queue, next_priority_queue)
            Crawler.depth = self.depth + 1

    @staticmethod
    def load_from_hash_table_to_priority_queue(hash_table, priority_queue, depth):
        dict_lock.acquire()
        try:
            for element in hash_table:
                priority_queue.put(Url.get_url(hash_table[element], element, depth))
            hash_table.clear()
        finally:
            dict_lock.release()

    @staticmethod
    def load_from_priority_queue_to_queue(bfs_queue, next_priority_queue):
        dict_lock.acquire()
        try:
            while not next_priority_queue.empty():
                bfs_queue.put(next_priority_queue.get())
        finally:
            dict_lock.release()


class Rank(threading.Thread):
    def __init__(self, url, next_hash_table, next_priority_queue, bfs_queue, depth):
        threading.Thread.__init__(self)
        self.url = url
        self.next_hash_table = next_hash_table
        self.next_priority_queue = next_priority_queue
        self.bfs_queue = bfs_queue
        self.depth = depth

    def run(self):
        Rank.rank(self.url, self.next_hash_table, self.next_priority_queue, self.bfs_queue, self.depth)

    @staticmethod
    def rank(url, next_hash_table, next_priority_queue, bfs_queue, depth):
        dict_lock.acquire()
        try:
            if url not in next_hash_table:
                next_hash_table[url['href']] = 50
            else:
                next_hash_table[url['href']] = next_hash_table[url['href']] + 1
            if len(next_hash_table) >= 500:
                Crawler.load_from_hash_table_to_priority_queue(next_hash_table, next_priority_queue, depth)
                Crawler.load_from_priority_queue_to_queue(bfs_queue, next_priority_queue)
        finally:
            dict_lock.release()




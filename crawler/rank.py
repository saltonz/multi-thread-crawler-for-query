import threading
from crawler.crawler import Crawler


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
        if url not in next_hash_table:
            next_hash_table[url['href']] = 50
        else:
            next_hash_table[url['href']] = next_hash_table[url['href']] + 1
        if len(next_hash_table) >= 500:
            Crawler.load_from_hash_table_to_priority_queue(next_hash_table, next_priority_queue, depth)
            Crawler.load_from_priority_queue_to_queue(bfs_queue, next_priority_queue)


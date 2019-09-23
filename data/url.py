import time


class Url(object):
    def __init__(self, priority, url, depth):
        self.priority = priority
        self.url = url
        self.depth = depth
        self.time_stamp = time.localtime()
        self.id = 0
        self.title = ""

    def __repr__(self):
        return "<Crawler {}>".format(self.url)

    def __lt__(self, other):
        return self.priority > other.priority

    @classmethod
    def get_url(cls, priority, url, depth):
        return cls(priority, url, depth)

    def get_time(self):
        return self.time_stamp

    def set_id(self, _id):
        self.id = _id

    def set_time(self, time_stamp):
        self.time_stamp = time_stamp

    def set_title(self, title):
        self.title = title

    def json(self):
        return {
            "priority": self.priority,
            "url": self.url,
            "depth": self.depth,
            "timestamp": self.time_stamp,
            "id": self.id,
            "title": self.title,
        }

import datetime
import threading
import re
import socket
import logging
from bs4 import BeautifulSoup
from common.database import Database
from data.url import Url
from ssl import SSLError
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser


class Download(threading.Thread):
    def __init__(self, url, work_queue, count_queue):
        threading.Thread.__init__(self)
        self.url = url
        self.work_queue = work_queue
        self.count_queue = count_queue

    def run(self):
        Download.down_url(self.url, self.work_queue, self.count_queue)

    @staticmethod
    def down_url(url, work_queue, count_queue):
        rp = RobotFileParser()
        split_url = url.url.split('/')
        robot_url = split_url[0] + "//" + split_url[2]
        rp.set_url(robot_url)
        try:
            # check robot.txt
            rp.read()
            user_agent = 'GoodCrawler'
            if not rp.can_fetch(user_agent, url.url):
                logging.info("url.url is not allowed to crawl by robot.txt")
                return

            # download page
            response = urlopen(url.url)
            html = response.read().decode('utf-8')
            response.close()
            soup = BeautifulSoup(html, features='lxml')
            title = soup.find('h1').get_text()

            # upgrade the global id
            temp_count = count_queue.get()
            count_queue.put(temp_count + 1)
            print(temp_count)

            # set url's value and save to MongoDB
            url.set_time(datetime.datetime.now())
            url.set_id(temp_count)
            url.set_title(title)

            print(url.depth, title, '    url: ', url.url, '    time: ', url.get_time())
            Database.insert("test", url.json())

            sub_urls = soup.find_all("a", {"href": re.compile("https://.*?")})
            for url_string in sub_urls:
                work_queue.put(url_string)

        except socket.gaierror:
            logging.info("Encountered gai error")
        except HTTPError as err:
            logging.info("Encountered exception on url: " + url.url)
            logging.info("Error Info: ", err)
        except SSLError as err:
            logging.info("Encountered SSL Error:", err)
        except Exception as e:
            logging.info(e)


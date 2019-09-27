__author__ = "Salton"

import sys
import socket
from seed.seed import Seed
from crawler.crawler import Crawler
from common.database import Database

if len(sys.argv) <= 1:
    print('No query input')
    exit()
if len(sys.argv) > 2:
    print('Too many parameters, please run as [python run.py "your query"]')
    exit()
query = sys.argv[1]

Database.initialize()
socket.setdefaulttimeout(2)
# Generate seeds
seed = Seed.get_seed(query)
seed.generate_url_seeds_from_google()
urlList = seed.get_url_seed_list()
for url in urlList:
    print(url)

# Start Crawler
crawler = Crawler.get_crawler(urlList, 1, 20000)
crawler.start()



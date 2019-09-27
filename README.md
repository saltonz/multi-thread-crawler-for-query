## Document for assignment1 of WSE - multi thread crawler

### Metrics

* **Priority**: related to the uncrawled graph - which one has more hyperline point to or have more score on PageRank
* **Novelty**: If a page on a 
* **Output**: A log with a list of all visited **URLs** in the order they are visited, together with the information such as **size of the page** and **depth** of each page, **priority score** of the page when it was crawled and the **timestamp** of the download.

### Usage

```bash
python run.py "[Your query]"
```

### Env

Python 3.7

```
requests==2.8.0
BeautifulSoup4==4.8.0
lxml==4.4.1
pybloom_live==3.0.0
pymongo==3.9.0
```



### Key Methods:

1. **Google API**
    * Used to generate the seed of our crawling process
2. **Bloom Filter**
    * Used to make sure the same url won't be crawled twice. Better efficiency than HashMap when number of the result is large, with a possibility of mis-check.
    To control the mis-check rate, used scalable bloom Filter
3. **Hash Map**
    * To identify whether a url is already in the priority queue
4. **Priority Queue**
    * To dynamicly update the priority of a page during the process of BFS.
5. **Robot File Parser**
    * According to https://www.robotstxt.org/robotstxt.html , the sites don't want to be crawled may add this robots.txt on their site. So robot File parser is used to identify the sites don't want to be crawled.
6. **Multi Thread Processing**
    * The bottleneck of web crawler is network IO and local file IO, when facing such IO operations, use multi thread method to accomplish faster crawling speed.
7. **Thread Pool**
    * Lots of threads will be created and destroyed frequently, with thread pool we can save time on process create and destroy for better efficiency.
    * During the test we found that the threadPoolExecuter doesn't work well with our logic
8. **Asyncio**
    * The main bottleneck of crawler is network I/O, and asynchronous computing can fulfill the requirement that a single thread working with many coroutines.
9. **MongoDB**
    * fast method to store the pages encountered.
    * better organization of each urls' information.

### Logic

(To be completed)

Crawl -> Parse -> Store -> Rank 

Use multi threads method to accelerate. (Tested 3-20 pages per second.)

Parse: Use Beautiful soup and regular expression to filter out the links

Store: after parse, store the info to MongoDB

Rank: at the end of every iteration, calculate the rank of pages in un-crawled subgraph and update their priority in the Priority Queue



### Experiment

```
Paris Texas
Crawler started from:    2019-09-26 19:21:18.958819
Crawler finished in:     2019-09-26 20:38:39.886982
Time Consumed:  1:17:20.928163
Number of Sites encountered:  7876
Number of pages crawled:  20000

brooklyn parks
Crawler started from:    2019-09-27 02:36:56.965808
Crawler finished in:     2019-09-27 03:10:41.745376
Time Consumed:  0:33:44.779568
Number of Sites encountered:  167727
Number of pages crawled:  20000
```


## Document for assignment1 of WSE - multi thread crawler

### Metrics

* **Priority**: related to the uncrawled graph - which one has more hyperline point to or have more score on PageRank

* **Novelty**: If a page on a 

* **Output**: A log with a list of all visited **URLs** in the order they are visited, together with the information such as **size of the page** and **depth** of each page, **priority score** of the page when it was crawled and the **timestamp** of the download.

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

### Logic

### 
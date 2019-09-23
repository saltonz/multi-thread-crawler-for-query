import requests
import re
from data.url import Url


class Seed(object):
    def __init__(self, params):
        self.urlList = []
        self.params = {
            "q": params
        }

    def __repr__(self):
        return "<Seed {}>".format(self.urlList)

    @classmethod
    def get_seed(cls, params):
        return cls(params)

    def generate_url_seeds_from_google(self):
        google_url = "http://www.google.com/search"
        response = requests.get(google_url, params=self.params)
        htmls = re.findall(r'<a href="/url\?q.*?>.*?</a>', response.text)

        for html in htmls:
            targetUrl = re.findall(r'https://.*?&', html)
            if len(targetUrl) == 0:
                print("Couldn't generate query seed from google, please try other query words. Or try again later")
            else:
                self.urlList.append(targetUrl[0][:-1])

        self.urlList.pop(-1)

    def generate_url_seeds_from_bing(self):
        bing_url = "https://www.bing.com/search"
        response = requests.get(bing_url, params=self.params)
        htmls = re.findall(r'<a.*?>.*?</a>', response.text)

        for html in htmls:
            self.urlList.append(html)

    def get_url_seed_list(self):
        return self.urlList




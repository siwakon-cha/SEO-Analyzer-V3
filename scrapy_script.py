
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from urllib.parse import urlparse
from scrapy.exceptions import CloseSpider
from seoanalyzer.page import Page
import sys
from datetime import datetime
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
from collections import Counter
import requests
import re

try:
    url = sys.argv[1]
    max_pages = int(sys.argv[2])
except:
    url = "https://www.thaiprintshop.com/"
    max_pages = 10

cred = credentials.Certificate("seo-luca-firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://seo-luca-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

parsed_url = urlparse(url)
subdomain = parsed_url.netloc.replace('.','_')
print(subdomain)

current_time = str(time.time()).replace(".", "_")

def get_pagespeed_metrics(url):
    api_key = "AIzaSyC7LzYcbuKiFcgGbDOh_abbGIwy4C4Vcks"  # Replace with your actual API key
    endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
    
    try:
        response = requests.get(endpoint)
        data = response.json()
        
        if 'lighthouseResult' in data:
            metrics = data['lighthouseResult']['audits']
            lcp = float(metrics['largest-contentful-paint']['numericValue'])
            fid = float(metrics['max-potential-fid']['numericValue'])
            cls = float(metrics['cumulative-layout-shift']['numericValue'])
            
            return lcp, fid, cls
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def remove_number_keys(counter):
    number_keys = [key for key in counter.keys() if str(key).replace(" ", '').isdigit()]
    for key in number_keys:
        del counter[key]
    return counter

class MySpider(Spider):
    name = 'my_spider'
    start_urls = [url]  # Replace with the URL of the website you want to scrape
    custom_settings = {
        'DOWNLOAD_FAIL_ON_DATALOSS': False,
        'LOG_ENABLED': False,
        'ROBOTSTXT_OBEY' : False,
    }
    max_pages = max_pages
    pages_number = 0
    # max_depth = 6  # Maximum depth of crawling
    allowed_domains = []
    visited_urls = set()  # Set to keep track of visited URLs
    pages = []  # List to store text content of each page
    analyze_headings = True
    analyze_extra_tags = False
    keyword_counter = Counter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_domains = self.extract_domains()
        self.page_content = []
        # self.analyze_headings = 
        # self.analyze_extra_tags = analyze_extra_tags
            
    def extract_domains(self):
        domains = set()
        for url in self.start_urls:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if domain:
                domains.add(domain)
        return list(domains)

    def is_file_url(self, url):
        url_lower = url.lower()

        # Check if the URL ends with a string resembling a file extension
        if '.' in url_lower:
            last_segment = url_lower.rsplit('/', 1)[-1]
            extension = last_segment.rsplit('.', 1)[-1]
            if len(extension) <= 4 and extension.isalpha():
                return True
        
        return False
        
    def parse(self, response):
        
        page = Page(url=response.url, base_domain=self.start_urls[0],
            analyze_headings=self.analyze_headings,
            analyze_extra_tags=self.analyze_extra_tags)
                
        if page.parsed_url.netloc == page.base_domain.netloc:
            page.analyze(raw_html = response.text)
            data =  {'url': response.url,
                    'keywords': dict(remove_number_keys(page.wordcount).most_common(25)),
                    'bigrams': dict(remove_number_keys(page.bigrams).most_common(25)),
                    'trigrams': dict(remove_number_keys(page.trigrams).most_common(25)),
                    'warnings': {index: value for index, value in enumerate(page.warnings)}}
            self.pages.append(data)
            self.visited_urls.add(response.url)
            # db.reference(f'website_data/{subdomain}/webpage_analysis/{current_time}/{self.pages_number}').set(data)
            self.pages_number += 1
            self.keyword_counter.update(page.wordcount)
            
            if self.pages_number >= self.max_pages:
                raise CloseSpider('Condition met: Stopping spider')
            else:
                for link in page.links:
                    parsed_url = urlparse(response.url)
                    base_url = parsed_url.scheme + "://" + parsed_url.netloc
                    if link.startswith('/') or link.startswith('../'):
                        link = base_url+link
                    if self.pages_number < self.max_pages:
                        parsed_url = urlparse(link)
                        if parsed_url.netloc in self.allowed_domains:
                            if link.startswith('http') and link not in self.visited_urls and not self.is_file_url(link):
                                
                                yield response.follow(link, callback=self.parse)
                            
            
# Create a CrawlerProcess instance
process = CrawlerProcess()

# Start the crawling process with the spider class
process.crawl(MySpider)

# Run the process
process.start()

db.reference(f'website_data/{subdomain}/webpage_analysis/{current_time}').set(MySpider.pages)

time_ref = db.reference(f'website_data/{subdomain}/update_times')
existing_times = time_ref.get()
if existing_times:
    existing_times_list = list(existing_times)
else:
    existing_times_list = []
existing_times_list.append(current_time)
time_ref.set(existing_times_list)

print(url)
from backlinks_analysis import get_backlinks_df
output_dataframes, output_dict_data = get_backlinks_df(url)
db.reference(f'website_data/{subdomain}/backlinks_analysis/{current_time}').set(output_dict_data)

db.reference(f'website_data/{subdomain}/keywords_count').set({current_time: len(MySpider.keyword_counter.keys())})

from web_core_vitals import webcorevitals
test,score,fcp,si,lcp,tti,tbt,cls,date = webcorevitals([url])[0]
db.reference(f'website_data/{subdomain}/web_core_vitals').set({current_time: {'score': score, 'fcp': fcp, 'si': si, 'lcp': lcp, 'tti':tti, 'tbt': tbt, 'cls': cls}})
#!/bin/bash

scrapy crawl lse_crawler 
scrapy crawl file_downloader
scrapy crawl calendar_crawler
scrapy crawl lsesu_crawler
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class NaverCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    source = scrapy.Field()  # 신문사
    title = scrapy.Field()  # 제목
    url = scrapy.Field()  # 기사링크
    content = scrapy.Field()
    date = scrapy.Field()  # 날짜
    pass

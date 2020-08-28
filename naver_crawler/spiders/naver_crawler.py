# -*- coding: utf-8 -*-
import scrapy
import sys
from scrapy.spiders import Spider
from ..items import NaverCrawlerItem
import datetime
import time
import csv

class NaverSpider(scrapy.Spider):
    name = "naver"

    custom_settings = {
        'DOWNLOAD_TIMEOUT': 720
    }

    def start_requests(self):
        url_format = 'https://search.naver.com/search.naver?&where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_pge&sort=0&photo=0&field=0&reporter_article=&pd=3&ds='
        yield scrapy.Request(url=url_format, cookies={'news_office_checked' : '1018'}, callback=self.parse_page_num)   # 연합: 1001, 이데일리: 1018, 인포맥스: 2227
        del url_format


    def parse_page_num(self,response):
        page_urls = []

        # max_page = 221744 // 10 + 1      # 2016 : 221744 # 2017.01.31~12.31: 161121 #17.01.01 ~ 17.01.30: 18191  # 2015 : 249650  / 2014:149451 /
        #for term in range(0, 365, 1):   # 4627
        s_date = (datetime.date(2016, 1, 1)).strftime('%Y.%m.%d')
        s_from = s_date.replace('.', '')
        e_date = (datetime.date(2016, 1, 1) + datetime.timedelta(+365)).strftime('%Y.%m.%d')
        e_to = e_date.replace('.', '')
        date_page_url = response.url + s_date + '&de=' + e_date + '&docid=&nso=so:r,p:from' + s_from + 'to' + e_to + ',a:all&mynews=1&cluster_rank=63&start='

        total_num = response.xpath('//*[@id="main_pack"]/div[2]/div[1]/div[1]/span/text()').extract()[0].split(' ')[-1].replace(',', '')[:-1]
        max_page = (int(total_num) // 10) + 1

        for page in range(0, max_page, 1):
            page_url = date_page_url + str(page) + '1&refresh_start=0'
            page_urls.append(page_url)
        for page_url in page_urls:
            yield scrapy.Request(url=page_url, cookies={'news_office_checked' : '1018'}, callback=self.parse_page)
        del page_urls

    def parse_page(self, response):
        articles = response.xpath("//dd[@class='txt_inline']")
        urls = []
        infomax_urls = []
        for article in articles:
            if (article.xpath("./span[@class='_sp_each_source']/text()").get().strip() in ["연합뉴스", '이데일리']):
                article_ = article.xpath("./span[@class='_sp_each_source']/text()").get().strip()
                urls.extend((article.xpath("./a/@href").extract()))

            elif (article.xpath("./span[@class='_sp_each_source']/text()").get().strip() == "연합인포맥스"):
                infomax_url = response.xpath("//*[@id='main_pack']/div[2]/ul/li/dl/dt")
                infomax_urls.extend((infomax_url.xpath("./a/@href").extract()))

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'title':article_})
        del urls

        for infomax_url in infomax_urls:
            if 'news.einfomax.co.kr' in infomax_url:
                yield scrapy.Request(url=infomax_url, callback=self.parse_page_contents_infomax)
        del infomax_urls

    def parse(self, response):
        item = NaverCrawlerItem()
        item['url'] = response.url
        item['source'] = response.meta['title']
        item["title"] = response.xpath('//*[@id="articleTitle"]/text()').get()
        item['date'] = response.xpath('//*[@id="main_content"]/div[1]/div[3]/div/span/text()').getall()
        item['content'] = response.xpath("//div[@id='articleBodyContents']//text()").getall()
        self.log(item['url'])
        self.log(item['content'])
        yield item

    def parse_page_contents_infomax(self, response):
        item = NaverCrawlerItem()
        item['url'] = response.url
        item["source"] = '연합인포맥스'
        item["title"] = response.xpath('//*[@id="user-container"]/div[3]/header/div/div/text()').get()
        item["date"] = response.xpath('//*[@id="user-container"]/div[3]/header/section/div/ul/li[2]/text()').get()
        item["content"] = response.xpath('//*[@id="article-view-content-div"]/text()').getall()
        self.log(item['url'])
        self.log(item['content'])
        yield item
import scrapy
import time
from scrapy.http import HtmlResponse
import re
import datetime

from ..items import NaverCrawlerItem

class NaverSpider(scrapy.Spider):
    # 식별자 classifier
    name = "naver"
    # 크롤링 할 도메인
    # allowed_domains = ["naver.com", "http://news.einfomax.co.kr"]

    # 2005.01.01 크롤링 시작페이지 호출
    def start_requests(self):        
        start_url = 'https://search.naver.com/search.naver?where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_opt&sort=0&photo=0&field=0&reporter_article=&pd=3&ds=2005.01.01&de=2005.01.01&docid=&nso=so%3Ar%2Cp%3Afrom20050101to20050101%2Ca%3Aall&mynews=1&refresh_start=0&related=0'        
        # start_url = 'https://search.naver.com/search.naver?where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_opt&sort=0&photo=0&field=0&reporter_article=&pd=3&ds=2017.01.01&de=2017.01.01&docid=&nso=so%3Ar%2Cp%3Afrom20170101to20170101%2Ca%3Aall&mynews=1&refresh_start=0&related=0'        
        yield scrapy.Request(url=start_url, cookies={'news_office_checked' : '1001,1018,2227'}, callback=self.get_crawl_range, dont_filter=True)        
            

    # 2005.01.01 ~ 2017.12.31까지 1일씩 증가시켜가며, 이데일리, 연합뉴스, 연합인포맥스 기사를 선택 
    def get_crawl_range(self, response):
        # 시작일과 종료일 사이 며칠인지 구하는 코드
        # start_day = datetime.datetime(2005,1,1)
        # end_day = datetime.datetime(2017,12,31)
        # diff = end_day - start_day
        
        # 2005.01.01 ~ 2017.12.31까지 (총 4747일)
        # 총 246,852건
        
        # 2005.01.01만 테스트
        # for term in range(0, 1):
        for term in range(0, 4627):  # 3896
            date = (datetime.date(2005, 5, 1) + datetime.timedelta(+term)).strftime('%Y.%m.%d')
            url = 'https://search.naver.com/search.naver?&where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_pge&sort=0&photo=0&field=0&reporter_article=&pd=3&ds={0}&de={1}&docid=&nso=so:r,p:from{2}to{3},a:all&mynews=1&cluster_rank=14&start=1&refresh_start=10'.format(date, date, date.replace('.', ''), date.replace('.', ''))                
            yield scrapy.Request(url=url, cookies={'news_office_checked' : '1001,1018,2227'}, callback=self.per_page, dont_filter=True)                        
        
        
    # 페이지를 증가시켜가며 매 페이지에 속해있는 기사를 크롤링
    def per_page(self, response):
        # 해당 일자에 있는 기사의 총 수를 10으로 나눠 페이지 수 찾기
        tmp = response.xpath('//*[@id="main_pack"]/div[2]/div[1]/div[1]/span/text()').get()
        print('-----------------------------------------------------------------------------------------------')
        res = re.findall('/\s([0-9,]+)', tmp)
        res = res[0].replace(',', '')
        print(res)
        length = (int(res) // 10) + 1        
        print(length)       
        print('-----------------------------------------------------------------------------------------------')
        
        # 계산된 페이지수에 맞게 각각의 페이지를 호출
        for page in range(0, length):
            print("url : ", response.url)
            url = response.url.replace('&start=1', '&start='+str((10*int(page))+1))
            print("replaced_url : ", url)
            yield scrapy.Request(url=url, cookies={'news_office_checked' : '1001,1018,2227'}, callback=self.parse, dont_filter=True)           
        

    # 포맷이 다른 연합인포맥스의 기사를 골라내기 위한 작업
    def parse(self, response):
        # 해당 페이지 내에 있는 모든 li tag를 골라냄(10개의 기사가 있다면 li_tag는 10개가 있음)        
        li_tag = response.xpath('//*[@id="main_pack"]//div/ul/li/dl')
        # print('-----------------------------------------------------------------------------------------------------')
        # print('                    parse() call                  ', len(li_tag))
        # print(response.url)
        # print(li_tag)
        # print('-----------------------------------------------------------------------------------------------------')
        
        # 저널 이름에 따른 url 수집
        for li in li_tag :
            journal_name = li.xpath('./dd/span/text()').get()
            # print(journal_name)

            if journal_name == '연합뉴스':
                # print('연합뉴스')
                href = li.xpath('./dd/a/@href') 
                url = response.urljoin(href[0].extract())
                print(url)
                yield scrapy.Request(url, callback=self.parse_page_contents_yeonhap)
            elif journal_name == '이데일리':
                # print('이데일리')                
                href = li.xpath('./dd/a/@href') 
                url = response.urljoin(href[0].extract())
                print(url)
                yield scrapy.Request(url, callback=self.parse_page_contents_edaily)
            elif journal_name == '연합인포맥스':
            # else :
                # print('연합인포맥스')
                href = li.xpath('./dt/a/@href') 
                url = response.urljoin(href[0].extract())
                print(url)
                yield scrapy.Request(url, callback=self.parse_page_contents_infomax)


    # 이데일리 기사 포맷에 맞는 크롤링 수행
    def parse_page_contents_edaily(self, response):
        item = NaverCrawlerItem()
        item["journal_name"] = '이데일리'
        item["title"] = response.xpath('//*[@id="articleTitle"]/text()').get()
        item["date"] = response.xpath('//*[@id="main_content"]/div[1]/div[3]/div/span/text()').get()
        item["article"] = response.xpath('//*[@id="articleBodyContents"]/text()').getall()
        yield item


    # 이데일리 기사 포맷에 맞는 크롤링 수행
    def parse_page_contents_yeonhap(self, response):
        item = NaverCrawlerItem()
        item["journal_name"] = '연합뉴스'
        item["title"] = response.xpath('//*[@id="articleTitle"]/text()').get()
        item["date"] = response.xpath('//*[@id="main_content"]/div[1]/div[3]/div/span/text()').get()
        item["article"] = response.xpath('//*[@id="articleBodyContents"]/text()').getall()
        yield item


    # 이데일리 기사 포맷에 맞는 크롤링 수행
    def parse_page_contents_infomax(self, response):        
        item = NaverCrawlerItem()
        item["journal_name"] = '연합인포맥스'
        item["title"] = response.xpath('//*[@id="user-container"]/div[3]/header/div/div/text()').get()
        item["date"] = response.xpath('//*[@id="user-container"]/div[3]/header/section/div/ul/li[2]/text()').get()
        item["article"] = response.xpath('//*[@id="article-view-content-div"]/text()').getall()
        yield item
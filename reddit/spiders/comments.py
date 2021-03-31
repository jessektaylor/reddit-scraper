import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from selenium import webdriver
from shutil import which
from scrapy.selector import Selector
from selenium.webdriver.support.ui import WebDriverWait
import time 
from selenium.webdriver.common.by import By
import os
import json
import ast
from twisted.internet import reactor
from scrapy.utils.project import get_project_settings



class RedditSpider(scrapy.Spider):
    name = 'comments'
    allowed_domains = os.getenv('allowed_domains')
    start_urls = ast.literal_eval(os.getenv('start_url_list'))

    def __init__(self):
        path = which('chromedriver')
        print(path)
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('headless')
        options.add_argument('--disable-dev-shm-usage')     
        options.add_argument('--disable-extensions')   
        options.add_argument('--disable-gpu')
        options.add_argument('window-size=1200x600')
        self.driver = webdriver.Chrome(executable_path=path,options=options)
        self.driver.implicitly_wait(5)
        print(os.getenv('start_url'))
        self.driver.get(os.getenv('start_url')) 
        time.sleep(5)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)

        self.html = self.driver.page_source
        sel  = Selector(text=self.html)
        #get all valid links
        allPosts = sel.xpath(".//*[@id='SHORTCUT_FOCUSABLE_DIV']/div[2]/div/div/div/div[2]/div[3]/div[1]/div[4]/div")
        self.postsUrls = list()
        for post in allPosts:
            # check if the comment is promoted
            promoted = post.xpath(".//div[2]/div[1]/div/div[1]/span[1]/text()").get()
            if promoted != 'promoted' and promoted != None:
                postUrl =  post.xpath(".//div/div/div[2]/div/a/@href").get()
                self.postsUrls.append(postUrl)   

    def parse(self, response):
        base_url  = 'https://www.reddit.com'
        for i, url in enumerate(self.postsUrls):
            print(i, '  '+url)
       
        for postUrl in self.postsUrls:
            self.driver.get(base_url + postUrl)
            self.driver.maximize_window()
            time.sleep(5)
            html = self.driver.page_source
            self.sel  = Selector(text=html)
            values = {}
            values['postTitle'] = self.sel.xpath(".//h1/text()").get()
            values['postUserName'] = self.sel.xpath(".//div/div[2]/div/div[1]/div/a/text()").get()
            values['postTimeSince'] = self.sel.xpath(".//a[@data-click-id='timestamp']/text()").get()
            values['postUpVotes'] = self.sel.xpath(".//div[starts-with(@id ,'vote-arrows')]/div/text()").get()
            #getting alot of None for percent Upvotes
            values['postPercentUpVotes'] = self.sel.xpath(".//div[@data-test-id='post-content']/div[6]/div[2]/span/text()").get()
            if values['postPercentUpVotes'] == None:
                values['postPercentUpVotes'] = self.sel.xpath(".//div[@data-test-id='post-content']/div[5]/div[2]/span/text()").get()
            #values['postPercentUpVotes'] = self.sel.xpath(".//span[ends-with(text() , 'Upvoted')]/text()").get()
        
            postBox = self.sel.xpath(".//div[@data-test-id='post-content']")
            paragraphs = postBox.xpath(".//div/div/p")
            postParagraphs = list()
            for paragraph in paragraphs:
                postParagraphs.append(paragraph.xpath(".//text()").get())
            values['postText'] = postParagraphs

            #expand comments to see all by clicking the button 
            allCommentButton = self.driver.find_element(By.XPATH , "//button[contains(text(), 'View Entire Discussion')]").click()
            html = self.driver.page_source
            self.sel  = Selector(text=html)

            comments = self.sel.xpath(".//div[starts-with(@style, '--commentswrapper-gradient')]/div/div")
            
            commentList = list()
            for comment in comments:
                commentDict = dict()
                commentUserName = comment.xpath(".//a[starts-with(@href, '/user/')]/text()").get()
                commentUpVotes = comment.xpath(".//div[starts-with(@id, 'vote-arrows')]/div[1]/text()").get()
                commentTimeSince = comment.xpath(".//a[starts-with(@id, 'CommentTopMeta--Created--')]/text()").get()
                commentParagraphs = comment.xpath(".//div/div/p")
                commentText = list()
                for paragraph in commentParagraphs:
                    commentText.append(str(paragraph.xpath(".//text()").get()))  
                commentDict['commentUserName'] = commentUserName
                commentDict['commentUpVotes'] = commentUpVotes
                commentDict['commentTimeSince'] = commentTimeSince
                commentDict['commentText'] = commentText
                commentList.append(commentDict)
            values['comments'] = commentList
            values['subreddit_name'] = os.getenv('subreddit_name')
            yield values
        self.driver.close()



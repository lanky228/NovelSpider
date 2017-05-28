#!/usr/bin/python3
import threading
import queue
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib.request
import re
import os

# 解析页面
class Page:
    def __init__(self, url):
        self.url = url
        self.dic = self.__getDic(url)
    # 获取结构体
    def __getDic(self, url):
        html = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(html ,'lxml')
        body = soup.body
        while(True):
            temp = body
            for  content in body.children:
                if(hasattr(content, 'get_text') == False):
                    continue
                if(len(content.get_text()) >= len(body.get_text() )/2):
                    body = content
                    break
            if(temp == body):
                break
        dic = {}
        dic['title'] = soup.title.get_text() + '\n'
        dic['body'] = self.__replace(body.get_text('\n\t')) 
        dic['next'] = self.__getNext(url, soup)
        return dic
    # 字符替换
    def __replace(self, text):
        return re.sub(r'[^\u4e00-\u9fa5\w、，。：“”\t\n]', '', text)
    # 获取下一章地址
    def __getNext(self, url, soup):
        aList = soup.find_all('a', text= re.compile('下一.'))
        if(len(aList) > 0):
            next = aList[0]['href']
            if(next != None):
                return urljoin(url, next)
            else:
                return None

# 爬虫
class Spider (threading.Thread):
    def __init__(self, url_queue, data_queue):
        threading.Thread.__init__(self)
        self.url_queue = url_queue
        self.data_queue = data_queue
    def run(self):
        while True:
            url = self.url_queue.get()
            page = Page(url)
            next = page.dic['next'] 
            if(next != None):
                self.url_queue.put(next);
                pass
            self.data_queue.put(page.dic)
            print('下载：' + page.dic['title'])
            # 任务结束
            self.url_queue.task_done()

# 文件写入
class File (threading.Thread):
    def __init__(self, data_queue):
        threading.Thread.__init__(self)
        self.data_queue = data_queue
    def run(self):
        filename = 'novel.txt'
        if os.path.exists(filename):
            os.remove(filename)
        file = open(filename, 'a')
        while True:
            dic = self.data_queue.get()
            file.write(dic['body'])
            print('保存：' + dic['title'])
            # 任务结束
            self.data_queue.task_done()
        file.close( )

if __name__ == '__main__':
    # 第一章地址
    url = 'http://www.23us.com/html/7/7694/2186395.html'
    url_queue = queue.Queue()
    data_queue = queue.Queue()
    url_queue.put(url);

    spider = Spider(url_queue, data_queue)
    # 守护线程
    spider.daemon  = True
    spider.start()

    file = File(data_queue)
    # 守护线程
    file.daemon = True
    file.start()

    # 阻塞
    url_queue.join()
    data_queue.join()

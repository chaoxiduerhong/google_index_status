"""
逆向google
"""
import re
import json
import time
import traceback
import urllib.parse
from bs4 import BeautifulSoup, Comment
from spider.logs.syslog import SysLog
from config import gpt_conf

class StdHtml:
    """
    基础属性和动作

    获取属性：get_xxx
    执行动作：do_xxx
    检测：check_xxx
    点击：click
    页面输入框
    页面标题
    发送
    """
    def __init__(self, lock, browser_port, mark="", driver=None):
        self.lock = lock
        self.browser_port = browser_port
        self.driver = driver
        self.mark = mark
        self.sysLog = SysLog(thread_lock=self.lock, browser_port=self.browser_port, mark=self.mark)

    def std_html(self, html):
        """
        逆向解析请求数据
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 移除 <!-- --> 空注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 2. 去除 <ms-cmark-node>  <ms-grounding-sources> 标签，保留子内容
        for tag in soup.find_all('ms-cmark-node'):
            tag.unwrap()

        for tag in soup.find_all('ms-grounding-sources'):
            tag.unwrap()

        for tag in soup.find_all('ms-text-chunk'):
            tag.unwrap()

        # 3. 去除 <span> 标签，保留子内容
        for tag in soup.find_all('span'):
            tag.unwrap()

        # 4. 移除 ol、li、p、ul、strong、h1-h6 标签的所有属性
        tags_to_clean = ['ol', 'li', 'p', 'ul', 'strong'] + [f'h{i}' for i in range(1, 7)]
        for tag_name in tags_to_clean:
            for tag in soup.find_all(tag_name):
                tag.attrs = {}

        # 5. <a> 标签仅保留 href 属性
        for tag in soup.find_all('a'):
            href = tag.get('href')
            tag.attrs = {}
            if href:
                tag['href'] = href

        # 6. 移除空行（即完全为空或只有空白字符的 NavigableString 或标签）
        for element in soup.find_all(string=True):
            # 先移除纯空白文本
            if element.strip() == '':
                element.extract()

        # 再移除空标签（如 <p></p>、<div>    </div>）
        for tag in soup.find_all():
            if not tag.contents or all(
                    isinstance(content, str) and content.strip() == ''
                    for content in tag.contents
            ):
                tag.decompose()

        # 移除 <ms-search-entry-point> 及其子内容
        for tag in soup.find_all('ms-search-entry-point'):
            tag.decompose()

        return soup.prettify()

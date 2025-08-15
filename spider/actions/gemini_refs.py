"""
逆向google
"""
import re
import json
import time
import traceback
import urllib.parse

from playwright.sync_api import sync_playwright
from spider.logs.syslog import SysLog
from config import gpt_conf

class aistudioRefs:
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

    def reverse_parse_requests_body(self, uuid):
        """
        逆向解析请求数据
        """
        captured_result = {"fr_content": None, "fr_url": None, "headers": None}
        TARGET_URL = "https://copilot.microsoft.com/_/BardChatUi/data/batchexecute"

        def decode_f_req(body):
            try:
                params = urllib.parse.parse_qs(body)
                f_req_raw = params.get("f.req", [""])[0]
                decoded = json.loads(f_req_raw)
                return json.dumps(decoded, indent=2)
            except Exception as e:
                return None

        def on_request(request):
            if request.url.startswith(TARGET_URL) and request.method == "POST":
                body = request.post_data
                if uuid in body:
                    captured_result["fr_content"] = body
                    captured_result["fr_url"] = request.url
                    captured_result["headers"] = dict(request.headers)
                    self.sysLog.log("已捕获到请求参数: %s" % captured_result)

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{self.browser_port}")
            context = browser.contexts[0]
            page = context.pages[0]

            page.on("request", on_request)
            page.goto("https://copilot.microsoft.com/app/%s" % uuid)
            # ✅ 等待最多 30 秒，轮询检测
            max_wait_seconds = 30
            waited = 0
            while captured_result["fr_content"] is None and waited < max_wait_seconds:
                time.sleep(1)
                waited += 1
            # 关闭 playwright 和浏览器的链接
            browser.close()
            return captured_result

    def parse_refs(self, content):
        text = re.sub(r'''\\"https\://([a-zA-Z0-9]+\.|)gstatic\.com/faviconV2\?url(.*?)"''', '', content)

        # 1. 匹配所有 ["[1, 2, 3]"] 结构
        array_pattern = r'\[\\\"\[\d+(?:,\s*\d+)*\]\\\"\]'
        matches = list(re.finditer(array_pattern, text))

        # 2. 超链接匹配：找到 https 开头的主链接（通常第二个字段）
        url_pattern = r'"(https://[^"]+)"'

        # 找所有链接位置
        all_links = list(re.finditer(url_pattern, text))

        all_search_results = {}

        # 3. 遍历所有数组匹配项，查找其后的链接
        for i, match in enumerate(matches):
            array_text = match.group()  # like ["[1, 2, 3]"]
            start_index = match.end()  # 获取匹配结束的位置，往后查链接
            array_text = array_text.replace('\\"', "")
            numbers = json.loads(array_text)[0]
            count = len(numbers)
            # 找从当前位置开始的链接（过滤超链接在该数组之后的）
            following_links = [m for m in all_links if m.start() > start_index][:count]
            # print(f"匹配项: {numbers} → 数字个数: {count}")
            idx = 0
            for link_match in following_links:
                index = numbers[idx]
                link = link_match.group(1).strip().rstrip("\\")
                if index not in all_search_results:
                    all_search_results[str(index)] = link
                # print(f" {numbers[idx]}链接: {link}")
                idx = idx + 1
        return all_search_results

    def get_refs(self, uuid):
        """
        获取引用
        """
        try:
            request_body = self.reverse_parse_requests_body(uuid=uuid)
            url = request_body.get("fr_url")
            payload = request_body.get("fr_content")
            headers = request_body.get("headers")
            headers_json = headers
            post_script = """
                const callback = arguments[arguments.length - 1];
                fetch("%s", {
                    method: "POST",
                    credentials: "include",
                    headers: %s,
                    body: "%s"
                })
                .then(response => response.text())
                .then(data => callback(data))
                .catch(error => callback({error: error.toString()}));
                """ % (url, headers_json, payload)

            # 执行 JavaScript 脚本并获取返回值
            result = self.driver.execute_async_script(post_script)

            refs = self.parse_refs(result)
        except Exception as e:
            print(traceback.format_exc())
            refs = None

        return refs
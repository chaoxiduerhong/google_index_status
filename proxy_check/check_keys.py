# encoding=utf-8
"""
检测key是否可用

https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyAJAQ_vp1bhYBVemESz3W9ZAz66Zw577dw
如果返回的结构体中有 models 则说明可用


"""

import threading
import time
import traceback
import requests
import json
import utils.data
from config.gpt import gptConf
from config.keys import keysConf
from models import MProxyQueue

from threading import Lock

thread_lock = Lock()


lock = threading.Lock()
proxies = "http://127.0.0.1:10809"


class RequestThread(threading.Thread):
    def __init__(self, thread_id, keys):
        threading.Thread.__init__(self)
        self.thread_id = str(thread_id)
        self.proxy_info = None
        self.running_list = None
        self.keys = keys
        self.proxy_server = gptConf.proxy_server
        self.mark = ""


    @staticmethod
    def check(key):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models?key=%s" % key
            resp = requests.get(url, timeout=3, proxies={"http": proxies, "https": proxies})
            data = json.loads(resp.text)
            if resp.status_code == 200 and "models" in data:
                print("检测成功")
                return True
            print(key, data)
            return False
        except:
            return False

    def save_key(self, key):
        with thread_lock:
            utils.data.save_data("gemini_active_key", key)

    def run(self):
        result = []
        if not self.keys:
            print("队列已经用完")
        for key in self.keys:

            if self.check(key):
                self.save_key(key)
                print('"%s",\n' % key)




def split_list(lst, n):
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

def start():
    print("---------START-----------")
    keys = keysConf.gemini_key
    key_list = split_list(keys, 10)
    threads = []
    idx = 0
    utils.data.clear_data("gemini_active_key")

    for keys in key_list:
        idx = idx + 1
        thread = RequestThread(idx, keys)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print("---------END-----------")

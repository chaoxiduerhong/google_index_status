# encoding=utf-8
"""
检测是否有代理挂了

如果检测到某个代理上的代理有一条可访问，则可用。
如果连续检测到20条路线都不通，则标记该路线不可用。


"""

import threading
import time
import traceback
import requests
import json
import random

import utils.data
from config.gpt import gptConf
from models import MProxySourceType
from config.keys import keysConf
from spider.fs import FeiShu

lock = threading.Lock()
proxy_server = "http://" + gptConf.proxy_host
min_run_interval_seconds= 7200

class RequestThread(threading.Thread):
    def __init__(self, key):
        threading.Thread.__init__(self)
        self.thread_id = str(key)
        self.proxy_info = None
        self.running_list = None
        self.proxy_server = gptConf.proxy_server
        self.mark = ""
        self.report_ts = 0

    @staticmethod
    def check(proxy_info):
        proxy_port= proxy_info['port']
        try:
            proxy_address = f"{proxy_server}:%s" % proxy_port
            url = "https://www.google.com/"
            resp = requests.get(url, timeout=3, proxies={"http": proxy_address, "https": proxy_address})
            if resp.status_code == 200:
                return True
            return False
        except:
            return False

    def get_latest_proxy(self):
        """
        获取线上运行的最新队列
        """
        result = []
        url = f"{proxy_server}:8045/running_proxy"
        resp = requests.get(url)
        data = resp.content.decode("utf-8")
        proxy_dicts = json.loads(data)
        proxy_dicts = proxy_dicts['data']
        for indexID in proxy_dicts:
            proxy_dict = proxy_dicts[indexID]
            item = {
                "indexId": indexID,
                'remarks': proxy_dict['remarks'],
                'subid': proxy_dict['subid'],
                'source_type': proxy_dict['source_type'],
                'status': 'waiting',
                'pid': proxy_dict['pid'],
                'port': proxy_dict['proxy_http_port']
            }
            result.append(item)
        # 打乱顺序。
        random.shuffle(result)
        return result

    def plog(self, info):
        mark = f"[Thread_%s][{utils.common.get_now_str()}]-%s" % (self.thread_id, self.mark)
        print("%s - %s" % (mark, info))


    def host_report_status(self, server_name, notice_status, notice_info):
        """
        链接123 数据库上报信息
        notice_status: 上报的状态（子线程信息）  一般：normal/queue_empty 这两种状态
        notice_info： 上报的信息。只有当上报的状态异常的时候，才会显示（子线程信息）

        """
        current_ts = utils.common.get_second_utime()
        if current_ts - self.report_ts > 120:
            self.report_ts = current_ts
            from models.HostStatus import HostStatusModel
            hostStatus = HostStatusModel()
            data = {
                "thread_id": str(self.thread_id),
                "thread_name": str(self.thread_id),
                "server_name": server_name,     # f"copilot-Link-{gpt_conf.query_detail_mode}",
                "project_name": "aistudio_spider",
                "thread_status": notice_status,
                "thread_info": notice_info,
                "min_run_interval_seconds": min_run_interval_seconds
            }
            hostStatus.report_status(data)
            time.sleep(30)

    def run(self):
        # 获取所有的队列
        proxy_list = self.get_latest_proxy()
        result = {}

        try:
            for current_proxy in proxy_list:
                self.host_report_status("copilot-check-all", "normal", "运行正常")
                if current_proxy['source_type'] not in result:
                    ret = self.check(current_proxy)
                    if ret:
                        result[current_proxy['source_type']] = {
                            "status": "success",
                            "check_num": 1
                        }
                    else:
                        result[current_proxy['source_type']] = {
                            "status": "failed",
                            "check_num": 1
                        }
                elif result[current_proxy['source_type']]['status'] == "success":
                    self.plog("[%s]已验证成功，跳过" % current_proxy['source_type'])
                elif current_proxy['source_type'] in result and result[current_proxy['source_type']]['check_num'] <= 10:
                    ret = self.check(current_proxy)
                    if ret:
                        result[current_proxy['source_type']] = {
                            "status": "success",
                            "check_num": result[current_proxy['source_type']]['check_num'] + 1
                        }
                    else:
                        result[current_proxy['source_type']] = {
                            "status": "failed",
                            "check_num": result[current_proxy['source_type']]['check_num'] + 1
                        }
                else:
                    self.plog("[%s]已验证失败，跳过" % current_proxy['source_type'])
            self.plog("本次检测结束。sleep 1h continue")
            fs = FeiShu()
            fs.send_msg("海外路线状态", json.dumps(result, indent=4))
        except Exception as e:
            self.plog("匹配异常:%s" % e)


def start():
    while True:

        print("---------START-----------")
        threads = []
        for key in range(0, 1):
            thread = RequestThread(key)
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()
        time.sleep(min_run_interval_seconds)
        print("---------END-----------")
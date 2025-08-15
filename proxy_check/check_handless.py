# encoding=utf-8
"""
API key not valid  出现这个 认为账号无效，切换一个其他的来检测


Permission denied 账号权限不足或者被禁用，切换其他key检测


PERMISSION_DENIED
INVALID_ARGUMENT


"""

import threading
import time
import traceback
import requests
import json
import random

import utils.data
from config.gpt import gptConf
from models import MProxyQueue
from config.keys import keysConf

lock = threading.Lock()
proxy_server = "http://" + gptConf.proxy_host

class RequestThread(threading.Thread):
    def __init__(self, key):
        threading.Thread.__init__(self)
        self.thread_id = str(key)
        self.proxy_info = None
        self.running_list = None
        self.proxy_server = gptConf.proxy_server
        self.mark = ""
        self.report_ts = 0
        self.sleep_ts = 1800

    @staticmethod
    def get_indexID_list(data):
        result = []
        if data:
            for item in data:
                if isinstance(item, dict):
                    item_data = item
                else:
                    item_data = data[item]
                if "indexId" in item_data and item_data['indexId'] not in result:
                    result.append(item_data['indexId'])
        return result

    @staticmethod
    def check(current_proxy):
        """
        https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyAJAQ_vp1bhYBVemESz3W9ZAz66Zw577dw
        根据这个接口来了检测

        从所有的keys中随机获取一个

        """
        try:
            if "port" not in current_proxy:
                return False
            proxy_port = current_proxy['port']
            proxy_address = f"{proxy_server}:{proxy_port}"

            url = "https://copilot.microsoft.com/"
            response = requests.get(url, verify=False,
                                    proxies={"http": proxy_address, "https": proxy_address}, timeout=5)
            if response.status_code == 200:
                return True
            return False
        except:
            return False


    @staticmethod
    def check_base(current_proxy):
        if "port" not in current_proxy:
            return False
        port = current_proxy['port']
        proxy_address = f"{proxy_server}:{port}"
        try:
            url = "https://www.google.com/"
            resp = requests.get(url, timeout=3, proxies={"http": proxy_address, "https": proxy_address})
            if resp.status_code == 200:
                return True
            return False
        except:
            return False

    #
    def get_proxy_list(self):
        """
        获取当前线程的代理队列
        """
        result = []
        proxy_list = MProxyQueue.get()
        for current_proxy in proxy_list:
            indexId = current_proxy['indexId']
            indexId_end = str(indexId)[-1]
            if indexId_end == self.thread_id:
                result.append(current_proxy)
        return result

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
        return result

    def get_local_proxy(self):
        """
        获取数据库中所有代理
        """
        return MProxyQueue.get()

    def save_proxy(self, data):
        """
        更新：只更新port。
        """
        condition ={
            'indexId': data['indexId']
        }
        if MProxyQueue.first(condition=condition):
            MProxyQueue.update_one(data={
                'port': data['port']
            }, condition=condition)
        else:
            MProxyQueue.add_one(data)

    def plog(self, info):
        mark = f"[Thread_%s][{utils.common.get_now_str()}]-%s" % (self.thread_id, self.mark)
        print("%s - %s" % (mark, info))

    def auto_merge_proxy(self):
        """
        合并后的数据，必须是启动的。
        """
        with lock:
            latest_data = self.get_latest_proxy()
            local_data = self.get_local_proxy()
            latest_data_ids = self.get_indexID_list(latest_data)
            local_data_ids = self.get_indexID_list(local_data)
            add_total = 0
            del_total = 0
            update_total = 0

            # 线上不存在，直接退出程序
            if not latest_data:
                self.plog("----error --- 代理检测出现了故障， 程序退出-----")
                exit()

            # 本地不存在，全部add
            if latest_data and not local_data:
                for item in latest_data:
                    self.save_proxy(item)
            elif latest_data and local_data:
                # 最新的不在本地 直接新增
                for latest_item in latest_data:
                    latest_id = latest_item['indexId']
                    # 更新或者新增
                    self.save_proxy(latest_item)
                    if latest_id not in local_data_ids:
                        add_total = add_total + 1
                    else:
                        update_total = update_total + 1

                for local_id in local_data_ids:
                    if local_id not in latest_data_ids:
                        MProxyQueue.delete(condition={
                            "indexId": local_id
                        })
                        del_total = del_total + 1
            self.plog("自动化合并代理结束, 共新增了代理%s, 更新了代理:%s， 移除了无效代理:%s" % (add_total, update_total, del_total))

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
                "project_name": "copilot_spider",
                "thread_status": notice_status,
                "thread_info": notice_info,
                "min_run_interval_seconds": self.sleep_ts
            }
            hostStatus.report_status(data)
            time.sleep(30)

    def run(self):
            while True:
                self.host_report_status("copilot-check", "normal", "运行正常")
                self.auto_merge_proxy()
                # 获取所有的队列
                proxy_list = self.get_proxy_list()
                proxy_total = len(proxy_list)
                if proxy_total == 0:
                    self.plog("proxy queue empty...")
                    time.sleep(5)
                    continue
                self.plog(f"Found {proxy_total} proxy to be test, ")
                idx = 0
                try:
                    for current_proxy in proxy_list:
                        idx = idx + 1
                        indexId = current_proxy['indexId']
                        self.mark = "[%s/%s] - [remarks: %s, source_type:%s, indexId:%s]" % (idx, proxy_total,  current_proxy['remarks'], current_proxy['source_type'], indexId)
                        self.plog(f"---START---")

                        start_ts = utils.common.get_second_utime()
                        status = self.check(current_proxy)


                        status_check_base = self.check_base(current_proxy)
                        end_ts = utils.common.get_second_utime()
                        if status:
                            MProxyQueue.update_one(data={
                                'status': "running",
                                'status_check_base': "running" if status_check_base else "fault",
                                'success_ts': utils.common.get_second_utime(),
                                'duration_ts': end_ts - start_ts,
                                'running_ts': 0
                            }, condition={
                                "indexId": current_proxy['indexId']
                            })
                            self.plog(f"check success!")
                        else:
                            MProxyQueue.update_one(data={
                                'status': "fault",
                                'status_check_base': "running" if status_check_base else "fault",
                                "api_fault_num": (current_proxy['api_fault_num'] + 1) if 'api_fault_num' in current_proxy else 1
                            }, condition={
                                "indexId": current_proxy['indexId']
                            })
                            self.plog(f"check failed!")
                        self.plog(f"---END NEXT...---")
                    self.plog("本次检测结束。sleep 1h continue")

                except Exception as e:
                    self.plog("匹配异常:%s" % e)

                # 每轮sleep 秒
                time.sleep(self.sleep_ts)


def start():
    print("---------START-----------")
    # Create 10 threads
    threads = []
    for key in range(0, 10):
        thread = RequestThread(key)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print("---------END-----------")

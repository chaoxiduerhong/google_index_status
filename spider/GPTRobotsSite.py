# -*- coding:utf-8 -*-
"""
负责爬取和提取答案 并行操作
"""

import traceback
import time

import utils.common

from config import gpt_conf

from models import MSession, SessionModel, MProducts

from models import ProductsResultModel
from models import ProductsResultFullModel

from spider.GPTBase import GPTBase
from spider.logs.syslog import SysLog
from spider.product_queue.product import ProductQueue
from spider.wdriver.wdriver import WDriver as WDriverBrowser
from spider.browser_gpt import RBrowserManager as BrowserManager

class GPTQuery(GPTBase):
    def __init__(self, thread_lock, browser_port):
        super(GPTQuery, self).__init__(thread_lock, browser_port)
        # 是否正常运行。触发浏览器重启后，将该值设置为False， 成功回答后将该值设置为True
        # 如果为True，则减少相应的等待时间
        self.is_success_run = False
        self.is_prod_account = False

        # 因为在外部初始化该类，会因为多线程的原因，导致设置table_name失效
        self.MProductsResult = ProductsResultModel()
        self.MProductsResultFull = ProductsResultFullModel()


    def init_browser(self):
        """
        初始化
        """
        try:
            # 初始化和端口相关的
            # 因为是基于浏览器，并且可切换的，所有的数据都得重新初始化
            # 后期修改 根据切换浏览器状态来初始化这些信息
            self.MBrowser = BrowserManager()
            self.sysLog = SysLog(thread_lock=self.lock, browser_port=self.browser_port)
            self.productQueue = ProductQueue(self.lock, self.browser_port)
            self.WDriver = WDriverBrowser(self.lock, self.browser_port, interceptor_urls=gpt_conf.interceptor_urls)

            return True
        except:
            return False

    def save(self, data, bid=None):
        """
        table:product_gpt_des
        """
        data['url'] = gpt_conf.url
        data['browser_port'] = self.browser_port
        data['hostname'] = utils.common.get_sys_uname()
        self.MProductsResult.add_one(data)
        self.sysLog.log("save data success, bid:%s" % data['bid'])

    def std_bid(self, bid):
        bid = str(bid)
        return f"b{bid.zfill(6)}"


    def get_result(self, target_url):
        """
        获取搜索结果

        """
        hrefs = self.pageAction.get_search_hrefs()
        if target_url not in hrefs:
            return False
        return True

    def simulator(self, product):
        """
        子项通过 outline_items 字段获取
        """
        # 上报running 状态。 只有远端才会上报
        self.report_running_status()

        # 初始化浏览器连接
        self.init_webbrowser()
        self.init_page_action()

        start_time = utils.common.get_second_utime()

        query_msg = f"site:https://www.benchchem.com/product/{self.std_bid(product['bid'])}"
        check_url = f"https://www.benchchem.com/product/{self.std_bid(product['bid'])}"
        self.sysLog.log("current full url: %s" % query_msg)


        if not self.pageAction.switch_to_search_page():
            self.going_restart(is_match_proxy=True)
            self.sysLog.log("switch_to_login_page Failed!")
            time.sleep(20)
            return False

        # 检测人工校验
        time.sleep(2)
        self.sysLog.log("准备进行自动化人工校验检测")
        #  TODO 进行自动化人工校验
        if not self.pageAction.auto_robots():
            self.sysLog.log("人工校验未通过")
            self.going_restart(is_match_proxy=True)
            return False

        if not self.pageAction.check_search_input():
            self.sysLog.log("check_search_input Failed!")
            self.going_restart(is_match_proxy=True)
            return False

        ask_status = self.ask_js(query_msg)
        if not ask_status:
            self.sysLog.log("ask_js failed, continue")
            return False

        time.sleep(5)
        # 等待查询
        idx = 0
        while True:
            # 查询失败
            idx += 1
            if idx >= 30:
                break
            # 搜索完成
            try:
                if "/search" in self.driver.current_url:
                    break
            except Exception as e:
                continue
            time.sleep(1)

        # 获取查询结果
        search_status = self.get_result(check_url)
        # 存储数据
        end_time = utils.common.get_second_utime()
        data = {
            "bid": product['bid'],
            "product_name": product['product_name'],
            "duration": end_time - start_time,
            "status": search_status,
            "query": query_msg,
            "check_url": check_url,
            "proxy_port": self.browser_proxy['port'],
        }
        self.client_running_num = self.client_running_num + 1
        self.save(data)
        self.sysLog.log(f"current product query complete, status:{search_status}. save and next")
        return "continue"


    def query(self):
        """
        结果表名称： product_ast_bench_outline_detail_{idx}
        """
        is_first = True
        while True:
            try:
                if not self.init_browser():
                    print(f"{self.browser_port} - 初始化失败！")
                    self.waiting(300)
                    continue

                product = None

                if not product:
                    product = self.productQueue.get_product()

                if not product:
                    msg_title = "产品队列用尽通知"
                    msg_content = " 产品已经用尽，请尽快补充产品 "
                    self.sysLog.log(msg_content)
                    self.host_report_status(f"copilot-query_detail-{gpt_conf.query_detail_mode}", "queue_empty", "产品已经用尽，请尽快补充产品")
                    self.waiting(600)
                    continue

                # 产品数据检测
                if "bid" not in product or "product_name" not in product:
                    self.sysLog.log("check primary filed failed, next product...")
                    continue

                self.sysLog.log("get product success, bid: %s" % product['bid'])

                self.mark = "[bid:%s][running_num:%s]" % (product['bid'], self.client_running_num)
                self.sysLog.set_mark(self.mark)

                # 首次运行先分配下发一可用的代理
                if not self.check_proxy_status():
                    self.sysLog.log("check proxy status Failed switch proxy and sleep 60s...")
                    self.going_restart(is_match_proxy=True)
                    time.sleep(60)
                    continue
                self.sysLog.log("Check proxy status Okay, proceeding")

                # 故障重试机制： 连续失败n次后会触发一些处理事件
                if self.get_resp_error_num >= 5:
                    if self.get_resp_error_num == 5:
                        print("连续失败5次，重启并且匹配代理")
                        self.going_restart(is_match_proxy=True)
                    else:
                        print("连续大于5次，每次重启")
                        self.going_restart(is_match_proxy=True)

                    if 10 <= self.get_resp_error_num <= 15:
                        print("连续大于10次，每次重启并且匹配代理")
                        # 连续超过10次，每次修改10分钟，并且切换代理
                        self.going_restart(is_match_proxy=True)
                        time.sleep(600)
                    if self.get_resp_error_num > 15:
                        print("连续大于15次，重置状态。sleep 1h")
                        # 重置请求，并且直接sleep 1h
                        self.get_resp_error_num = 0
                        self.going_restart(is_match_proxy=True)
                        time.sleep(3600)

                if self.client_max_num <= self.client_running_num:
                    self.sysLog.log("current client client_running_num %s, sleep..." % self.client_running_num)
                    self.waiting(120)
                    self.going_restart(is_match_proxy=True)

                # 失败重试次数
                err_retry = 0
                while True:
                    err_retry = err_retry + 1
                    self.sysLog.log("start simulator...")
                    try:
                        # TODO 上一个和下一个时间间隔最大 172个。因为可能存在失败或者等待的情况，设置为150
                        start_ts = utils.common.get_second_utime()
                        resp_status = self.simulator(product)
                        end_ts = utils.common.get_second_utime()
                        cost_ts = int(end_ts - start_ts)
                        self.sysLog.log(f"Done Simulator, Cost {cost_ts} s.")

                        left_ts = gpt_conf.fixed_running_loop_for_login - cost_ts
                        self.sysLog.log("current requests left ts %s" % left_ts)

                        if gpt_conf.is_fixed_running_time and resp_status:
                            if left_ts > 0:
                                self.sysLog.log("======>fixed sleep %s..." % left_ts)
                                time.sleep(left_ts)
                        break
                    except:
                        _sleep_ts = 30
                        self.sysLog.err_log("获取数据异常, 原因：%s" % (traceback.format_exc()))
                        self.sysLog.log(f"获取数据异常，重新尝试{err_retry}/5。 sleep {_sleep_ts}s")
                        time.sleep(_sleep_ts)

                        if err_retry >= 4:
                            self.sysLog.log(
                                f"产品获取数据异常 {err_retry}/4，即将执行清缓存，重启 browser，重新匹配代理后继续尝试")
                            # 重启浏览器操作
                            self.going_restart(is_match_proxy=True)

                        if err_retry >= 6:
                            self.sysLog.log("产品获取数据失败，切换下一个产品继续")
                            break

            except:
                print(traceback.format_exc())
                self.sysLog.log(f"{self.browser_port} - 未知异常原因(while-true-Try/Exception)，程序等待10分钟再次运行。 ")
                self.sysLog.err_log(f"{self.browser_port} - 未知异常原因，程序等待10分钟再次运行。Error:%s" % traceback.format_exc())
                time.sleep(600)

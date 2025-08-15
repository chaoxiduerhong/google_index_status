# -*- coding:utf-8 -*-
import json
import traceback
import time
import os
import requests
import json

from selenium.webdriver.common.keys import Keys
from config import gpt_conf
import utils.common
from models import MSession, MProxyQueue, MSessionLog
from spider.actions.page_action import PageAction


class GPTBase:
    def __init__(self, thread_lock, browser_port):
        self.mark = None
        self.browser_port = browser_port

        self.browser_host = "127.0.0.1"
        self.browser_proxy = None
        self.browser_conn_status = False
        # 浏览器编号
        self.driver = None
        # 创建线程锁c
        self.lock = thread_lock
        # 获取异常次数。如果该次数大于等于阈值，则认为本次需要切换代理。并且重置值为0. 请求成功也切换为0
        self.get_resp_error_num = 0
        # 最大账号连续失败次数
        self.limit_account_error_num = 0
        self.session_key = None
        self.session_token = None
        self.session_list = []
        # 检测必须使用本地的代理来控制。Query需要RBrowserManager来控制
        # self.MBrowser = BrowserManager()
        self.MBrowser = None
        # self.sysLog = SysLog(thread_lock=self.lock, browser_port=self.browser_port)
        self.sysLog = None
        # self.productQueue = ProductQueue(self.lock, self.browser_port)
        self.productQueue = None
        # self.WDriver = WDriverBrowser(self.lock, self.browser_port, interceptor_urls=gpt_conf.interceptor_urls)
        self.WDriver = None
        self.pageAction = None
        # 代理获取是否使用登录的代理下发方案：用于登录，同一个代理24h内只允许下发一次
        self.is_login_proxy_issue = False
        self.clear_user_data = False
        self.is_reorder = False
        self.is_prod_account = False
        self.report_ts = 0
        # 每个客户端最大连续运行次数
        self.client_max_num = 30
        # 当前已经连续运行的次数
        self.client_running_num = 0


    def waiting(self, ts):
        self.sysLog.log(f"Will SLEEP FOR {ts} seconds")
        time.sleep(ts)

    def connect_webbrowser(self):
        idx = 0
        self.sysLog.log(f"connect_webbrowser, connected to {self.browser_port} ...")
        while True:
            idx = idx + 1
            time.sleep(1)

            # 超过3次，重启浏览器
            if idx >= 3:
                self.sysLog.log("connection browser failed! restart browser")
                self.going_restart(is_match_proxy=True)
                time.sleep(30)

            # 超过10次，可能出现了故障。这时候需要多等待5分钟
            if idx >= 10:
                self.sysLog.log("check webbrowser connected failed,retry More than 10 times. sleep 300s continue.")
                time.sleep(300)

            try:
                self.sysLog.log(f"connect_webbrowser, conn num {idx}")
                self.WDriver.set_clear_user_data(self.clear_user_data)
                # TODO 可能遇到这种情况：因为切换的代理不行，一直处于访问卡死状态。这里失败需要重新切换代理
                if not self.WDriver.init_driver():
                    self.going_restart(is_match_proxy=True)
                    continue
                self.driver = self.WDriver.driver
                self.browser_conn_status = True
                self.sysLog.log(f"connect_webbrowser, success")
                break
            except:
                err_msg = str(traceback.format_exc())
                self.sysLog.log("check connected chrome failed! waiting retry...!")
                self.sysLog.err_log("check connected chrome failed! please check browser, waiting retry...!, error: %s" % err_msg)

            self.browser_conn_status = False

    def init_webbrowser(self):
        """
        初始化浏览器
        如果已经初始化，则跳过
        初始化前先检测浏览器是否可用，可连接。如果浏览器无法链接则强制退出并且冲切
        """
        if self.browser_conn_status and self.WDriver.is_browser_alive():
            # TODO 检测浏览器是否链接。
            return True
        else:
            self.connect_webbrowser()
            return True

    def init_page_action(self):
        self.pageAction = PageAction(self.lock, self.browser_port, mark=self.mark, driver=self.driver,
                                     WDBrowser=self.WDriver)

    def going_restart(self, clear_cache=None, is_match_proxy=False, clear_user_data=None, is_reorder=None):
        """
        is_match_proxy： 是否需要重新匹配代理。用于远端请求
        清cookie
        重启浏览器
        重新连接浏览器
        设置代理？
        is_reorder:是否支持重启后浏览器重新排序
        """
        try:
            # 每次重启浏览器最大次数被重置
            self.client_running_num = 0
            if is_reorder is None:
                is_reorder = self.is_reorder
            # 当需要匹配代理，并且为远端的适合，重新匹配一个新的代理
            if is_match_proxy:
                self.proxy_issue()
                self.WDriver.set_proxy(proxy_port=self.browser_proxy['port'], proxy_id=self.browser_proxy['indexId'])

            self.browser_conn_status = False
            # 重启浏览器
            self.sysLog.log("Browser is about to restart...")
            self.WDriver.browser_restart(clear_user_data=clear_user_data, is_reorder=is_reorder)
            time.sleep(3)
            # 浏览器重启后建立连接
            self.init_webbrowser()
            self.init_page_action()
        except:
            pass

    def update_browser_status(self, running_status="actived"):
        """
        更新配置文件中浏览器信息
        """
        with self.lock:
            try:
                browser_info = self.MBrowser.get_browser(self.browser_port)
                print("update_browser_status - BROWSER INFO ")
                utils.set_setting(gpt_conf.browser_status_file_path, self.browser_port, {
                    "running_status": running_status,
                    "running_time": utils.get_now_str(),
                    "running_proxy": browser_info['proxy_name']
                })
            except:
                print("update_browser_status failed, err:%s" % traceback.format_exc())

    def check_browser_breakdown(self, error_info):
        """
        检测浏览器是否崩溃，并且发送通知
        如果一个浏览器，10分钟内连续崩溃多次，则重启
        force_restart: 非捕获异常获取到，当触发一定限制的时候，手动触发
        """
        if "timeout: Timed out receiving message from renderer" in error_info or \
                "InvalidSessionIdException: Message: invalid session id" in error_info or \
                "Message: no such window: target window already closed" in error_info or \
                "unknown error: cannot connect to chrome" in error_info or \
                "force_restart" in error_info or \
                "cannot connect to chrome at" in error_info or \
                "failed to check if window was closed" in error_info:
            self.sysLog.log("检测到窗口【%s】对应的浏览器窗口可能崩溃。尝试重启浏览器" % self.browser_port)
            self.going_restart(clear_cache=False, is_match_proxy=True)
            self.update_browser_status(running_status="err_breakdown")
            self.connect_webbrowser()
            time.sleep(60)

    def check_auth_token(self):
        # TODO 整改
        try:
            ret = self.driver.execute_script("return window.localStorage.getItem('userToken')")
            res = json.loads(ret)
            return res['value']
        except:
            return None

    def get_cookie_auth_token(self):
        try:
            all_cookies = self.driver.get_cookies()
            return all_cookies
        except:
            print("get_cookie_auth_token Failed")
            return None

    def check_user_login(self, session_token=None):
        """
        检测并且返回用户信息
        """

        def check_login_status(url, headers):
            script = f'''
            return fetch("{url}", {{
                method: "GET",
                headers: {json.dumps(headers)}
            }}).then(response => response.json()).then(data => data);
            '''
            result = self.driver.execute_script(script)
            self.sysLog.log(f"check-login-status(): res: {result}")
            if 'user' in result:
                return result['user']
            else:
                return None
            # return 'user' in result

        api_url = "https://graph.microsoft.com/v1.0/me"
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json'
        }
        return check_login_status(api_url, headers)

    def set_birthday_api(self, cookie_session_token):
        return True


    def save_token(self, session_token):
        save_token_root = gpt_conf.new_token_file
        os.makedirs(save_token_root, exist_ok=True)
        token_file_path = "%s/%s" % (save_token_root, self.session_key)
        session_token = json.dumps(session_token, indent=4)
        with open(token_file_path, 'w') as f:
            f.write(session_token)

    def check_session_token(self, sessions):
        name_list = [item['name'] for item in sessions]
        if "SID" in name_list and "HSID" in name_list:
            return True
        return False

    def add_account_log(self, action_type, action_info, account=None):
        """
        只记录账号的活动状态
        """
        if not account:
            account = self.session_key
        MSessionLog.add_log(
            account=account,
            browser_port=self.browser_port,
            action_type=action_type,
            action_info=action_info,
            proxy_source_indexId = self.browser_proxy['indexId'],
            proxy_source_type=self.browser_proxy['source_type'],
            proxy_source_name=self.browser_proxy['remarks'],
        )

    def auto_login(self, account=None):
        """
        设置token不需要检测用户是否登录。接口获取到后直接干
        """
        # 捕获页面加载异常的情况
        idx = 0
        while True:
            idx = idx + 1
            if idx == 2:
                time.sleep(30)
            if idx == 3:
                time.sleep(60)
            if idx > 3:
                time.sleep(300)
                return False
            try:
                self.session_key = None
                self.pageAction.close_other_tab()
                # 开启了token自动登录 + 未登录状态
                if gpt_conf.is_token_auto_login:
                    # 获取session token
                    self.sysLog.log("执行下发账号")
                    if account:
                        session_response = self.api_session_issue_by_db_account(account)
                    else:
                        session_response = MSession.lock_get_session_issue(
                            self.browser_port,
                            utils.common.get_sys_uname(),
                            self.browser_proxy['port']
                        )

                    try:
                        session_token = session_response['session']
                        self.sysLog.log("获取到下发的账号 account:%s; data_type:%s" % (session_response['session_key'], session_response['data_type']))

                        if self.check_session_token(session_token):
                            self.sysLog.log("下发账号的关键字段校验正常")
                        else:
                            self.sysLog.log("发的账号信息可能有问题，丢失了sid 或者hsid等重要信息")
                            MSession.update_one(data={"sync_status": "error"}, condition={"account": session_response['session_key']})
                            continue
                    except:
                        self.sysLog.log("获取到账号数据，解析异常")
                        time.sleep(2)
                        continue

                    # 清除本地数据
                    self.WDriver.clear_local_cache()
                    self.sysLog.log("clear_local_cache: Done clear cache...")

                    # 设置
                    self.sysLog.log("正在进行登录...")
                    for cookie in session_token:
                        cookie.pop('expiry', None)
                        self.driver.add_cookie(cookie)
                    time.sleep(1)  # 等页面加载

                    # 强制刷新页面
                    self.driver.refresh()

                    self.sysLog.log("in auto_login(): page is refresh...")

                    # TODO 检测用户是否登录状态？如果登录则跳出
                    self.pageAction.switch_to_chat_page()

                    # TODO 检测用户是否在登录界面。如果用户在登录界面，则需要标记该账号： login_status: auth_failed
                    current_url = self.driver.current_url
                    if session_response['session_key'] and current_url.startswith("https://accounts.google.com"):
                        self.sysLog.log("账号登录状态已经失效，需要重新登录后可使用。 account:%s, account_info" % session_response)
                        self.add_account_log(
                            account=session_response['session_key'],
                            action_type="checked_login_invalid",
                            action_info="该账号已经过期，状态被设置为 invalid"
                        )
                        MSession.update_login_status_invalid(session_response['session_key'])
                        return False

                    time.sleep(5)
                    if self.pageAction.check_login_mark():
                        self.session_key = session_response['session_key']
                        self.sysLog.log("检测登录成功, account:%s" % self.session_key)
                        self.add_account_log(
                            action_type="cookie_login_success",
                            action_info="通过cookie登录成功"
                        )

                        self.session_token = session_token
                        self.is_prod_account =  session_response['is_prod_account'] if "is_prod_account" in session_response else False
                        MSession.update_success_num(self.session_key)

                        cookie_session_token = self.get_cookie_auth_token()
                        MSession.update_last_cookie(self.session_key, cookie_session_token)
                        self.save_token(cookie_session_token)
                        return True
                    else:
                        self.sysLog.log("检测登录失败, account:%s, account_info" % session_response)
                        self.add_account_log(
                            action_type="cookie_login_failed",
                            action_info="通过cookie登录失败"
                        )
                        # 如果检测到账号无效. 上报登录异常
                        MSession.update_failed_num(session_response['session_key'])
                        return False
            except:
                self.sysLog.log(f"auto login failed.!!!!!!!!!!! {traceback.format_exc()}")
            time.sleep(3)
            return False

    def api_proxy_issue(self):
        req_url = f"{gpt_conf.remote_server}/proxy_issue?"

        # 注意：禁用和限制代理是互斥的
        proxy_source_type = gpt_conf.proxy_source_type
        if proxy_source_type:
            req_url = req_url + f"&proxy_source_type={proxy_source_type}"
        elif gpt_conf.dis_source_type:
            req_url = req_url + f"&dis_source_type={gpt_conf.dis_source_type}"

        # proxy 全局后，只有 tagss 的 hk和tw 可以顺畅访问
        proxy_countries = gpt_conf.proxy_countries
        if proxy_countries:
            req_url = req_url + f"&proxy_countries={proxy_countries}"

        print( f"api_proxy_issue: {req_url}")

        resp = requests.get(url=req_url, timeout=13)
        resp_json = json.loads(resp.content)
        return resp, resp_json

    def api_proxy_issue_for_login(self):
        req_url = f"{gpt_conf.remote_server_for_login}/proxy_issue_for_login"
        print( f"api_proxy_issue_for_login: {req_url}")
        resp = requests.get(url=req_url, timeout=15)
        resp_json = json.loads(resp.content)
        return resp, resp_json

    def proxy_issue(self):
        """
        获取下发的代理，并且远端上报error状态
        下发代理成功，更新本地浏览器代理配置

        不再上报代理失败状态。
        """
        with self.lock:
            try:
                if not self.is_login_proxy_issue:
                    resp, resp_json = self.api_proxy_issue()
                else:
                    resp, resp_json = self.api_proxy_issue_for_login()

                # failed_proxy = self.browser_proxy
                self.browser_proxy = resp_json['data']

                # if failed_proxy and "port" in failed_proxy:
                #     self.report_error_status(failed_proxy['port'])

                proxy_info = json.loads(resp.content)
                try:
                    proxy_info['data']['source_type']
                except:
                    print("proxy issue failed:%s" % proxy_info)

                print("*** proxy_issue success!, source_type:%s" % proxy_info['data']['source_type'])
                print("*** proxy_issue success!, remarks:%s" % proxy_info['data']['remarks'])
            except Exception as e:
                print("*** proxy_issue failed: %s" % e)
                print("*** proxy_issue failed: %s" % traceback.format_exc())

    def api_session_issue(self):
        """
        session请求并且下发
        每次请求获取一组数据，并且将该组数据存储到一个队列中。每次使用都出队，获取一个
        接口：session_issues
        数据队列：session_list

        """
        try:
            if not self.session_list:
                req_url = "%s/session_issue_list?hostname=%s&browser_port=%s&proxy_port=%s" % (gpt_conf.remote_server, utils.common.get_sys_uname(), self.browser_port, self.browser_proxy['port'])
                print(f"[{self.browser_port}] {req_url}")
                resp = requests.get(url=req_url, timeout=15)
                resp_json = json.loads(resp.content)
                # 需要 debug 的时候打印
                if 'data' in resp_json and resp_json['data']:
                    self.session_list = resp_json['data']
            if self.session_list:
                result = self.session_list.pop(0)
                print("current api_session_issue account:", result['account'])
                return result
            else:
                print("current api_session_issue not find account")
                return None

        except:
            print("-------- !!!!!!!! get session error !!!!!!!! ----", traceback.format_exc())
            return None


    def api_session_issue_by_db_account(self, account):
        """
        session请求并且下发
        每次请求获取一组数据，并且将该组数据存储到一个队列中。每次使用都出队，获取一个
        接口：session_issues
        数据队列：session_list
        """
        return MSession.lock_get_session_issue_account(account)

    def report_running_status(self):
        MProxyQueue.update_one(condition={
            'port': int(self.browser_proxy['port'])
        }, data={
            "running_ts": utils.common.get_second_utime()
        })

    def report_success_status(self):
        """
        给远端上报success_ts状态
        """
        current = MProxyQueue.first(condition={
            'port': int(self.browser_proxy['port'])
        })
        if current:
            success_num = 1
            if "success_num" in current:
                success_num = current['success_num'] + 1
            MProxyQueue.update_one(condition={
                'port': int(self.browser_proxy['port'])
            }, data={
                "success_num": success_num,
                "status": "running",
                "success_ts": utils.common.get_second_utime(),
                "running_ts": utils.common.get_second_utime()
            })

    def report_error_status(self, proxy_port=None):
        """
        上报故障状态
        """
        if not proxy_port:
            proxy_port = self.browser_proxy['port']
        MProxyQueue.update_one(condition={
            'port': int(proxy_port)
        }, data={
            "status": "fault"
        })

    def check_proxy_status(self):
        if self.browser_proxy:
            try:
                proxy_address = "http://%s:%s" % (gpt_conf.proxy_host, self.browser_proxy['port'])
                url = "https://www.google.com/"
                resp = requests.get(url, timeout=3, proxies={"http": proxy_address, "https": proxy_address})
                if resp.status_code == 200:
                    return True
                return False
            except:
                return False

    def ask_js(self, ask_msg):
        """
        发起询问
        """
        try:
            # 模拟点击文本框
            utils.common.action_wait()

            time.sleep(1)
            # 模拟手工输入操作
            self.sysLog.log("waiting entering ask msg")
            input_box = self.pageAction.get_search_input()

            if input_box:
                # 先清空输入框
                self.driver.execute_script("arguments[0].textContent = '';", input_box)
                self.driver.execute_script(f"arguments[0].value = `{ask_msg}`;", input_box)
                # 输入完毕，输入enter 获取点击相关按钮。这里当前按输入enter来确认
                input_box.send_keys(" ")
                self.sysLog.log("click ENTER KEY")
                time.sleep(2)
                input_box.send_keys(Keys.CONTROL, Keys.ENTER)
                return True
            else:
                return False
        except:
            self.sysLog.log("ask js error: %s" % traceback.format_exc())
            return False

    @staticmethod
    def get_ask_msg(product):
        ask_msg = gpt_conf.ask_template.replace("{keywords}", product['product_name'])
        return ask_msg

    @staticmethod
    def get_ask_msg_for_template(product:dict, template_content:str):
        ask_msg = gpt_conf.ask_template.replace("{keywords}", product['product_name'])
        ask_msg = ask_msg.replace("{template}", template_content)
        return ask_msg

    def save(self, data, bid=None):
        pass

    def simulator(self, product):
        pass

    def query(self):
        pass

    def check_hand_something_error(self):
        """
        自动化处理something 异常时间。
        """
        # 检测到了，设置当前浏览器封锁1h
        if self.pageAction.check_something_error():
            MSession.update_exp_to(browser_port=self.browser_port)
            return True
        return False


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
                "thread_id": str(self.browser_port),
                "thread_name": str(self.browser_port),
                "server_name": server_name,     # f"copilot-Link-{gpt_conf.query_detail_mode}",
                "project_name": "aistudio_spider",
                "thread_status": notice_status,
                "thread_info": notice_info,
            }
            hostStatus.report_status(data)
            time.sleep(30)


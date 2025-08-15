# -*- coding:utf-8 -*-
import traceback
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from spider.browser import BrowserManager as OBrowserManager

from config import gpt_conf
from spider.browser_gpt import RBrowserManager as BrowserManager

from spider.browser_gpt_bit import BitBrowserManager

class WDriver:
    def __init__(self, thread_lock=None, browser_port=None, proxy_info=None, interceptor_urls=None, enable_bit_driver=False):
        # 相当于 selenium 的 driver
        self.chrome_options = None
        self.driver = None
        self.browser_config_path = gpt_conf.browser_config_path

        self.page = None
        self.browser_port = browser_port
        self.browser_host = "127.0.0.1"

        # 启用bit浏览器
        self.enable_bit_driver = enable_bit_driver
        self.bit_driver_path = None
        self.bit_http = None

        self.browser = None
        self.context = None
        self.default_url=f"http://localhost:{self.browser_port}/json/version"
        # proxy_info: proxy_host, proxy_port
        self.proxy_host = proxy_info['proxy_host'] if proxy_info and "proxy_host" in proxy_info else gpt_conf.proxy_host
        self.proxy_port = proxy_info['proxy_port'] if proxy_info and "proxy_port" in proxy_info else None
        self.proxy_id = proxy_info['proxy_id'] if proxy_info and "proxy_id" in proxy_info else None
        self.proxy_protocol = proxy_info['proxy_protocol'] if proxy_info and "proxy_protocol" in proxy_info else "http"
        self.interceptor_urls = interceptor_urls
        self.lock = thread_lock
        self.is_clear_user_data = False
        self.MBrowser = BrowserManager()
        self.MBitBrowser = BitBrowserManager()

    def init_bit(self, bit_driver_path, bit_http):
        """
        初始化bit浏览器
        """
        self.bit_driver_path = bit_driver_path
        self.bit_http = bit_http
        print(self.bit_driver_path, self.bit_http, "current init data=============")

    def set_proxy(self, proxy_port, proxy_id, proxy_host=gpt_conf.proxy_host, proxy_protocol="http"):
        """
        设置代理
        在重启浏览器前调用生效
        """
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_id = proxy_id
        self.proxy_protocol = proxy_protocol



    def set_interceptor_urls(self, urls):
        self.interceptor_urls = urls

    def set_clear_user_data(self, status=False):
        self.is_clear_user_data = status
        # 清除用户数据需要重新排序
        if status:
            browserManager = OBrowserManager()
            browserManager.reorder()


    def is_browser_alive(self):
        try:
            self.driver.execute_script("return 1;")
            return True
        except:
            return False

    def driver_interceptor(self):
        """
        为driver 创建拦 urls 截器
        发现类似请求则拦截。

        urls: 支持正则写法
        """
        if self.interceptor_urls:
            self.driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": self.interceptor_urls})
            self.driver.execute_cdp_cmd('Network.enable', {})

    def close_other_tab(self):
        """
        关闭其他标签页, 保留当前标签页
        """
        try:
            # 获取所有窗口的句柄
            window_handles = self.driver.window_handles
            # 关闭除当前窗口外的所有其他窗口
            current_window = self.driver.current_window_handle
            if len(current_window) > 1:
                for handle in window_handles:
                    if handle != current_window:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                # 最后，确保切换回主窗口
                self.driver.switch_to.window(current_window)
            return True
        except:
            print(traceback.format_exc())
            # self.log("关闭其他窗口失败")
        return False

    def init_driver(self):
        idx = 0
        # self.log(f"connect_webbrowser, connected to {self.browser_name} ...")
        while True:
            idx = idx + 1
            time.sleep(1)

            # 超过3次，重启浏览器
            if idx >= 3:
                print("connection browser failed! restart browser")
                # TODO 重启浏览器。
                time.sleep(60)
                return False
            try:
                self.chrome_options = Options()
                # TODO 后期调研该设置的必要性
                self.chrome_options.ignore_local_proxy_environment_variables()

                if self.enable_bit_driver:
                    # 浏览器信息配置
                    driverPath = self.bit_driver_path
                    debuggerAddress = self.bit_http

                    print("---------")
                    print(debuggerAddress)
                    print(driverPath)
                    print("---------")

                    self.chrome_options.add_experimental_option("debuggerAddress",debuggerAddress)
                    chrome_service = Service(driverPath)
                    self.driver = webdriver.Chrome(service=chrome_service, options=self.chrome_options)
                else:
                    # 浏览器信息配置
                    self.chrome_options.add_experimental_option("debuggerAddress", "%s:%s" % (self.browser_host, self.browser_port))
                    self.driver = webdriver.Chrome(options=self.chrome_options)

                # 配置拦截器： 不同的网站需要配置不同的拦截器。  比如 perplexity 上报触发人工校验： cookie `cf_clearance`
                # self.driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": ["www.perplexity.ai/cdn-cgi/challenge-platform/*"]})
                # self.driver.execute_cdp_cmd('Network.enable', {})
                self.driver_interceptor()

                # TODO 后期方案： 隐藏webdirver,

                # TODO 后期方案： 设置 navigator.languages

                # TODO 后期方案： navigator.plugins

                # TODO 后期方案： canvas

                # TODO 后期方案： WebGL Vendor + WebGL Renderer
                time.sleep(1)
                self.close_other_tab()
                self.driver.get(gpt_conf.driver_default_page)
                return True
            except:
                err_msg = str(traceback.format_exc())
                print("init_driver ERROR:",err_msg)
                return False


    def browser_restart(self, clear_user_data=None, is_reorder=False):
        """
        重启浏览器单独封装
        1. 强制关闭当前端口
        2. 启动浏览器
        """
        with self.lock:
            try:
                if clear_user_data is None:
                    clear_user_data = self.is_clear_user_data
                if self.enable_bit_driver:
                    return self.MBitBrowser.restart_browser(port = self.browser_port,
                                                  proxy_port=self.proxy_port,
                                                  is_reorder=is_reorder)
                else:
                    self.MBrowser.restart_browser(self.browser_port,
                                                  proxy_port=self.proxy_port,
                                                  proxy_name=self.proxy_id,
                                                  clear_user_data=clear_user_data,
                                                  is_reorder=is_reorder)

            except:
                print("browser_restart failed %s" % traceback.format_exc())

    def get_browser(self):
        """
        动态获取
        """
        return self.MBrowser.get_browser(self.browser_port)

    def clear_cookie(self):
        """
        清cookie
        该方案会强制跨域清cookie
        """
        self.driver.delete_all_cookies()

    def clear_localStorage(self):
        """
        清localStorage
        """
        self.driver.execute_script("window.localStorage.clear()")


    def clear_sessionStorage(self):
        """
        清sessionStorage
        """
        self.driver.execute_script("window.sessionStorage.clear()")

    def clear_local_cache(self):
        """
        需要清除三个域名下的
        """
        self.clear_cookie()
        self.clear_sessionStorage()
        self.clear_localStorage()
        return True

    def clear_cookie_by_name(self):
        """
        清除指定的cookie name
        """
        pass



"""
主要解决人工校验问题
链接窗口，打开新标签
等待人工校验，并且打开
"""

import time
import traceback
from DrissionPage import ChromiumPage, ChromiumOptions, WebPage
from DrissionPage.common import Keys, By

class Driss:
    def __init__(self, port):
        self.port = port
        self.driver = self.getDriver()

    def getDriver(self):
        co = ChromiumOptions()
        # 阻止“自动保存密码”的提示气泡
        co.set_pref('credentials_enable_service', False)
        # 阻止“要恢复页面吗？Chrome未正确关闭”的提示气泡
        co.set_argument('--hide-crash-restore-bubble')
        co_page = ChromiumOptions().set_local_port(self.port)
        return ChromiumPage(co_page)

    def initDriver(self):
        self.driver = self.getDriver()

    def auto_robots(self):
        """
        自动化人工点击
        """
        try:
            dom = self.driver. \
                ele((By.ID, "recaptcha")). \
                ele((By.TAG_NAME, "div")).ele((By.TAG_NAME, "div")). \
                ele((By.TAG_NAME, "iframe")).ele((By.ID, "recaptcha-anchor"))
            dom.click()
            return True
        except:
            print(traceback.format_exc())
            return False

    def to_click(self):
        print("DISS create new tab")
        self.driver = self.driver.new_tab()
        time.sleep(2)
        print("DISS to chat page")
        self.driver.get('https://copilot.microsoft.com/')
        time.sleep(10)
        self.auto_robots()
        print("DISS handle ok")

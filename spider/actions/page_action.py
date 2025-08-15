"""
页面操作
和页面相关的操作封装到这里
"""
import re
import time
import traceback
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .Driss import Driss
import utils.common
from spider.logs.syslog import SysLog
from config import gpt_conf

class PageAction:
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
    def __init__(self, lock, browser_port, mark="", driver=None, WDBrowser=None):
        self.lock = lock
        self.browser_port = browser_port
        self.driver = driver
        self.WDBrowser = WDBrowser
        self.mark = mark
        self.sysLog = SysLog(thread_lock=self.lock, browser_port=self.browser_port, mark=self.mark)



    def get_chat_input(self):
        """
        获取聊天框
        最大等待5s
        """
        try:
            parent_box = self.driver.find_element(By.CSS_SELECTOR, "textarea.textarea")
            return parent_box
        except Exception as e:
            return None

    def get_language_model(self):
        """
        有两个：选择r1 + 联网搜索
        """
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="button"].ds-button--filled'))
            )
            buttons = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="button"].ds-button--filled')
            return buttons
        except Exception as e:
            return None


    def get_url_uuid(self):
        """
        # TODO 获取url方案是之前项目的，需要手动修改
        回答问题的地址：https://copilot.microsoft.com/a/chat/s/8e0231f6-6a6c-4135-b2ca-72d7ffb3e183
        获取url部分并且 chat 存在，uuid 存在
        uuid 长度36
        """
        idx = 0
        is_success = False
        while True:
            idx = idx + 1
            time.sleep(2)
            try:
                current_url = self.driver.current_url
                parsed_url = urlparse(current_url)
                path = parsed_url.path.strip().strip("/")
                url_attrs = path.split('/')
                if is_success and "app/" in path and len(url_attrs) >= 2:
                    return current_url, url_attrs[-1]
                elif "app/" in path and len(url_attrs) >= 2:
                    is_success = True
                    time.sleep(2)
                else:
                    self.sysLog.log("not find url_uuid, continue...")
            except:
                time.sleep(5)
                continue

            if idx > 30:
                return current_url, None

    def auto_start_research(self):
        """
        只有点了start research 才会开始
        """
        try:
            confirm_button = WebDriverWait(self.driver, 80).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="confirm-button"]'))
            )
            time.sleep(2)
            confirm_button.click()
            return True
        except Exception as e:
            print("未找到 confirm-button 或等待超时")
            return False

    def auto_security_layer(self):
        """
        自动化程序可能会触发安全层保护机制。 需要手动点击对应的元素
        """
        try:
            backdrop = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "cdk-overlay-backdrop-showing")]'))
            )
            backdrop.click()
            return True
        except:
            return False

    def go_page_bottom(self):
        # 使用 JavaScript 将浏览器滚动到页面底部
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except:
            pass

    def go_page_top(self):
        # 使用 JavaScript 将浏览器滚动到页面底部
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
        except:
            pass


    def switch_to_home_page(self):
        """
        只有在home页下进行cookie切换
        """
        try:
            self.driver.get(gpt_conf.driver_default_page)
            return True
        except:
            return False

    def switch_to_chat_page(self):
        """
        设置token不需要检测用户是否登录。接口获取到后直接干
        """
        try:
            self.driver.get(gpt_conf.url)
            return True
        except:
            return False


    def switch_to_search_page(self):
        """
        切换
        """
        try:
            self.driver.get(gpt_conf.url)
            # 执行
            return True
        except:
            return False


    def check_black_page(self):
        """
        检测是否为空白页面url
        /?__cf_chl_rt_tk=dRDP9uzqdX58NB0Y6xs.NAHkLCUDsnipsCzaepA3wdQ-1745480589-1.0.1.1-y3ur4O86KtM4zHCi8.xzzDgprcWUe.Kukp45qBYr_aY
        标志：__cf_chl_rt_tk在url中则返回true

        """
        try:
            current_url = self.driver.current_url
            if "__cf_chl_rt_tk" in current_url:
                return True
            else:
                return False
        except:
            pass
        return False

    def check_black_page_by_content(self):
        idx = 0
        while True:
            idx = idx + 1
            if idx >3:
                return True
            time.sleep(5)
            try:
                text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
                if not text or len(text) == 0:
                    continue
                else:
                    return False
            except:
                continue


    def check_chat_page(self):
        return True if self.get_chat_input() else None


    def check_cf_robots(self):
        """
        直接通过cf 跳转的人工校验来确认
        """
        try:
            main_content = self.driver.find_element(By.CLASS_NAME, "main-content")
            h1_element = main_content.find_element(By.CLASS_NAME, "zone-name-title")
            h1_element.find_element(By.XPATH, "following-sibling::div")
            return True
        except:
            return False

    def check_pop_robots(self):
        """
        弹出窗口的人工校验
        """
        return False

    def check_robots(self):
        """
        任意一个都认为是人工校验 cf-turnstile
        # TODO 应该是sorry index 的一个
        """
        try:
            if "sorry/index" in self.driver.current_url:
                return False
            return True
        except:
            return False

    def close_other_tab(self):
        """
        关闭其他标签页
        """
        try:
            window_handles = self.driver.window_handles
            current_window = self.driver.current_window_handle
            if len(current_window) > 1:
                for handle in window_handles:
                    if handle != current_window:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                self.driver.switch_to.window(current_window)
        except:
            print(traceback.format_exc())

    def auto_robots(self):
        """
        TODO 需要校验和测试
        """
        idx = 0
        while True:
            idx = idx + 1
            if idx > 3:
                self.sysLog.log("---**人工校验异常，请联系管理员检测代码**--")
                return False
            if self.check_robots():
                try:
                    # 检测到人工校验，进行人工校验
                    drissObj = Driss(self.browser_port)
                    drissObj.to_click()
                    print("current robots OK, sleep 6s close other tab")
                    time.sleep(6)
                    tabs = self.driver.window_handles
                    if len(tabs) > 1:
                        keep_handle = tabs[1]
                        self.driver.switch_to.window(keep_handle)

                        # 遍历所有 tab，关闭非第二个 tab
                        for handle in tabs:
                            if handle != keep_handle:
                                self.driver.switch_to.window(handle)
                                self.driver.close()
                        self.driver.switch_to.window(keep_handle)
                    time.sleep(3)
                    self.switch_to_chat_page()
                    time.sleep(2)
                except:
                    continue
            else:
                return True

    # 自动化登录相关方法
    def login_step_check_use_google_login(self):
        """
        点击使用google登录
        """
        try:
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'ServiceLogin')]"))
            )
            return True
        except:
            return False

    def login_step_use_google_login(self):
        """
        点击使用google登录
        """
        try:
            google_button = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((
                By.XPATH,
                "//a[contains(@href, 'ServiceLogin')]"
            )))
            google_button.click()
            return True
        except:
            return False

    def login_step_check_use_other_account_login(self):
        """
        点击使用其他账号登录
        """
        try:
            current_url = self.driver.current_url
            if "v3/signin/accountchooser" in current_url:
                return True
            return False
        except:
            return False

    def login_step_use_other_account_login(self):
        """
        点击使用其他账号登录
        这里跟pplex不一样。有个隐藏的移除
        """
        try:
            other_accounts = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@role='link']")))
            other_accounts[-2].click()
            return True
        except:
            return False

    def login_step_check_input_email(self):
        """
        输入邮箱
        """
        try:
            # 等待最多 3 秒，找到并点击该输入框
            input_box = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[data-report-event="Signin_Email_Phone_Skype"]')
                )
            )
            return True
        except:
            return False

    def login_step_check_email_code_login(self):
        """
        输入邮箱
        """
        try:
            # 等待最多 3 秒，找到并点击该输入框
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(
                    (By.ID, 'proof-confirmation-email-input')
                )
            )
            if "oauth20_authorize" in self.driver.current_url:
                return True
            return False
        except:
            return False

    def login_step_skip_email_code_login(self):
        try:
            time.sleep(10)
            skip_link = self.driver.find_element(By.XPATH, """(//span[@data-testid="viewFooter"])[last()]//div/span""")
            time.sleep(5)
            self.driver.execute_script("arguments[0].click();", skip_link)
            return True
        except:
            return False

    def login_step_input_email(self, email):
        """
        输入邮箱
        """
        try:
            email_input = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[data-report-event="Signin_Email_Phone_Skype"]')
                )
            )
            time.sleep(3)
            email_input.click()
            time.sleep(2)
            for str_item in email:
                email_input.send_keys(str_item)
                utils.common.action_wait(30,120)
            return True
        except:
            return False

    def login_step_input_email_next(self):
        """
        输入邮箱后的下一步
        """
        try:
            next_button_email = email_input = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[data-report-event="Signin_Submit"]')
                )
            )
            time.sleep(3)
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button_email)
            self.driver.execute_script("arguments[0].click();", next_button_email)
            # next_button_email.click()
            return True
        except:
            return False

    def login_step_check_input_password(self):
        """
        输入密码
        """
        try:
            WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.ID, "passwordEntry")))
            return True
        except:
            return False

    def login_step_input_password(self, password):
        """
        输入密码
        """
        try:
            password_input = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, "passwordEntry")))
            time.sleep(3)
            password_input.click()
            time.sleep(2)
            password_input.send_keys(password)
            return True
        except:
            print(traceback.format_exc())
            return False


    def login_step_input_password_next(self):
        """
        输入密码后的下一步
        """
        try:
            next_button_password = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='primaryButton']")))
            time.sleep(3)
            next_button_password.click()
            return True
        except:
            return False


    def login_step_check_keep_login_status(self):
        """
        检测保持登录状态
        """
        try:
            if "ppsecure/post.srf" in self.driver.current_url:
                return True
            return False
        except:
            return False


    def login_step_check_login_status(self):
        """
        点击保持登录状态 是
        """
        try:
            confirm_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='primaryButton']")))
            time.sleep(3)
            confirm_button.click()
            return True
        except:
            return False


    def login_step_check_login_to_target(self):
        """
        点击继续，进入到目标网站
        该页面的协议加载需要一点时间，需要sleep5s 或者检测到目标数据不存在为止
        """
        try:
            current_url = self.driver.current_url
            if "signin/oauth/id" in current_url:
                return True
            return False
        except:
            return False

    def login_step_login_to_target(self):
        """
        点击继续，进入到目标网站
        该页面的协议加载需要一点时间，需要sleep5s 或者检测到目标数据不存在为止
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains

            actions = ActionChains(self.driver)
            actions.move_by_offset(10, 20).click_and_hold().pause(0.5)
            actions.move_by_offset(40, 20).pause(0.5)
            actions.release().perform()

            js = """
            var target = arguments[0];
            var rect = target.getBoundingClientRect();
            var x = rect.left + rect.width / 2;
            var y = rect.top + rect.height / 2;

            ['mouseover','mousedown','mouseup','click'].forEach(function(eventType) {
                var evt = new MouseEvent(eventType, {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: x,
                    clientY: y
                });
                target.dispatchEvent(evt);
            });
            """
            time.sleep(5)
            element = self.driver.find_elements(By.XPATH, "//div[@data-is-touch-wrapper='true']//button")[-1]
            self.driver.execute_script(js, element)
            return True
        except:
            return False

    def login_step_check_chat_with_aistudio(self):
        """
        这是已经跳转到 https://copilot.microsoft.com/ 这个页面了。需要点击 Chat With copilot 来进入聊天。但是不能直接url跳转进入

        """
        try:
            WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.TAG_NAME, "terms-of-service")))
            if self.login_step_check_use_aistudio() is False:
                return True
            return False
        except:
            return False

    def login_step_chat_with_aistudio(self):
        """
        这是已经跳转到 https://copilot.microsoft.com/ 这个页面了。需要点击 Chat With copilot 来进入聊天。但是不能直接url跳转进入
        """
        try:
            chat_with_aistudio = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//terms-of-service//button")))
            time.sleep(3)
            chat_with_aistudio.click()
            return True
        except:
            return False


    def login_step_check_use_aistudio(self):
        """
        这是已经跳转到 https://copilot.microsoft.com/ 这个页面了。需要点击 Chat With Gemini 来进入聊天。但是不能直接url跳转进入

        """
        try:
            WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.TAG_NAME, "terms-of-service-dialog")))
            return True
        except:
            return False

    def login_step_use_gemini(self):
        """
        这是已经跳转到 https://gemini.google.com/ 这个页面了。需要点击 Chat With Gemini 来进入聊天。但是不能直接url跳转进入
        """
        try:
            use_gemini = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//terms-of-service-dialog//button")))
            time.sleep(3)
            use_gemini.click()
            return True
        except:
            return False

    def login_step_check_welcome_got_it(self):
        try:
            WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.TAG_NAME, "mat-dialog-actions")))
            return True
        except:
            return False

    def login_step_welcome_got_it(self, waiting=15):
        try:
            welcome_got_it = WebDriverWait(self.driver, waiting).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-dialog-actions//button")))
            time.sleep(2)
            welcome_got_it.click()
            return True
        except:
            return False

    def check_google_captcha(self):
        """
        自动化解决google 的人工校验
        """
        time.sleep(3)
        if "challenge/recaptcha" in self.driver.current_url:
            return True
        return False

    def auto_accept_cookie(self):
        """
        接收cookie弹窗
        """
        try:
            # 等待 cookie_banner-description 元素出现
            desc_div = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cookie_banner-description"))
            )

            # 使用 XPath 查找下一个兄弟 div 元素
            sibling_div = desc_div.find_element(By.XPATH, 'following-sibling::div[1]')

            # 点击该兄弟元素
            sibling_div.click()
            return True

        except:
            return False

    def check_login_mark(self):
        """检测用户是否已经登录的标志"""
        try:
            self.driver.find_element(By.XPATH, "//div[@cdkoverlayorigin and @aria-label]")
            return True
        except:
            return False

    def get_login_mark(self):
        """
        1. url以 https://copilot.microsoft.com/ 这个开头
        2. 存在头像
        """
        try:
            time.sleep(3)
            login_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="settings-button"]')))
            login_btn.click()

            login_inner = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="settings-menu"]//div//button'))
            )

            email_info = login_inner.get_attribute('outerHTML')
            match = re.search(r'[\w\.-]+@[\w\.-]+', email_info)
            email = match.group(0)
            if email:
                return email.strip()
        except:
            print("get_login_mark error")
        return None


    def switch_model(self):
        """
        切换数据模型
        1. 先点击 class 为 gds-mode-switch-button 的button
        2. div class 为 title-and-description 并且包含 2.5 Pro 的元素点击
        """
        try:
            # 当默认下来打开的时候，直接点击会报错。先点击以下空白或者输入框然后点击就不会有问题
            try:
                self.get_chat_input().click()
                time.sleep(1)
            except:
                pass

            mode_switch_button = self.driver.find_element(By.CLASS_NAME, "gds-mode-switch-button")
            mode_switch_button.click()
            time.sleep(2)
            deep_button = self.driver.find_element(By.XPATH, "//div[contains(@class, 'title-and-description')][contains(., '2.5 Pro')]")
            deep_button.click()
            return True
        except Exception as e:
            print("----------切换 Model 失败")
            return False


    def get_current_model(self):
        """
        获取当前模型
        """
        try:
            model_dom = self.driver.find_elements(By.CSS_SELECTOR, 'div.model-option-content')
            model_text = model_dom[-1].text
            return model_text.strip().lower().replace(" ", "_")
        except Exception as e:
            print(traceback.format_exc())
            return "not_find"

    def select_deep_research(self):
        """
        切换deepresearch
        """
        try:
            target = self.driver.find_element(
                By.CSS_SELECTOR,
                'button:has(mat-icon[data-mat-icon-name="travel_explore"])'
            )
            target.click()
            return True
        except:
            print("----------切换 DeepResearch 失败")
            return False



    def check_something_error(self):
        """
        检测 something error 的情况。检测到该情况需要封锁该账号 1h
        """
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Something went wrong")]'))
            )
            return True
        except:
            return False


    def check_limited_info(self):
        try:
            # 最多等待10秒，直到页面中包含指定文本
            WebDriverWait(self.driver, 5).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "which is the maximum I can do at one time.")
            )
            return True
        except:
            return False

    def check_day_limited_info(self):
        try:
            # 最多等待10秒，直到页面中包含指定文本
            WebDriverWait(self.driver, 5).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "You've used all your research requests today")
            )
            return True
        except:
            return False

    def check_day_upgrade_limited_info(self):
        """
        触发升级限制： 提示限制了 并且有升级提示
        """
        try:
            # 最多等待10秒，直到页面中包含指定文本
            WebDriverWait(self.driver, 5).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "You've reached your limit of 20 research reports.")
            )
            return True
        except:
            return False

    def check_day_limited(self):
        if self.check_day_limited_info() or self.check_day_upgrade_limited_info():
            return True
        return False


    def check_not_start_research(self):
        try:
            # 最多等待10秒，直到页面中包含指定文本
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".retry-without-tool"))
            )
            return True
        except:
            return False

    def check_accept_terms_service(self, accept_terms_ts=10):
        try:
            time.sleep(accept_terms_ts)
            self.driver.find_element(By.ID, "mat-mdc-checkbox-0-input")
            return True
        except Exception as e:
            return False

    def accept_terms_service(self, accept_terms_ts=10):
        """
        我接受协议处理
        """
        idx = 0
        while True:
            idx = idx + 1
            try:
                if idx > 3:
                    return False

                # 点击 附加条款协议
                time.sleep(accept_terms_ts)
                checkbox = self.driver.find_element(By.ID, "mat-mdc-checkbox-0-input")
                self.driver.execute_script("arguments[0].click();", checkbox)
                utils.common.action_wait(1000,3000)
                self.sysLog.log("点击了附加条款协议按钮")

                # 点击 邮件通知协议
                checkbox2 = self.driver.find_element(By.ID, "mat-mdc-checkbox-1-input")
                self.driver.execute_script("arguments[0].click();", checkbox2)
                utils.common.action_wait(1000,3000)
                self.sysLog.log("点击了邮件通知协议按钮")

                # 点击我接受
                accept_button = self.driver.find_element(By.XPATH, "//div[@class='tos-actions']//button")
                # 点击按钮
                self.driver.execute_script("arguments[0].click();", accept_button)
                self.sysLog.log("点击了我接受按钮")
                return True
            except Exception as e:
                self.driver.refresh()
                time.sleep(5)
                continue


    def auto_restart_button(self):
        """
        检测是否有重新开始按钮，如果有则执行浏览器回退
        """
        return False

    def check_click_login_button(self):
        try:
            current_url = self.driver.current_url
            if current_url.startswith("https://copilot.microsoft.com"):
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'sign-in') and contains(., 'Sign in')]"))
                )
                return True
            return False
        except:
            return False

    def check_email_verification_code(self):
        """
        需要输入邮箱验证码，该账号作废
        检测验证码要等待3s
        """
        return False


    def check_email_recovery_identifier(self):
        """
        检测账号处于待恢复状态
        该状态下，账号其实是废了
        """
        try:
            if "/recover" in self.driver.current_url:
                self.driver.find_element(By.ID, "iLandingViewAction")
                return True
            return False
        except Exception as e:
            return False



    def auto_click_login_button(self):
        """
        检测页面是否为  https://copilot.microsoft.com/welcome  并且 存在登录按钮
        """
        try:
            button = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class, 'sign-in') and contains(., 'Sign in')]"
            )
            time.sleep(2)
            button.click()
            return True
        except:
            return False


    def option_select_flash_pre_0520(self):
        """
        切换到Gemini 2.5 Flash Preview 05-20模型
        """
        try:
            time.sleep(3)
            select_element = self.driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-select-arrow-wrapper")[-1]
            select_element.click()

            time.sleep(1)
            # 点击 id 为 mat-option-35 的元素
            # option_element = self.driver.find_elements(By.TAG_NAME, "ms-model-option")[-1]
            option_element = self.driver.find_element(By.XPATH, "//ms-model-option[contains(., '05-20')]")
            option_element.click()
            return True
        except Exception as e:
            return False

    def option_select_flash_pre_0617(self):
        """
        切换到Gemini 2.5 Flash Preview 05-20模型
        """
        try:
            time.sleep(3)
            select_element = self.driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-select-arrow-wrapper")[-1]
            select_element.click()

            time.sleep(1)
            # 点击 id 为 mat-option-35 的元素
            option_element = self.driver.find_element(By.XPATH, "//ms-model-option[contains(., 'Preview 06-17')]")
            option_element.click()
            return True
        except Exception as e:
            return False

    def option_select_pro_2_5(self):
        """
        切换到Gemini 2.5 Pro模型
        """
        try:
            time.sleep(3)
            element = self.driver.find_element(By.XPATH, "//*[contains(@class, 'mat-mdc-select-trigger')]")
            self.driver.execute_script("arguments[0].click();", element)

            time.sleep(1)
            option_element = self.driver.find_elements(By.TAG_NAME, "ms-model-option")[0]
            option_element.click()
            return True
        except Exception as e:
            return False

    def option_enable(self, toggle_button):
        idx = 0
        while 'mdc-switch--unselected' in toggle_button.get_attribute('class'):
            idx = idx + 1
            if idx >= 4:
                return False
            time.sleep(1)
            toggle_button.click()

            WebDriverWait(self.driver, 1).until(
                lambda d: 'mdc-switch--unselected' not in toggle_button.get_attribute('class')
                          or toggle_button.is_enabled()  # 确保不会卡死
            )
        return True

    def option_set_temperature(self):
        try:
            # 等待并找到 aria-label="Temperature" 的 <input> 元素
            temperature_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-test-id="temperatureSliderContainer"]//input[@type="range"]'))
            )
            # 方案1： 根据值：更精确的控制
            self.driver.execute_script("arguments[0].value = 0.5;", temperature_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                                       temperature_input)

            # 方案2： 使用 ActionChains 拖动滑块：该方案只能根据像素值来计算
            # from selenium.webdriver.common.action_chains import ActionChains
            # actions = ActionChains(driver)
            # actions.click_and_hold(temperature_input).move_by_offset(50, 0).release().perform()
            # 计算需要拖动的偏移量（示例：向右拖动 50 像素）
            # 注意：实际偏移量需要根据滑块的宽度或 min/max 值来动态计算

            return True

        except Exception as e:
            print("操作失败:", e)
            return False


    def option_set_thinking(self):
        try:
            parent_driver = self.driver.find_element(By.TAG_NAME, "ms-thinking-budget-setting")
            idx = 0
            while True:
                idx = idx + 1
                switch_buttons = parent_driver.find_elements(By.CSS_SELECTOR, 'button[role="switch"]')
                if len(switch_buttons) == idx:
                    switch_button = switch_buttons[idx-1]
                    if not self.option_enable(switch_button):
                        print("处理失败", switch_button.get_attribute('id'))
                        return False
                    print("处理成功", switch_button.get_attribute('id'))
                elif len(switch_buttons) < idx:
                    print("没有找到新的设置项")
                    break
                else:
                    continue


            print("set thinking mode and set thinking budget complete")
            time.sleep(2)
            temperature_input = parent_driver.find_element(By.CSS_SELECTOR, 'input[type="range"]')
            # 根据值：更精确的控制
            self.driver.execute_script("arguments[0].value = 99999;", temperature_input)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", temperature_input)

            print("set thinking-budget-Temperature complete")
            return True

        except Exception as e:
            print("操作失败:", e)
            return False

    def option_set_google_search(self):
        try:
            container = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="search-as-a-tool-toggle"]'))
            )
            search_button = container.find_element(By.CSS_SELECTOR, 'button')
            if not self.option_enable(search_button):
                print("处理失败", search_button.get_attribute('id'))
                return False
            return True

        except Exception as e:
            print("操作失败:", e)
            return False

    def waiting_response(self):
        """
        等待google aistudio回答结束
        """
        try:
            max_waiting_ts = 300
            current_ts = 0
            retry_num = 0
            while True:
                if current_ts % 10 == 0:
                    self.sysLog.log("正在回答中...")
                time.sleep(1)
                # 最大等待时间 300s
                if current_ts >= max_waiting_ts:
                    print(f"超过了最大等待时间{current_ts}/{max_waiting_ts}")
                    return True

                # 尝试30s 依旧报错，则认为回答有问题
                if retry_num >= 30:
                    return False

                current_ts = current_ts + 1
                try:
                    running_status = self.driver.find_element(By.CSS_SELECTOR, 'span.run-button-content')
                    running_text = running_status.text
                    if "ctrl" in running_text.lower():
                        self.sysLog.log("回答完毕")
                        return True
                except Exception as e:
                    retry_num = retry_num + 1
                    print(traceback.format_exc())
        except Exception as e:
            self.sysLog.log("waiting_response 操作失败:%s" % e)
            return False

    def get_response(self):
        """
        获取内容和引用
        内容分两种：纯html/纯文本  注意：纯文本主要用于提纲清洗

        返回：html text refs std_html
        """
        try:
            content_outers = self.driver.find_elements(By.CSS_SELECTOR, 'div.model-prompt-container')
            if len(content_outers) < 2:
                self.sysLog.log("get_response 没有获取到相应内容")
                return False

            content_outer = content_outers[-1]
            try:
                content_dom = content_outer.find_element(By.TAG_NAME, 'ms-cmark-node')
            except:
                content_dom = content_outer.find_element(By.XPATH, '//div[contains(@class, "very-large-text-container")]')

            # 引用不是必须的
            content_text = self.driver.execute_script("return arguments[0].innerText;", content_dom)

            # 引用不是必须的
            try:
                refs_dom = content_outer.find_element(By.TAG_NAME, 'ms-grounding-sources')
                refs_html = refs_dom.get_attribute('outerHTML')
            except:
                refs_html = ""
            return {
                "status": "success",
                "text": content_text,
                "origin_html": content_dom.get_attribute('outerHTML'),
                "refs_html": refs_html
            }

        except Exception as e:
            self.sysLog.log("get_response 操作失败: %s " % traceback.format_exc())
            # TODO debug
            return False

    def check_limited(self):
        try:
            errordom = self.driver.find_element(By.CSS_SELECTOR, "div.model-error")
            return True
        except:
            return False


    def check_search_input(self):
        """
        检测搜索输入框是否存在
        """
        try:
            textarea = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='q']"))
            )
            time.sleep(1)
            textarea.click()
            return True
        except:
            return False

    def get_search_input(self, query):
        """
        输入 query 进行查询
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='q']"))
            )
        except Exception as e:
            return None

    def get_search_hrefs(self):
        result_ele = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "search"))
        )

        links = result_ele.find_elements(By.TAG_NAME, "a")
        hrefs = [link.get_attribute("href") for link in links if link.get_attribute("href")]
        return hrefs





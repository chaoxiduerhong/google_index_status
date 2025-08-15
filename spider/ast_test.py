"""
https://copilot.microsoft.com/prompts/new_chat

登录相关测试


"""

import traceback
import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from fake_useragent import UserAgent


from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import time
import urllib.parse

print("start init")


def getDissDriver(port):
    from DrissionPage import ChromiumPage, ChromiumOptions, WebPage
    from DrissionPage.common import Keys, By
    co = ChromiumOptions()
    # 阻止“自动保存密码”的提示气泡
    co.set_pref('credentials_enable_service', False)
    # 阻止“要恢复页面吗？Chrome未正确关闭”的提示气泡
    co.set_argument('--hide-crash-restore-bubble')
    co_page = ChromiumOptions().set_local_port(port)
    return ChromiumPage(co_page)

def get_driver(port, browser_host="127.0.0.1"):
    """
    根据端口获取对应driver
    """
    # 浏览器信息配置
    browser_host = browser_host
    ua = UserAgent()
    random_ua = ua.random

    chrome_options = Options()
    chrome_options.ignore_local_proxy_environment_variables()
    chrome_options.add_argument(f'user-agent={random_ua}')
    # 以下为伪装非机器操作。大多数情况下可能没啥用。

    # 方案1
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # 添加参数以禁用信息条
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument("--disable-features=PrivacySandboxSettings3")  # 屏蔽 隐私权功能

    chrome_options.add_experimental_option("debuggerAddress", "%s:%s" % (browser_host, port))
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def google_auth_test():
    """
    将已经登录的导出到一个文本里面


    登录到其他浏览器测试

    1h - n天后登录到其他电脑测试

    导出的时候备注，那个电脑

    """
    driver = get_driver(9704)
    domains = [
        "https://copilot.microsoft.com"
    ]
    # 用于收集所有 cookie
    all_cookies = {}

    for domain in domains:
        try:
            driver.get(domain)
            cookies = driver.get_cookies()
            all_cookies[domain] = cookies
            print(f"✅ Collected {len(cookies)} cookies from {domain}")
        except Exception as e:
            print(f"❌ Failed to load {domain}: {e}")
    # 打印全部 cookie（可根据需要存为 JSON）
    print(json.dumps(all_cookies, indent=2))

    time.sleep(10)

    # 还原
    driver = get_driver(9600)
    driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    print("正在进行切换到浏览器2")
    for domain_url, cookies in all_cookies.items():
        driver.get(domain_url)
        for cookie in cookies:
            driver.add_cookie(cookie)
        time.sleep(1)  # 等页面加载
    # 最后访问 copilot 页面
    driver.get("https://copilot.microsoft.com/prompts/new_chat")
    print("切换完成")

    # 检测到关闭按钮，则执行关闭：mat-dialog-close button  包含属性


def login_step_use_other_account_login():
    """
    点击使用其他账号登录
    """
    driver = get_driver(9700)
    try:
        other_accounts = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='link']")))
        print(other_accounts[-2])

        html = other_accounts[-2].get_attribute("outerHTML")
        print(html)

        other_accounts[-2].click()
        print("----")
        return True
    except:
        print(traceback.format_exc())
        return False


def to_chat():
    driver = get_driver(9700)

    # 第一步：打开任意初始页面
    original_tab = driver.current_window_handle

    # 第二步：打开新 tab
    driver.execute_script("window.open('');")
    time.sleep(1)  # 稍等一下以确保新 tab 被创建

    # 获取所有 tab 句柄
    tabs = driver.window_handles

    # 第三步：切换到新 tab（最后一个）
    driver.switch_to.window(tabs[-1])
    driver.get("https://copilot.microsoft.com/app")

    # 第四步：关闭旧 tab
    driver.switch_to.window(original_tab)
    driver.close()

    # 第五步：切换回新 tab，继续操作
    driver.switch_to.window(tabs[-1])

    print(driver.current_url)

def login_step_chat_with_aistudio():
    """
    这是已经跳转到 https://copilot.microsoft.com/ 这个页面了。需要点击 Chat With copilot 来进入聊天。但是不能直接url跳转进入
    """
    try:
        driver = get_driver(9700)
        chat_with_aistudio = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//terms-of-service//button")))
        time.sleep(3)
        chat_with_aistudio.click()
        return True
    except:
        return False


def login_step_use_aistudio():
    """
    这是已经跳转到 https://copilot.microsoft.com/ 这个页面了。需要点击 Chat With copilot 来进入聊天。但是不能直接url跳转进入
    """
    try:
        driver = get_driver(9700)
        chat_with_aistudio = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//terms-of-service-dialog//button")))
        time.sleep(3)
        chat_with_aistudio.click()
        return True
    except:
        return False


def clear_local_cache():
    domains = [
        "https://copilot.microsoft.com",
        "https://ogs.google.com",
        "https://accounts.google.com"
    ]
    # 遍历每个域名并清除 cookie
    for domain in domains:
        driver = get_driver(9700)
        try:
            driver.get(domain)
            time.sleep(2)  # 可选：确保页面加载完成
            driver.delete_all_cookies()
            print(f"✅ Cleared cookies for {domain}")
        except Exception as e:
            continue
    return True

def clear_local():
    print("---start--")
    driver = get_driver(9704)
    print("---start--1")
    driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    print("---ttt---")
    driver.refresh()
    print("---END--")

def ask_js(ask_msg):
    """
    发起询问
    """
    try:
        print(ask_msg)
        driver = get_driver(9700)
        # 后期可以关闭，当前用于调试信息
        # 模拟点击文本框
        time.sleep(1)
        # 模拟手工输入操作
        parent_box = driver.find_element(By.CSS_SELECTOR, "rich-textarea.text-input-field_textarea")
        ql_editor = parent_box.find_element(By.CLASS_NAME, "ql-editor")
        # 获取该元素下的所有 <p> 子元素
        input_box = ql_editor.find_element(By.TAG_NAME, "p")
        input_box.click()
        print("=----------1------")
        if input_box:
            # 先清空输入框
            driver.execute_script("arguments[0].textContent = '';", input_box)
            driver.execute_script(f"arguments[0].textContent = `{ask_msg}`;", input_box)
            # 输入完毕，输入enter 获取点击相关按钮。这里当前按输入enter来确认
            print("=----------2------")
            input_box.send_keys(" ")
            time.sleep(2)
            print("=----------3------")
            # input_box.send_keys(Keys.ENTER)
            print("=----------4------")
            return True
        else:
            return False
    except:
        print(traceback.format_exc())
        return False

def switch_model():
    """
    切换数据模型
    1. 先点击 class 为 gds-mode-switch-button 的button
    2. div class 为 title-and-description 并且包含 2.5 Pro 的元素点击
    """
    try:
        driver = get_driver(9700)
        mode_switch_button = driver.find_element(By.CLASS_NAME, "gds-mode-switch-button")
        mode_switch_button.click()
        print("--------1-------")
        time.sleep(2)
        deep_button = driver.find_element(By.XPATH, "//div[contains(@class, 'title-and-description')][contains(., '2.5 Pro')]")
        deep_button.click()
        print("--------2-------")
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False

def select_deep_research():
    """
    切换deepresearch

    """
    try:
        driver = get_driver(9700)
        target = driver.find_element(
            By.CSS_SELECTOR,
            'button:has(mat-icon[data-mat-icon-name="travel_explore"])'
        )
        target.click()
        return True
    except:
        print("not find button")
        return False

def auto_start_research():
    """
    只有点了start research 才会开始
    """
    try:
        driver = get_driver(9701)
        confirm_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="confirm-button"]'))
        )
        time.sleep(2)
        confirm_button.click()
        return True
    except Exception as e:
        print("未找到 confirm-button 或等待超时：", e)
        return False


def get_content():
    driver = get_driver(9702)
    element = driver.find_element(By.XPATH, "//*[contains(@id, 'message-content-id-')]/div[1]")
    print(element.text)


def get_content_by_hs():
    """

    ---
    通过历史记录获取

    获取 tagname 为 c-wiz 节点下的 div纯文本为 Prompted Start research 的元素

    获取 tagname 为 c-wiz，并且属性包含data-date，纯文本包含Prompted Start research 的元素，最大等待时间 10s。 获取到该元素后，获取其 data-date值

    获取上面元素的下一个兄弟节点，提取纯文本，从纯文本中解析出日期：

    点击该兄弟节点 打开 item-details 页面

    获取i 元素，class="google-material-icons notranslate wpbf2" 并且纯文本为 chat的元素

    获取以上元素的下一个兄弟节点。

    该节点下 div 下 div 下 div为目标节点

    获取目标节点html内容

    内容解析：一个p元素不要  最后ul为引用。中间为正文

    ---
    先从数据库获取最近一条created_at 日期（中国时间） 获取该产品的产品名称
    解析完整个列表后，
    """
    def _pm_time_to_time(text):
        import re
        match = re.search(r"(\d{1,2}:\d{2})\s*[APap][Mm]", text)
        if match:
            time_str = match.group(0).replace("\u202f", " ")  # 替换窄不间断空格
            # 解析为 datetime 对象并转为 24小时格式
            time_24h = datetime.strptime(time_str.strip(), "%I:%M %p").strftime("%H:%M:%S")
            return time_24h
        else:
            return None

    from datetime import datetime
    driver = get_driver(9704)
    # driver.get("https://myactivity.google.com/product/copilot?utm_source=copilot")
    # 等待页面加载出至少一个目标元素（最多10秒）
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(
            By.XPATH,
            "//c-wiz[contains(@data-date, '') and @data-token and contains(., 'Prompted Start research')]"
        )) > 0
    )

    # 获取所有符合条件的 c-wiz 元素
    elements = driver.find_elements(
        By.XPATH,
        "//c-wiz[contains(@data-date, '') and @data-token and contains(., 'Prompted Start research')]"
    )

    for item in elements:
        item_data = {}
        date_str = item.get_attribute("data-date")
        data_day = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        full_time = f"{data_day} {_pm_time_to_time(item.text)}"

        item_data['text'] = item.text
        item_data['date'] = full_time

        print(item_data)
        sub_a = item.find_element(By.TAG_NAME, "a")
        sub_a.click()
        time.sleep(2)


def parse_refs(content):
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
                all_search_results[index] = link
            # print(f" {numbers[idx]}链接: {link}")
            idx = idx + 1
    return all_search_results

def get_api_content():
    """
    https://copilot.microsoft.com/_/BardChatUi/data/batchexecute?source-path=%2Fapp%2F61af540cba1dcbf5&hl=en
    """
    port = 9704
    uuid = "61af540cba1dcbf5"
    request_body = get_api_params(uuid=uuid, prot=port)

    driver = get_driver(port)
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
    result = driver.execute_async_script(post_script)

    refs = parse_refs(result)

    print(json.dumps(refs, indent=2))


def auto_restart_button():
    """
    检测是否有重新开始按钮，如果有则执行浏览器回退
    """
    try:
        driver = get_driver(9700)
        # 最长等待 10 秒直到某个 button 出现在页面上
        button = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//button[@data-mdc-dialog-action]"))
        )
        if button:
            print("加测到了")
            driver.back()
            return True
        print("未检测到")
        return False
    except Exception as e:
        print("出错：", e)
        return False

def login_step_welcome_got_it():
    try:
        driver = get_driver(9700)
        welcome_got_it = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//mat-dialog-actions//button")))
        time.sleep(3)
        welcome_got_it.click()
        return True
    except:
        return False


def get_chat_input():
    """
    获取聊天框
    最大等待5s
    """
    try:
        driver = get_driver(9700)
        input_box = driver.find_element(By.CSS_SELECTOR, "textarea.textarea")
        print("获取成功")
        ask_msg="hello"
        if input_box:
            # 先清空输入框
            driver.execute_script("arguments[0].textContent = '';", input_box)
            driver.execute_script(f"arguments[0].value = `{ask_msg}`;", input_box)
            # 输入完毕，输入enter 获取点击相关按钮。这里当前按输入enter来确认
            input_box.send_keys(" ")
            time.sleep(2)
            input_box.send_keys(Keys.CONTROL, Keys.ENTER)
        return input_box
    except Exception as e:
        return None

def accept_terms_service():
    """
    我接受协议处理
    """

    try:
        driver = get_driver(9700)
        # 点击 附加条款协议
        time.sleep(3)
        checkbox = driver.find_element(By.ID, "mat-mdc-checkbox-0-input")
        driver.execute_script("arguments[0].click();", checkbox)
        time.sleep(3)
        # print("点击了1")
        # # 点击 邮件通知协议
        checkbox2 = driver.find_element(By.ID, "mat-mdc-checkbox-1-input")
        driver.execute_script("arguments[0].click();", checkbox2)
        time.sleep(3)
        # print("点击了2")
        # 点击我接受
        accept_button = driver.find_element(By.XPATH, "//div[@class='tos-actions']//button")
        # 点击按钮
        accept_button.click()
        print("点击了3")
        return True
    except Exception as e:
        return False



def select_model():
    try:
        driver = get_driver(9600)
        # 等待并点击 id 为 mat-select-value-3 的元素（最多等待 5 秒）
        time.sleep(3)
        select_element = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-select-arrow-wrapper")[-1]
        select_element.click()

        time.sleep(1)
        # 点击 id 为 mat-option-35 的元素
        option_element = driver.find_elements(By.TAG_NAME, "ms-model-option")[-1]
        option_element.click()

    except Exception as e:
        print("操作失败:", e)


def option_set_temperature():
    from selenium.webdriver.common.action_chains import ActionChains

    try:
        driver = get_driver(9600)
        # 等待并找到 aria-label="Temperature" 的 <input> 元素
        temperature_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-test-id="temperatureSliderContainer"]//input[@type="range"]'))
        )

        # 方案1 使用 ActionChains 拖动滑块：该方案只能根据像素值来计算
        # from selenium.webdriver.common.action_chains import ActionChains
        # actions = ActionChains(driver)
        # actions.click_and_hold(temperature_input).move_by_offset(50, 0).release().perform()
        # 计算需要拖动的偏移量（示例：向右拖动 50 像素）
        # 注意：实际偏移量需要根据滑块的宽度或 min/max 值来动态计算

        # 根据值：更精确的控制
        driver.execute_script("arguments[0].value = 0.5;", temperature_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", temperature_input)

        return True

    except Exception as e:
        print("操作失败:", e)
        return False

def option_set_thinking():
    try:
        driver = get_driver(9600)
        # ms-thinking-budget-setting
        parent_driver = driver.find_element(By.TAG_NAME, "ms-thinking-budget-setting")
        def hand_set(toggle_button):
            # 2️⃣ 检查 class 属性
            idx = 0
            while 'mdc-switch--unselected' in toggle_button.get_attribute('class'):
                idx = idx + 1
                if idx >= 4:
                    return False
                time.sleep(1)
                toggle_button.click()

                # 重新获取按钮的 class 属性
                WebDriverWait(driver, 1).until(
                    lambda d: 'mdc-switch--unselected' not in toggle_button.get_attribute('class')
                              or toggle_button.is_enabled()  # 确保不会卡死
                )
            return True

        idx = 0
        while True:
            idx = idx + 1
            switch_buttons = parent_driver.find_elements(By.CSS_SELECTOR, 'button[role="switch"]')
            if len(switch_buttons) == idx:
                switch_button = switch_buttons[idx-1]
                if not hand_set(switch_button):
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
        driver.execute_script("arguments[0].value = 99999;", temperature_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", temperature_input)

        print("set thinking-budget-Temperature complete")
        return True

    except Exception as e:
        print("操作失败:", e)
        return False

def option_set_google_search():
    try:
        driver = get_driver(9600)
        def hand_set(toggle_button):
            # 2️⃣ 检查 class 属性
            idx = 0
            while 'mdc-switch--unselected' in toggle_button.get_attribute('class'):
                idx = idx + 1
                if idx >= 4:
                    return False
                time.sleep(1)
                toggle_button.click()

                # 重新获取按钮的 class 属性
                WebDriverWait(driver, 1).until(
                    lambda d: 'mdc-switch--unselected' not in toggle_button.get_attribute('class')
                              or toggle_button.is_enabled()  # 确保不会卡死
                )
            return True

        container = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="search-as-a-tool-toggle"]'))
        )

        # 2️⃣ 在该容器中找到 <button> 元素
        search_button = container.find_element(By.CSS_SELECTOR, 'button')
        if not hand_set(search_button):
            print("处理失败", search_button.get_attribute('id'))
            return False

        return True

    except Exception as e:
        print("操作失败:", e)
        return False


def waiting_response():
    """
    等待逻辑：

    先获取第一个的计时，第一个的停留10s不动，则监听第二个的 如果第二个不存在，再等30s如果还是不存在，则

    获取第二个 model-run-time-pill class
    如果时间在10s内没有任何变化，则获取到了
    """
    try:
        max_waiting_ts = 300
        current_ts = 0
        retry_num = 0
        driver = get_driver(9700)
        while True:
            time.sleep(1)
            # 最大等待时间 300s
            if current_ts >= max_waiting_ts:
                return True

            # 尝试30s 依旧报错，则认为回答有问题
            if retry_num >= 30:
                return False

            current_ts = current_ts + 1
            try:
                running_status = driver.find_element(By.CSS_SELECTOR, 'span.run-button-content')
                running_text = running_status.text
                if "ctrl" in running_text.lower():
                    print("回答完毕")
                    return True
                print("正在进行中...")
            except Exception as e:
                retry_num = retry_num + 1
                print(traceback.format_exc())
    except Exception as e:
        print("操作失败:", e)
        return False


def get_response():
    """
    获取内容和引用
    内容分两种：纯html/纯文本  注意：纯文本主要用于提纲清洗

    返回：html text refs std_html
    """
    try:
        driver = get_driver(port=9655)
        content_outer = driver.find_elements(By.CSS_SELECTOR, 'div.model-prompt-container')[-1]
        try:
            content_dom = content_outer.find_element(By.TAG_NAME, 'ms-cmark-node')
        except:
            content_dom = content_outer.find_element(By.XPATH, '//div[contains(@class, "very-large-text-container")]')

        refs_dom = content_outer.find_element(By.TAG_NAME, 'ms-grounding-sources')
        content_text = driver.execute_script("return arguments[0].innerText;", content_dom)

        print(content_text)

        try:
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
        print("操作失败:", e)
        return False

def get_current_mode():
    try:
        driver = get_driver(9700)
        model_dom = driver.find_elements(By.CSS_SELECTOR, 'div.model-option-content')
        model_text = model_dom[-1].text
        return model_text.strip().lower().replace(" ", "_")
    except Exception as e:
        print(traceback.format_exc())
        return False

def auto_login():
    driver = get_driver(9600)
    driver.get("https://copilot.microsoft.com/")
    cookies = [
    {
      "domain": ".google.com",
      "expiry": 1780025708,
      "httpOnly": True,
      "name": "__Secure-3PSIDCC",
      "path": "/",
      "sameSite": "None",
      "secure": True,
      "value": "AKEyXzU-jUdhmZo3CPYEDpUAMWAJa9i5Xm_55TcbWSA8Vn8rpvy6dJ2A6q8fRxd_UCy7E6IpNQ"
    },
    {
      "domain": ".google.com",
      "expiry": 1780025708,
      "httpOnly": True,
      "name": "__Secure-1PSIDCC",
      "path": "/",
      "sameSite": "Lax",
      "secure": True,
      "value": "AKEyXzWVgvY0TpIKq2t-NSuBfu2DaqpHjYaaF699NROjMgDiiYkSVK6G2iPmCXmhohjxtLT3"
    },
    {
      "domain": ".google.com",
      "expiry": 1780025708,
      "httpOnly": False,
      "name": "SIDCC",
      "path": "/",
      "sameSite": "Lax",
      "secure": False,
      "value": "AKEyXzWhmkMut1gFyvcm0jIvJGDppgdiNrLAphybj4_gNkVNUDGXIDnWqznqRNFy8ShxVfnnYw"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": False,
      "name": "APISID",
      "path": "/",
      "sameSite": "Lax",
      "secure": False,
      "value": "RBT6QJRhUhLrh4id/AcnYGQx_4jdTm7PbT"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": True,
      "name": "SSID",
      "path": "/",
      "sameSite": "Lax",
      "secure": True,
      "value": "AVnHtFxrBqJgRVeIh"
    },
    {
      "domain": ".google.com",
      "expiry": 1764300612,
      "httpOnly": True,
      "name": "NID",
      "path": "/",
      "sameSite": "None",
      "secure": True,
      "value": "524=FqwhbW6NpO0HY3RO641BRm0XJyJ_hy_7lTYj8vARcMKDqYqt3x5BQcAw0VRPwFXYIx9JM0q4iJsdioeAcsqNntGA4xMpMyuQbSsC5UzakikQl8M3WnwBAYK4wDAlaXU8xPinU3NW-Tsqqq6uCmEnaDfRAYLwu3Q7ok_l5rVtn-rfwL8QzLDUx5FClmtUWa2txRLhPqIcyRd-ank2izGTnnbcWFc2yhsaewbakdCxvqLnhtyAh-ROxxh7LjJW-w6eTbMHMEzRXI-WZebjfKeWQkjiEpHZrj7qSLf-zyslH8nv-YtzUB0IIXpBSF6FHpzBYtDCj9Ww4TRGk-gpiFGorJCfduCBn1z2Oh3HLt3QuOE8KPTG_ZmGKKs3pcFPfBF61vUELA5nYOzHvzJ1IqhmVDNaGygtZ7j97vSKykxYnM2aU8abt645F_YMlTtSkVf-Rxipv2PHEcsuq1iYuIAyw1tcn3FMVQ9r3cMofrRGB9pY_yJxVhPDDKlPNPnTsKfNLhAhVp4f6SGmgwv9Xu7uFE6iRkhj-lm7waobBC0u0BMIE9Y7MbwwnunbLCL9moGO5W6ArdieLgovvMgw7GQ7Y66GtQlNp9adJBKKF_5fM1pSg0_P73j8RJ00vm6BOvgJ"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": True,
      "name": "__Secure-3PSID",
      "path": "/",
      "sameSite": "None",
      "secure": True,
      "value": "g.a000xQiN9Z1JCwRJItF1xxiIiXu8ZzKRsh0GtPTJntsDhIryQWv6py3Kt2Lt0DFDUjzG5z3VJgACgYKAeoSAQ4SFQHGX2MiPMfqlmvAwkIChybNzhSqKRoVAUF8yKoIqfNVGKdRrLNcxh5ZLOSf0076"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": True,
      "name": "__Secure-1PSID",
      "path": "/",
      "sameSite": "Lax",
      "secure": True,
      "value": "g.a000xQiN9Z1JCwRJItF1xxiIiXu8ZzKRsh0GtPTJntsDhIryQWv6fO0fna-czaE-9dTlC0OdFQACgYKAQYSAQ4SFQHGX2Mi3_4-WqsJJXPwSrh52BawvBoVAUF8yKrV5uDWfA3h_abAfQ5bEifq0076"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": False,
      "name": "__Secure-3PAPISID",
      "path": "/",
      "sameSite": "None",
      "secure": True,
      "value": "m9bSNI_dLixvMIcR/A8nbeFQ1_LLL3XMnT"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": False,
      "name": "__Secure-1PAPISID",
      "path": "/",
      "sameSite": "Lax",
      "secure": True,
      "value": "m9bSNI_dLixvMIcR/A8nbeFQ1_LLL3XMnT"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": False,
      "name": "SID",
      "path": "/",
      "sameSite": "Lax",
      "secure": False,
      "value": "g.a000xQiN9Z1JCwRJItF1xxiIiXu8ZzKRsh0GtPTJntsDhIryQWv6t5q0I5mvhikHar88NriN1QACgYKAcsSAQ4SFQHGX2Miliyyn1UoS6_i4UyDEimvlRoVAUF8yKq_WUdVmZqhMJVMQDEP0q8q0076"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": False,
      "name": "SAPISID",
      "path": "/",
      "sameSite": "Lax",
      "secure": True,
      "value": "m9bSNI_dLixvMIcR/A8nbeFQ1_LLL3XMnT"
    },
    {
      "domain": ".google.com",
      "expiry": 1783049493,
      "httpOnly": True,
      "name": "HSID",
      "path": "/",
      "sameSite": "Lax",
      "secure": False,
      "value": "ApDJzwNBLDRIxLvwD"
    }
  ]
    driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    for cookie in cookies:
        driver.add_cookie(cookie)
    time.sleep(1)  # 等页面加载


    print("设置完成")


def check_click_login_button():
    try:
        driver = get_driver(9600)
        current_url = driver.current_url
        if current_url.startswith("https://copilot.microsoft.com"):
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'sign-in') and contains(., 'Sign in')]"))
            )
            print("检测到了登录")
            return True
        return False
    except:
        return False

def auto_click_login_button():
    """
    检测页面是否为  https://copilot.microsoft.com/welcome  并且 存在登录按钮
    """
    try:
        driver = get_driver(9600)
        button = driver.find_element(
            By.XPATH,
            "//button[contains(@class, 'sign-in') and contains(normalize-space(text()), 'Sign in')]"
        )
        time.sleep(2)
        button.click()
        return True
    except:
        return False


def check_email_verification_code():
        """
        需要输入邮箱验证码，该账号作废
        """
        try:
            driver = get_driver(9700)
            current_url = driver.current_url
            if "signin/challenge/selection" in current_url:
                return True
            return False
        except:
            return False


def option_select_flash_pre_0520():
    """
    切换到Gemini 2.5 Flash Preview 05-20模型
    """
    try:
        driver = get_driver(9600)
        time.sleep(3)
        select_element = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-select-arrow-wrapper")[-1]
        time.sleep(1)
        select_element.click()

        time.sleep(2)
        # 点击 id 为 mat-option-35 的元素
        # option_element = driver.find_elements(By.TAG_NAME, "ms-model-option")[-2]
        option_element = driver.find_element(By.XPATH, "//ms-model-option[contains(., '05-20')]")
        time.sleep(1)
        option_element.click()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def option_select_pro_2_5():
    """
    切换到Gemini 2.5 Pro模型
    """
    try:
        driver = get_driver(9600)
        time.sleep(3)
        element = driver.find_element(By.XPATH, "//*[contains(@class, 'mat-mdc-select-trigger')]")
        driver.execute_script("arguments[0].click();", element)

        time.sleep(1)
        option_element = driver.find_elements(By.TAG_NAME, "ms-model-option")[0]
        option_element.click()
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def login_step_skip_email_code_login():
        try:
            time.sleep(1)
            driver = get_driver(9600)
            print("-------1-")
            skip_link = driver.find_element(By.XPATH, """(//span[@data-testid="viewFooter"])[last()]//div/span""")
            time.sleep(2)
            print("-------3-")
            driver.execute_script("arguments[0].click();", skip_link)
            print("-------4-")
            # skip_link.click()
        except:
            print(traceback.format_exc())
            return False

def login_step_check_login_status():
    """
    点击保持登录状态 是
    """
    try:
        driver = get_driver(9600)
        confirm_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='primaryButton']")))
        time.sleep(3)
        confirm_button.click()
        return True
    except:
        return False

def sync_localstorage():
    try:
        driver1 = get_driver(9600)
        driver1.get("https://copilot.microsoft.com/")
        local_storage_data = driver1.execute_script(
            "var items = {}; "
            "for (var i = 0; i < localStorage.length; i++) { "
            "  var key = localStorage.key(i); "
            "  items[key] = localStorage.getItem(key); "
            "} "
            "return items;"
        )

        print(local_storage_data)
        driver2 = get_driver(9700)
        driver2.get("https://copilot.microsoft.com/")
        for key, value in local_storage_data.items():
            driver2.execute_script(f"localStorage.setItem({repr(key)}, {repr(value)})")
    except:
        return False



def switch_to_login_page():
    """
    切换
    """
    try:
        driver = get_driver(9700)
        # 登录入口按钮
        login_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="settings-button"]')))
        login_btn.click()
        time.sleep(2)

        # 登录界面进入按钮
        login_btn2 = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//div[@data-testid="settings-menu"]//button[@title="Sign in" or @title="登录" or @title="Login"]')
            )
        )
        login_btn2.click()
        time.sleep(2)

        # 正式进入了登录界面，点击 通过Microsoft按钮
        ms_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//div[contains(@class, "max-h-dvh")]//button[contains(@title, "Microsoft")]')
            )
        )
        ms_button.click()
        time.sleep(2)

        # 检测url中是否包含了 login.microsoftonline.com 这个字符，如果包含，进入登录界面成功，否则返回False
        current_url = driver.current_url
        if "login.microsoftonline.com" in current_url:
            return True

        print("当前登录界面中url中不存在 login.microsoftonline.com, 请检查进入登录页面代码")
        # 执行
        return False
    except:
        print(traceback.format_exc())
        return False


def check_email_recovery_identifier():
    """
    检测账号处于待恢复状态
    该状态下，账号其实是废了
    """
    driver = get_driver(9700)
    try:
        if "/recover" in driver.current_url:
            driver.find_element(By.ID, "iLandingViewAction")
            return True
        return False
    except Exception as e:
        return False

def get_login_mark():
    """
    1. url以 https://copilot.microsoft.com/ 这个开头
    2. 存在头像
    """
    try:
        driver = get_driver(9600)
        time.sleep(3)
        login_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="settings-button"]')))
        login_btn.click()
        time.sleep(3)

        login_inner = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="settings-menu"]//div//button'))
        )

        email_info = login_inner.get_attribute('outerHTML')
        match = re.search(r'[\w\.-]+@[\w\.-]+', email_info)

        email = match.group(0)
        if email:
            return email.strip()
    except:
        print(traceback.format_exc())
        print("get_login_mark error")
    return None


def check():
    """
    https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyAJAQ_vp1bhYBVemESz3W9ZAz66Zw577dw
    根据这个接口来了检测

    从所有的keys中随机获取一个

    """
    try:
        proxy = f"http://127.0.0.1:10809"

        # TODO 这里的key设置在配置文件。当前用的是备用账号。
        url = "https://copilot.microsoft.com/"
        proxy_address = proxy
        response = requests.get(url, verify=False,
                                proxies={"http": proxy_address, "https": proxy_address}, timeout=5)
        if response.status_code == 200:
            return True
        return False
    except:
        print(traceback.format_exc())
        return False


def auto_robots():
    """
    自动化人工点击
    """
    driver = getDissDriver(9600)
    try:
        dom = driver. \
            ele((By.ID, "recaptcha")). \
            ele((By.TAG_NAME, "div")).ele((By.TAG_NAME, "div")). \
            ele((By.TAG_NAME, "iframe")).ele((By.ID, "recaptcha-anchor"))
        dom.click()
        return True
    except:
        print(traceback.format_exc())
        return False


auto_robots()

print("end")
time.sleep(100000)
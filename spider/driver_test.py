import time
import traceback
import re
from flask import request
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.webdriver.common.keys import Keys
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
from playwright.sync_api import sync_playwright
import time
import urllib.parse


print("start init")
def get_driver(port):
    """
    根据端口获取对应driver
    """
    # 浏览器信息配置
    browser_host = "127.0.0.1"
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
    1. 获取浏览器9700的所有cookie
    2. 导入到9701
    """
    driver = get_driver(9700)
    domains = [
        "https://copilot.microsoft.com",
        "https://ogs.google.com",
        "https://myaccount.google.com"
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
            cookie.pop('domain', None)
            driver.add_cookie(cookie)
        time.sleep(1)  # 等页面加载
    # 最后访问 copilot 页面
    driver.get("https://copilot.microsoft.com")
    print("切换完成")


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

def get_chat_input():
    """
    获取聊天框
    最大等待5s
    """
    driver = get_driver(9700)
    try:
        return WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "rich-textarea.text-input-field_textarea"))
        )
    except Exception as e:
        print("===============1")
        return None


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



def google_login_test12():
    driver = get_driver(9600)
    driver.get("https://copilot.microsoft.com/")
    all_cookies = {}
    driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    print("正在进行切换到浏览器2")
    for domain_url in all_cookies:
        driver.get(domain_url)
        cookies = all_cookies[domain_url]
        for cookie in cookies:
            print(cookie, "==")
            # if "google"
            cookie.pop('domain', "accounts.google.com")
            driver.add_cookie(cookie)

        time.sleep(1)  # 等页面加载
    # 最后访问 copilot 页面
    driver.get("https://copilot.microsoft.com")

    print("设置完成")


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


def get_api_params(uuid="61af540cba1dcbf5", prot=9704):
    """
    获取请求参数
    """

    captured_result = {"fr_content": None, "fr_url": None}
    TARGET_URL = "https://gemini.google.com/_/BardChatUi/data/batchexecute"

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

                print("✅ 已捕获目标 f.req：\n", body)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{prot}")
        context = browser.contexts[0]
        page = context.pages[0]

        page.on("request", on_request)
        page.goto("https://gemini.google.com/app/%s" % uuid)

        print("⏳ 请手动触发聊天或加载对话以触发请求...")

        # ✅ 等待最多 30 秒，轮询检测
        max_wait_seconds = 30
        waited = 0
        while captured_result["fr_content"] is None and waited < max_wait_seconds:
            time.sleep(1)
            waited += 1
            print(f"⏳ 正在监听请求...（{waited}s）")

        if captured_result["fr_content"]:
            print("\n🎯 获取到的 f.req 内容如下：")
            print(captured_result["fr_content"])
        else:
            print("\n❌ 超时未捕获到目标 f.req 请求！")
        # 关闭 playwright 和浏览器的链接
        browser.close()
        return captured_result

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
    https://gemini.google.com/_/BardChatUi/data/batchexecute?source-path=%2Fapp%2F61af540cba1dcbf5&hl=en
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

get_api_content()

time.sleep(100000)
# -*- coding:utf-8 -*-
# Desc: project app configuration
"""
"""
from utils import env, template
import subprocess,re

class gptConf:

    # --------------------- -*- 基础配置 -*- ---------------------
    debug: bool = bool(int(env("DEBUG", 0)))

    # 输入类型 letter(字母), word（单词）, sentence（句子）
    input_type = env("INPUT_TYPE", "sentence")

    # 项目名称
    project_name = env("project_name", "google_index_status")

    # 日志文件存储路径
    log_file_path = env("log_file_path", project_name)

    error_log_file_path = env("error_log_file_path", f"{project_name}_error")

    log_root = env("log_root", f"./storage/logs/{project_name}")

    start_bid_file = env("start_bid_file", project_name)

    browser_config_path = env("browser_config_path", "browser")

    proxy_config_path = env("proxy_config_path", "proxy")

    browser_status_file_path = env("browser_status_file_path", "browser_status")

    proxy_stop_queue_file = env("proxy_stop_queue_file", "stop_proxy_queue")



    chrome_executable_path = env("chrome_executable_path", "C:/Program Files/Google/Chrome/Application/chrome.exe")

    # 用户浏览器数据
    browser_data_path = env("browser_data_path", "D:/dev/perplexity_spider_start")

    # 源数据表
    product_queue_table = env("PRODUCT_TABLE", "product_ast_bench_outline_detail_full")

    # 待注册邮箱队列表
    email_queue_table = env("EMAIL_QUEUE_TABLE", "email_addr")

    # 注册邮件临时存储表- 临时 TODO invalid
    copilot_auth_table = env("copilot_AUTH_TABLE", "copilot_auth")

    # 注册邮件存储到目标浏览器账号表- 正式 - 临时 TODO invalid
    copilot_browser_auth_table = env("copilot_BROWSER_AUTH_TABLE", "copilot_browser_auth_data")

    # 爬取产品结果为失败表
    product_table_result_failed = env("PRODUCT_FAILED_RESULT_TABLE", "product_google_index_status_failed")
    # 异步获取产品 TODO invalid
    product_table_result_failed_async = env("PRODUCT_FAILED_ASYNC_RESULT_TABLE", "product_copilot_failed_async")

    # 爬取产品结果成功表
    product_table_result = env("PRODUCT_RESULT_TABLE", "product_google_index_status")
    # 将所有的数据整合到一起 合并表 TODO invalid
    product_table_result_full = env("PRODUCT_RESULT_TABLE_FULL", "product_ast_bench_outline_detail_full")

    # 避免重复多次爬取同一个链接。这里将已经爬取到的存储到数据库中 TODO invalid
    product_table_result_urls = env("PRODUCT_RESULT_TABLE_URLS", "google_ast_urls")

    # 账号对列表 TODO invalid
    auth_data_table = env("AUTH_DATA_TABLE", "copilot_browser_auth_data")

    # 是否启用将失败的数据保存到失败表中。如果保存到失败表中会一直重新尝试该数据，直到失败。0启用，0关闭 TODO invalid
    is_save_failed_to_table = bool(int(env("is_save_failed_to_table", 0)))

    # 是否固定运行时长
    # is_fixed_running_time = bool(int(env("is_fixed_running_time", 0)))
    is_fixed_running_time = True

    # 固定运行时长周期
    fixed_running_loop_ts = 20  # 15 0windows, total 25.9w/day

    fixed_running_loop_for_login = 20  # 150windows, total 25.9w/day

    fixed_running_loop_ts_async = int(env("fixed_running_loop_ts_async", 20))

    # 入口
    url = "https://www.google.com/"
    # login 如果未登录，会跳转到登录界面 TODO invalid
    login_url = "https://copilot.microsoft.com/login"

    # 设置一个dirver 初始化后默认的页面
    driver_default_page = "https://www.google.com/"

    # TODO invalid
    ask_template = template(env("template_name", "template"))
    # 后面需要配置多个端口，同时登录，同时开启
    # --------------------- -*- 浏览器窗口相关配置 -*- ---------------------
    # 浏览器窗口
    window_x = int(env("window_x", 300))
    window_y = int(env("window_y", 250))
    window_rate = env("window_rate", 1)

    # 浏览器排列x位置
    position_x = int(env("position_x", 0))
    # 浏览器排列y位置
    position_y = int(env("position_y", 1))
    # 起始id
    position_start_id = int(env("position_start_id", 0))
    # 每行排列的数量：
    max_x_id = int(env("max_x_nums", 5))
    # 宽度
    window_width = int(env("window_width", 515))
    # 高度
    window_height = int(env("window_height", 250))
    # 最小限制 ID
    client_min_bid = int(env("CLIENT_MIN_BID", 0))
    # 最大限制 ID
    client_max_bid = int(env("CLIENT_MAX_BID", 9999999))

    product_name_len_lte = int(env("product_name_len_lte", 10))

    # 最小限制 ID
    client_min_bid_for_queue = int(env("CLIENT_MIN_BID_FOR_QUEUE", client_min_bid))
    # 最大限制 ID
    client_max_bid_for_queue = int(env("CLIENT_MAX_BID_FOR_QUEUE", client_max_bid))

    proxy_source_type = env("proxy_source_type", "") # "anyland", "jikeyun", feijiyunduijie-lz, tagss, suyunti, lanfan
    proxy_countries = env("proxy_countries", "") # "hk,tw"

    # 禁用的，多个用逗号隔开
    dis_source_type = env("dis_source_type", "")

    clear_cache = env("clear_cache", True)

    need_switch_language_model = bool(int(env("need_switch_language_model", 1)))

    # pro账号最大限制 500
    account_day_max_req_num_for_pro=int(env("account_day_max_req_num_for_pro", 500))
    # custom 普通账号最大3次
    account_day_max_req_num_for_custom = int(env("account_day_max_req_num_for_custom", 500))

    # 按时间分区。不同时间点跑不同的账号 TODO invalid
    is_token_auto_login = bool(int(env("is_token_auto_login", True)))
    # token/file 每次获取最新的token文件 文件：9600-1/9600-2  9601-1/9601-2  不存在则从原始的key文件中获取
    origin_token_file = env("origin_token_file", "origin_tokens")
    new_token_file = env("new_token_file", "./storage/data/token")

    is_save_log= bool(int(env("is_save_log", 0)))

    @staticmethod
    def get_proxy_server_ipv4():
        ipv4 = None
        try: # 使用 ping -4 命令，并捕获输出
            process = subprocess.Popen(['ping', '-4', 'dell-mini-1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            # 将输出转换为字符串，并使用正则表达式提取 IPv4 地址
            stdout_str = stdout.decode('gbk')  # 注意编码，windows中文系统一般为gbk
            ipv4_match = re.search(r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]', stdout_str)

            if ipv4_match:
                ipv4 = ipv4_match.group(1)
                print(f"成功获取 proxy-server IPv4 地址: {ipv4}")
        except Exception as e:
            print(f"获取 proxy-server IPv4 地址时发生错误：{e}")
        if not ipv4:
            ipv4 = env("proxy_server", "127.0.0.1")

        return ipv4

    # proxy_server = get_proxy_server_ipv4()
    # 代理 server 服务器
    proxy_server = env("proxy_server", "127.0.0.1")

    proxy_server_for_login = env("proxy_server_for_login", f"{proxy_server}")

    # 代理主机ip地址
    proxy_host = env("proxy_host", proxy_server)

    # 远程服务器地址：
    remote_server = env("remote_server", f"http://{proxy_server}:8053")

    # 远程服务器地址：
    remote_server_for_login = env("remote_server_for_login", f"http://{proxy_server_for_login}:8053")

    # webdirver 拦截地址  TODO 如果启用，以下方案需要验证。当前只是修改了域名，并没有实际校验过
    # interceptor_urls = [
    #     "copilot.google.com/cdn-cgi/challenge-platform/*"
    # ]

    interceptor_urls = []
    # TODO invalid
    query_link_thread_num = int(env("query_link_thread_num", 10))
    # TODO invalid
    query_link_start_time = int(env("query_link_start_time", 1750039260402494))
    # TODO invalid
    query_link_end_time = int(env("query_link_end_time", 1750384860706470))

    # 详情爬取模式 新增：add 补充：fill，新增+补充： add_fill TODO invalid
    query_detail_mode = env("query_detail_mode", "add")

    # 登录补号模式 waiting 和disabled模式
    # waiting  未触发登录验证码的账号
    # disabled 触发过登录验证码的账号 TODO invalid
    login_status_mode = env("login_status_mode", "waiting")



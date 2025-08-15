"""
浏览器管理 - 远端的

基本功能：主要为GPTRobots提供服务。多余接口移除
但是所有的改动都改动的是数据库或者调用的远程接口来处理。而非本地

"""
import signal, psutil
import json
import time
import os, inspect
import shutil
import utils
import requests
from threading import Thread
from config import gpt_conf
from config import browser_conf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def async_call(fn):
    """
    异步调用
    """

    def wrapper(*args, **kwargs):
        Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper


class BitBrowserManager:
    def __init__(self):
        self.browser_config_path = gpt_conf.browser_config_path
        self.proxy_config_path = gpt_conf.proxy_config_path
        self.bit_url = "http://127.0.0.1:54345"
        self.headers = {'Content-Type': 'application/json'}
        self.chrome_executable = gpt_conf.chrome_executable_path
        self.browser_data_path = gpt_conf.browser_data_path
        # gs 走的是 vmess ,v2ray 是 shadowsocks 协议
        self.proxy_mode = "vmess"
        # v2ray base_template.json
        self.proxy_template = "base_template_vmess.json"
        self.mode = "remote"


    def bit_open_browser(self, port, proxy_port=None):
        """
        创建并且打开浏览器
        """
        json_data = {
            'name': 'G-%s' % port,  # 窗口名称
            'remark': port,  # 备注
            'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
            # 代理类型  ['noproxy', 'http', 'https', 'socks5', 'ssh']
            'proxyType': 'http',
            'host': gpt_conf.proxy_host,  # 代理主机
            'port': proxy_port,  # 代理端口
            'proxyUserName': '',  # 代理账号
            "browserFingerPrint": {  # 指纹对象
                'coreVersion': '124'  # 内核版本，注意，win7/win8/winserver 2012 已经不支持112及以上内核了，无法打开
            }
        }
        res = requests.post(f"{self.bit_url}/browser/update",
                            data=json.dumps(json_data), headers=self.headers).json()
        browserId = res['data']['id']
        json_data = {"id": f'{browserId}'}
        res = requests.post(f"{self.bit_url}/browser/open",
                            data=json.dumps(json_data), headers=self.headers).json()
        if res:
            res['data']['id'] = browserId
        return res['data']

    def get_config(self, port):
        """
        一个浏览器一个配置文件。
        配置文件名称规范： bit_9600
        """
        port = str(port)
        browser_config_path = f"bit_{port}"
        data = utils.get_setting(browser_config_path)
        if not data:
            data = {}
        return data


    def save_config(self, port, config):
        """
        一个浏览器一个配置文件。
        配置文件名称规范： bit_9600

        {
            代理信息
            pid
            browser_id
        }
        """
        port = str(port)
        browser_config_path = f"bit_{port}"
        if not config:
            config = {}
        return utils.save_setting(browser_config_path,  config)

    def start_browser(self, port, proxy_port=None):
        """
        检测浏览器端口是否启动。如果未启动则启动，并且更新pid。
        如果已经去启动，则跳过。
        """
        return self.bit_open_browser(port, proxy_port)


    def open_browser(self, port, proxy_port=None):
        """
        检测浏览器端口是否启动。如果未启动则启动，并且更新pid。
        如果已经去启动，则跳过。
        """
        return self.start_browser(str(port), proxy_port)


    @staticmethod
    def std_browser_user(item, data):
        if "port" not in data:
            return None
        if not data['status']:
            return None
        if data['status'] != "actived":
            return None
        if "host" not in data or not data['host']:
            data['host'] = "127.0.0.1"
        if "proxy" not in data or not data['proxy']:
            data['proxy'] = None
        if "proxy_name" not in data or not data['proxy_name']:
            data['proxy_name'] = None
        if "name" not in data or not data['name']:
            data['name'] = item
        return data

    @staticmethod
    def kill_process_and_children_by_pid(parent_pid):
        """
        通过pid杀死进程以及子进程
        """
        is_ok = False
        try:
            # 获取父进程
            parent = psutil.Process(parent_pid)
            # 获取父进程的所有子进程（包括孙子进程等）
            children = parent.children(recursive=True)
            # 创建一个包含父进程PID的列表
            pids_to_kill = [parent_pid]
            # 将所有子进程的PID添加到列表中
            pids_to_kill.extend(child.pid for child in children)
            # 遍历列表，对每个PID发送SIGKILL信号
            for pid in pids_to_kill:
                try:
                    os.kill(pid, signal.SIGILL)
                    is_ok = True
                except PermissionError:
                    # 忽略权限错误，可能我们没有权限杀死某个进程
                    # print("close browser PermissionError")
                    pass
                except ProcessLookupError:
                    # 忽略进程查找错误，进程可能已经自然死亡
                    # print("close browser ProcessLookupError")
                    pass
                except:
                    pass
        except (psutil.NoSuchProcess, PermissionError):
            # 忽略错误，如果进程不存在或者没有权限
            # print("close browser PermissionError1")
            is_ok = False
        return is_ok

    @staticmethod
    def kill_process_and_children_by_port(port):
        """
        根据端口号查找占用该端口的进程，并杀死该进程及其所有子进程。
        """
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                connections = proc.connections(kind='inet')
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue  # 跳过无权限或已终止的进程
            except Exception as e:
                continue
            for conn in connections:
                if conn.laddr.port == int(port):
                    found = True
                    try:
                        parent_proc = psutil.Process(proc.pid)
                        # 非 chrome.exe 跳过。 避免误杀
                        if parent_proc.name() != "chrome.exe":
                            continue

                        children = parent_proc.children(recursive=True)
                        if children:
                            for child in children:
                                try:
                                    child.kill()
                                    # print(f"子进程 {child.pid} ({child.name()}) 已被杀死.")
                                except psutil.NoSuchProcess:
                                    pass
                                    # print(f"子进程 {child.pid} 已不存在.")
                                except psutil.AccessDenied:
                                    pass
                                    # print(f"没有权限杀死子进程 {child.pid} ({child.name()}).")
                                except Exception as e:
                                    pass
                                    # print(f"无法杀死子进程 {child.pid} ({child.name()}): {e}")
                        parent_proc.kill()

                        # print(f"端口 {port} 上的进程 {parent_proc.pid} ({parent_proc.name()}) 已被杀死.")
                        return True
                    except psutil.NoSuchProcess:
                        pass
                        # print(f"进程 {proc.pid} 已不存在.")
                    except psutil.AccessDenied:
                        pass
                        # print(f"没有权限杀死进程 {proc.pid} ({proc.name()}).")
                    except Exception as e:
                        pass
                        # print(f"无法杀死进程 {proc.pid} ({proc.name()}): {e}")
                    # TODO 假设一个端口只有一个相关进程，如有多个，请调整逻辑： 1. 取消return 终止 2. 所有循环结束在杀死父进程
                    return False
        if not found:
            pass
            # print(f"未找到使用端口 {port} 的进程.")
        return False

    def force_close(self, parent_pid, port):
        """
        强制杀死某个进程以及其子进程
        """
        if not parent_pid:
            return
        parent_pid = int(parent_pid)
        port = str(port)
        ret1 = self.kill_process_and_children_by_port(port)
        ret2 = self.kill_process_and_children_by_pid(parent_pid)
        time.sleep(10)
        return ret1 or ret2

    def load_conf(self):
        """
        读取配置文件内容 storage/data/browser.json 
        """
        return utils.get_setting(self.browser_config_path)

    def get_list(self, all_browser_on_host=False):
        """
        启动浏览器：获取启动的pid，更新配置文件
        """
        browser_data = browser_conf.browser_user

        # browser.json 中的
        local_list = self.load_conf()
        number_of_local_conf = len(local_list)
        caller_name = inspect.currentframe().f_back.f_code.co_name
        utils.log(
            f"[tricky] caller[{caller_name}] -> current[browser.py.get_list().load_conf()] - number_of_local_conf {number_of_local_conf}")

        browser_list = browser_data.copy()

        # 补充pid
        for key_in_browser_json in local_list:
            if (key_in_browser_json in browser_data and
                    browser_data[key_in_browser_json]['status'] == "actived" and
                    key_in_browser_json in browser_list):
                browser_data[key_in_browser_json] = local_list[key_in_browser_json]

        result = []
        for item in browser_data:
            browser = self.std_browser_user(item, browser_data[item])
            if browser:
                browser['running_status'] = "未知"
                browser['running_time'] = "未知"
                browser_status = utils.get_setting(gpt_conf.browser_status_file_path, item)
                if browser_status:
                    if "running_status" in browser_status:
                        browser['running_status'] = browser_status['running_status']
                    if "running_time" in browser_status:
                        browser['running_time'] = browser_status['running_time']
                if "pid" in browser and browser['pid'] and psutil.pid_exists(int(browser['pid'])):
                    browser['process_status'] = "已打开"
                else:
                    browser['process_status'] = "已关闭"
                result.append(browser)
        return result

    def get_browser(self, port):
        """
        根据端口获取浏览器
        """
        all_data = self.get_list()
        for item in all_data:
            if item['port'] == int(port):
                return item
        return {}

    def stop_browser(self, uid, pid=None):
        """
        关闭浏览器窗口 + 删除窗口
        如果关闭失败，可以尝试pid来强制关闭

        两个接口返回成功接口均是： {'success': True, 'data': '操作成功'}
        """
        if uid:
            print("------************---》 开始重启浏览器，发起定制", uid)
            json_data = {'id': f'{uid}'}
            ret1 = requests.post(f"{self.bit_url}/browser/close", data=json.dumps(json_data), headers=self.headers).json()
            print("关闭浏览器返回的数据集", ret1)
            json_data = {'id': f'{uid}'}
            ret2 = requests.post(f"{self.bit_url}/browser/delete", data=json.dumps(json_data), headers=self.headers).json()
            print("删除浏览器返回的数据集", ret2)



    @async_call
    def browser_resize(self, port, xid=0, yid=1):
        # 暂时保留。用于后期动态设置浏览器位置
        window_width = gpt_conf.window_width
        window_height = gpt_conf.window_height
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "%s:%s" % ("127.0.0.1", port))
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-default-browser-check")  # 禁止 检查默认浏览器
        chrome_options.add_argument("--no-default-browser-check")  # 禁止 检查默认浏览器
        chrome_options.add_argument("--no-first-run") # 不展示 首次运行告知
        chrome_options.add_argument("--disable-features=PrivacySandboxSettings3") # 屏蔽 隐私权功能
        driver = webdriver.Chrome(options=chrome_options)

        driver.set_window_size(window_width, window_height)

        offset_x = (xid - 1) * window_width
        offset_y = (yid - 1) * window_height
        driver.set_window_position(offset_x, offset_y)


    def reorder(self):
        """
        pass
        """
        json_data = {"seqlist": []}
        requests.post(f"{self.bit_url}/windowbounds/flexable", data=json.dumps(json_data), headers=self.headers).json()

    def restart_browser(self, port,  proxy_port=None, is_reorder=False, uid=None):
        """
        重启单个浏览器窗口
        clear_user_data： 清除历史记录
        keep_pos： 保留位置
        """
        port = str(port)
        uid = None
        pid = None
        current_browser_config = self.get_config(port)
        if "id" in current_browser_config:
            uid = current_browser_config["id"]
        if "pid" in current_browser_config:
            pid = current_browser_config["pid"]
        self.stop_browser(uid, pid)
        time.sleep(20)

        # 开启了删除用户数据
        # bit 浏览器无清除用户。因为每次都是新创建浏览器来处理

        # 查询是否有代理
        res = self.open_browser(port, proxy_port)
        res['proxy_port'] = proxy_port

        self.save_config(port, res)

        print("浏览器排序状态：", is_reorder)
        if is_reorder:
            time.sleep(5)
            self.reorder()

        return res
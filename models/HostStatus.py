import traceback
from .MongoBase import BaseModel
import platform
import time
import psutil
from utils import env
from .HostThreadStatus import HostThreadStatusModel

class HostStatusModel(BaseModel):
    """
    主机监控
    """

    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称
        self.table_name = "host_status"

    def get_memory(self):
        memory = psutil.virtual_memory()
        memory_use_percent = "%s %%" % memory.percent
        memory_total = "%s" % (int(memory.total) / (1024.0 ** 3))
        memory_available = "%s GB" % (int(memory.available) / (1024.0 ** 3))
        data = {
            "memory_use_percent": memory_use_percent,
            "memory_total": memory_total,
            "memory_available": memory_available
        }
        return data

    def get_cpu(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent

    def get_sys_uname(self):
        try:
            hostname = platform.uname().node
            return hostname
        except:
            return "unknown"

    def report_status(self, data):
        """
        name + host md5为key baifang-python_main_py_server 这种格式来作为key
        created_at running_status updated_at report_ts(上报的秒级时间戳)
        hostname
        cmd
        report_ts
        """
        # 部分设备获取不到hostname 只能通过配置文件来定义
        hostname = env("HOSTNAME", self.get_sys_uname())

        thread_id = data['thread_id']
        thread_name = data['thread_name']
        project_name = data['project_name']
        server_name = data['server_name']

        main_key = f"{project_name}-{hostname}-{server_name}"
        report_ts = int(round(time.time()))
        memory_info = self.get_memory()

        # 更新主机信息
        exists = self.first(condition={
            "key": main_key
        })
        if not exists:
            self.add_one({
                "key": main_key,
                "report_ts": report_ts,
                "hostname": hostname,
                "server_name": server_name,
                "project_name": project_name,
                "cpu_percent": self.get_cpu(),
                "memory_use_percent": memory_info["memory_use_percent"],
                "memory_total": memory_info["memory_total"],
                "memory_available": memory_info["memory_available"]
            })
        else:
            self.update_one(condition={
                "key": main_key
            }, data={
                "report_ts": report_ts,
                "hostname": hostname,
                "server_name": server_name,
                "project_name": project_name,
                "cpu_percent": self.get_cpu(),
                "memory_use_percent": memory_info["memory_use_percent"],
                "memory_total": memory_info["memory_total"],
                "memory_available": memory_info["memory_available"]
            })

        # 更新子线程信息
        hostThreadStatus = HostThreadStatusModel()
        sub_key = f"{project_name}-{hostname}-{thread_id}-{server_name}"
        exists = hostThreadStatus.first(condition={
            "key": sub_key
        })
        if not exists:
            hostThreadStatus.add_one(data={
                "p_key": main_key,
                "key": sub_key,
                "report_ts": report_ts,
                "thread_id": thread_id,
                "thread_name": thread_name,
                "thread_status": data['thread_status'],
                "thread_info": data['thread_info']
            })
        else:
            hostThreadStatus.update_one(condition={
                "key": sub_key
            }, data={
                "report_ts": report_ts,
                "thread_id": thread_id,
                "thread_name": thread_name,
                "thread_status": data['thread_status'],
                "thread_info": data['thread_info']
            })




import traceback
from .MongoBase import BaseModel
import platform
import time
import psutil

class HostThreadStatusModel(BaseModel):
    """
    上报主机的子线程
    """

    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称
        self.table_name = "host_thread_status"



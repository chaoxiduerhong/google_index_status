import traceback
from .MongoBase import BaseModel
from utils import common
from config import gpt_conf
from pymongo import ReturnDocument


class SessionLogModel(BaseModel):

    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称
        self.table_name = "ast_account_log"


    def add_log(self, account, browser_port, action_type, action_info, proxy_source_indexId, proxy_source_type, proxy_source_name):
        """
        如果成功，则成功次数+1，失败次数重置0
        用于记录重要日志
        action: 触发
        """
        hostname = common.get_sys_uname()

        data = {
            "account": account,
            "hostname": hostname,
            "browser_port": browser_port,
            "action_type": action_type,
            "action_info": action_info,
            "proxy_source_indexid": proxy_source_indexId,
            "proxy_source_type": proxy_source_type,
            "proxy_source_name": proxy_source_name,
        }
        self.add_one(data=data)

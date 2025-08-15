import time
import traceback

import utils.common
from .MongoBase import BaseModel
from utils import common
from config import gpt_conf
from pymongo import ReturnDocument


class SessionQueueModel(BaseModel):

    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称
        self.table_name = gpt_conf.auth_data_table

    def get_unsync_data(self, test_std_email=None):
        """
        获取当前该浏览器登录的账号
        """
        if test_std_email:
            print("current 当前模式为测试模式，test email", test_std_email)
            res = self.lock_find_one_and_update(
                {"std_email": test_std_email},
                {"$set": {"sync_status": "running"}},
                sort=None,
                return_document=ReturnDocument.BEFORE
            )
            return res
        # 优先获取已经登录的账号
        if gpt_conf.login_status_mode == "disabled":
            condition = {
                "ready_login_ts": {"$exists": False},
                "$or": [
                    {"sync_status": "waiting"},
                    {"login_status": "disabled"}
                ]
            }
        else:
            condition = {
                "ready_login_ts": {"$exists": False},
                "$or": [
                    {"sync_status": "waiting"},
                    {"login_status": "invalid"}
                ]
            }
        save_data = {"$set": {"sync_status": "running", 'ready_login_ts': common.ts()}}

        res = self.lock_find_one_and_update(
            condition,
            save_data,
            sort=None,
            return_document=ReturnDocument.BEFORE
        )

        if not res:
            if gpt_conf.login_status_mode == "disabled":
                condition = {
                    "$or": [
                        {"sync_status": "waiting"},
                        {"login_status": "disabled"}
                    ]
                }
            else:
                condition = {
                    "$or": [
                        {"sync_status": "waiting"},
                        {"login_status": "invalid"}
                    ]
                }
            res = self.lock_find_one_and_update(
                condition,
                save_data,
                sort=[("ready_login_ts", 1)],
                return_document=ReturnDocument.BEFORE
            )

        return res
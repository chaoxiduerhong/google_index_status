import traceback
from .MongoBase import BaseModel
from utils import common
from config import gpt_conf
from pymongo import ReturnDocument


class SessionModel(BaseModel):

    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称
        self.table_name = gpt_conf.auth_data_table

    def get_account_by_batch_hostname_port(self, hostname, browser_port, batch):
        where = {
            "hostname": str(hostname),
            "browser_port": str(browser_port),
            "batch": str(batch)
        }
        if hostname and browser_port and batch:
            session = self.first(condition=where)
            if session and "account" in session:
                return session["account"]
        return None

    def update_success_num(self, account):
        """
        如果成功，则成功次数+1，失败次数重置0
        """
        current = self.first(condition={
            'account': account
        })
        if current:
            try:
                success_num = current['success_num'] + 1
            except:
                success_num = 1

            self.update_one(condition={
                'account': account
            }, data={
                "failed_num": 0,
                "success_num": success_num,
            })


    def open_ask_lock(self, account):
        """
        解锁
        """
        current = self.first(condition={
            'account': account
        })
        if current:
            self.update_one(condition={
                'account': account
            }, data={
                "ask_lock": False
            })


    def update_failed_num(self, account):
        """
        如果成功，则成功次数+1，失败次数重置0
        """
        current = self.first(condition={
            'account': account
        })
        if current:
            try:
                failed_num = current['failed_num'] + 1
            except:
                failed_num = 1

            self.update_one(condition={
                'account': account
            }, data={
                "failed_num": failed_num,
            })
        else:
            print("update_failed_num failed, failed,", account, self.table_name)


    def update_disabled_login_status(self, account_data, status):
        """
        重新登录disabled 的账号
        如果登录成功：disabled_login_success_num + 1
        如果登录失败：disabled_login_failed_num + 1
        """
        account = account_data['account']
        current = self.first(condition={
            'account': account
        })

        if current:
            if "login_status" in current and current['login_status'] == "disabled":
                try:
                    if status == "success":
                        if "disabled_login_success_num" not in current:
                            success_num = 1
                        else:
                            success_num = current['disabled_login_success_num'] + 1
                        self.update_one(condition={
                            'account': account
                        }, data={
                            "disabled_login_success_num": success_num,
                        })
                    elif status == "failed":
                        if "disabled_login_failed_num" not in current:
                            failed_num = 1
                        else:
                            failed_num = current['disabled_login_failed_num'] + 1
                        self.update_one(condition={
                            'account': account
                        }, data={
                            "disabled_login_failed_num": failed_num,
                        })
                except:
                    pass


    def update_login_status_invalid(self, account):
        """
        如果成功，则成功次数+1，失败次数重置0
        """
        current = self.first(condition={
            'account': account
        })
        if current:
            self.update_one(condition={
                'account': account
            }, data={
                "login_status": "invalid",
                "sync_status":"waiting"
            })
        else:
            print("update_login_status_invalid failed, failed,", account, self.table_name)


    def update_login_status_disabled(self, std_email):
        """
        如果成功，则成功次数+1，失败次数重置0
        """
        current = self.first(condition={
            'std_email': std_email
        })
        if current:
            self.update_one(condition={
                'std_email': std_email
            }, data={
                "login_status": "disabled",
                "sync_status": "running"
            })
        else:
            print("update_login_status_disabled failed, failed,", std_email, self.table_name)


    def update_last_cookie(self, account, session_token):
        """
        如果成功，则成功次数+1，失败次数重置0
        """
        current = self.first(condition={
            'account': account
        })
        if current:
            self.update_one(condition={
                'account': account
            }, data={
                "cookie_data_last": session_token,
            })
            print("update_last_cookie success", account, self.table_name)
        else:
            print("update_last_cookie failed, failed,", account, self.table_name)

    def get_info_by_account(self, account):
        """
        获取账号信息
        """
        current = self.first(condition={
            'account': account
        })
        if current:
            return current
        else:
            print("get_info_by_account failed, failed,", account, self.table_name)
            return None

    def lock_ask_failed_update_day_count(self, account):
        try:
            condition = {
                "account": account
            }
            res = self.lock_find_one_and_update(
                condition,
                {
                    "$inc": {"day_count": -1},
                    "max": {"day_count": 0}
                },
                sort=None,
                return_document=ReturnDocument.BEFORE
            )
            return res
        except Exception as e:
            return None

    def lock_get_session_issue_account(self, account):
        account = str(account)
        condition = {
            "account": account
        }
        res = self.first(condition=condition)
        if not res:
            return None
        session_info = res['cookie_data_first']
        return {
            "session": session_info,
            "session_key": res['account']
        }

    def save_session_issue(self, condition, hostname, browser_port, proxy_port, is_init_day_count=False):
        if is_init_day_count:
            res = self.lock_find_one_and_update(
                condition,
                {
                    "$set": {
                        "hostname": hostname,
                        "browser_port": browser_port,
                        "proxy_port": proxy_port,
                        "batch": "1",
                        "updated_at": common.get_now_str(),
                        "ask_last_time": common.get_now_str(),
                        "ask_lock": True,
                        "day_count": 1
                    }
                },
                sort=[("ask_last_time", 1)],
                return_document=ReturnDocument.AFTER)
        else:
            res = self.lock_find_one_and_update(
                condition,
                {
                    "$inc": {"day_count": 1},
                    "$set": {
                        "hostname": hostname,
                        "browser_port": browser_port,
                        "proxy_port": proxy_port,
                        "batch": "1",
                        "updated_at": common.get_now_str(),
                        "ask_last_time": common.get_now_str(),
                        "ask_lock": True,
                    }
                },
                sort=[("ask_last_time", 1)],
                return_document=ReturnDocument.AFTER)
        return res


    def lock_get_session_issue(self, browser_port, hostname, proxy_port):
        """
        数据库文档锁，获取记录
        """
        try:

            batch = "1"
            browser_port = str(browser_port)
            hostname = str(hostname)

            # 按未进行任何分配
            # 这是时候无需判断 day_count 和 lock的限制
            condition = {
                "ask_last_time": {"$exists": False},
                "sync_status": "success",
                "login_status": "success"
            }
            data_type = None
            res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
            if res:
                data_type = "askLastTimeNotExists"

            # 按 最远更新时间来获取 ask_last_time 并且该时间大于 24h。
            # 这是时候无需判断 day_count 和 lock的限制
            # 出现大于24h的需要将count重置为 1
            if not res:
                current_ts = common.get_second_utime() - 86400
                current_time_str = common.formatTime(current_ts)
                condition = {
                    "ask_last_time": {'$lte': current_time_str},
                    "sync_status": "success",
                    "login_status": "success"
                }
                print("conditon2", condition)
                res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=True)
                if res:
                    data_type = "askLastTimeLTE24hForCustom"

            # 匹配同代理
            # 获取 活跃周期 700 之外 + 非锁定的账号 + 优先同代理路线的账号
            if not res:
                current_ts = common.get_second_utime() - 700
                current_time_str = common.formatTime(current_ts)
                condition = {
                    "ask_last_time": {'$lte': current_time_str},
                    "sync_status": "success",
                    "login_status": "success",
                    # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                    "ask_lock": False,
                    "proxy_port": proxy_port,
                }
                print("condition-1200", condition)

                res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
                if res:
                    data_type = "askLastTimeLTE300sForCustomSamePort"


            # 获取 活跃周期 1800 之外+ 不计是否锁定的账号 + 优先同代理路线的账号
            if not res:
                current_ts = common.get_second_utime() - 1500
                current_time_str = common.formatTime(current_ts)
                condition = {
                    "ask_last_time": {'$lte': current_time_str},
                    "sync_status": "success",
                    "login_status": "success",
                    # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                    "proxy_port": proxy_port,
                }

                print("condition-1800", condition)
                res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)



                # 不匹配同代理
                # 获取 活跃周期 700 之外 + 非锁定的账号
                if not res:
                    current_ts = common.get_second_utime() - 700
                    current_time_str = common.formatTime(current_ts)
                    condition = {
                        "ask_last_time": {'$lte': current_time_str},
                        "sync_status": "success",
                        "login_status": "success",
                        # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                        "ask_lock": False
                    }
                    print("condition-1200", condition)

                    res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
                    if res:
                        data_type = "askLastTimeLTE300sForCustom"

                # 获取 活跃周期 1800 之外+ 不计是否锁定的账号
                if not res:
                    current_ts = common.get_second_utime() - 1500
                    current_time_str = common.formatTime(current_ts)
                    condition = {
                        "ask_last_time": {'$lte': current_time_str},
                        "sync_status": "success",
                        "login_status": "success",
                        # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                    }

                    print("condition-1800", condition)
                    res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
                if res:
                    data_type = "askLastTime1800sForCustom"
            if not res:
                print("Not enough session assign")
                return None

            session_info = res['cookie_data_last'] if "cookie_data_last" in res else res['cookie_data_first']
            is_prod_account = False
            if "success_num" in session_info and session_info["success_num"] > 2:
                is_prod_account = True

            return {
                "session": session_info,
                "hostname": hostname,
                "browser_port": browser_port,
                "batch": batch,
                "session_key": res['account'],
                "data_type": data_type,
                "account_proxy_port": res['proxy_port'] if "proxy_port" in res else None,
                "ask_last_time": res['ask_last_time'] if "ask_last_time" in res else None,
                "account": res['account'],
                "day_count": res['day_count'],
                "email": res['email'] if "email" in res else None,
                # 是否生产过的账号，如果success成功过，> 2 则设置为true，否则为false
                "is_prod_account": is_prod_account,
            }
        except:
            print("-------- !!!!!!!! get session error !!!!!!!! ----", traceback.format_exc())
            return None

    def session_issue_total(self, browser_port, hostname, proxy_port):
        """
        账号下发统计
        """
        try:

            batch = "1"
            browser_port = str(browser_port)
            hostname = str(hostname)

            # 按未进行任何分配
            # 这是时候无需判断 day_count 和 lock的限制
            condition = {
                "ask_last_time": {"$exists": False},
                "sync_status": "success",
                "login_status": "success"
            }
            data_type = None
            res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
            if res:
                data_type = "askLastTimeNotExists"

            # 按 最远更新时间来获取 ask_last_time 并且该时间大于 24h。
            # 这是时候无需判断 day_count 和 lock的限制
            # 出现大于24h的需要将count重置为 1
            if not res:
                current_ts = common.get_second_utime() - 86400
                current_time_str = common.formatTime(current_ts)
                condition = {
                    "ask_last_time": {'$lte': current_time_str},
                    "sync_status": "success",
                    "login_status": "success"
                }
                print("conditon2", condition)
                res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=True)
                if res:
                    data_type = "askLastTimeLTE24hForCustom"

            # 匹配同代理
            # 获取 活跃周期 700 之外 + 非锁定的账号 + 优先同代理路线的账号
            if not res:
                current_ts = common.get_second_utime() - 700
                current_time_str = common.formatTime(current_ts)
                condition = {
                    "ask_last_time": {'$lte': current_time_str},
                    "sync_status": "success",
                    "login_status": "success",
                    # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                    "ask_lock": False,
                    "proxy_port": proxy_port,
                }
                print("condition-1200", condition)

                res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
                if res:
                    data_type = "askLastTimeLTE300sForCustomSamePort"


            # 获取 活跃周期 1800 之外+ 不计是否锁定的账号 + 优先同代理路线的账号
            if not res:
                current_ts = common.get_second_utime() - 1500
                current_time_str = common.formatTime(current_ts)
                condition = {
                    "ask_last_time": {'$lte': current_time_str},
                    "sync_status": "success",
                    "login_status": "success",
                    # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                    "proxy_port": proxy_port,
                }

                print("condition-1800", condition)
                res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)



                # 不匹配同代理
                # 获取 活跃周期 700 之外 + 非锁定的账号
                if not res:
                    current_ts = common.get_second_utime() - 700
                    current_time_str = common.formatTime(current_ts)
                    condition = {
                        "ask_last_time": {'$lte': current_time_str},
                        "sync_status": "success",
                        "login_status": "success",
                        # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                        "ask_lock": False
                    }
                    print("condition-1200", condition)

                    res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
                    if res:
                        data_type = "askLastTimeLTE300sForCustom"

                # 获取 活跃周期 1800 之外+ 不计是否锁定的账号
                if not res:
                    current_ts = common.get_second_utime() - 1500
                    current_time_str = common.formatTime(current_ts)
                    condition = {
                        "ask_last_time": {'$lte': current_time_str},
                        "sync_status": "success",
                        "login_status": "success",
                        # "day_count": {'$lt': gpt_conf.account_day_max_req_num_for_custom},
                    }

                    print("condition-1800", condition)
                    res = self.save_session_issue(condition, hostname, browser_port, proxy_port, is_init_day_count=False)
                if res:
                    data_type = "askLastTime1800sForCustom"
            if not res:
                print("Not enough session assign")
                return None

            session_info = res['cookie_data_last'] if "cookie_data_last" in res else res['cookie_data_first']
            is_prod_account = False
            if "success_num" in session_info and session_info["success_num"] > 2:
                is_prod_account = True

            return {
                "session": session_info,
                "hostname": hostname,
                "browser_port": browser_port,
                "batch": batch,
                "session_key": res['account'],
                "data_type": data_type,
                "account_proxy_port": res['proxy_port'] if "proxy_port" in res else None,
                "ask_last_time": res['ask_last_time'] if "ask_last_time" in res else None,
                "account": res['account'],
                "day_count": res['day_count'],
                "email": res['email'] if "email" in res else None,
                # 是否生产过的账号，如果success成功过，> 2 则设置为true，否则为false
                "is_prod_account": is_prod_account,
            }
        except:
            print("-------- !!!!!!!! get session error !!!!!!!! ----", traceback.format_exc())
            return None


    def update_notices_status(self, account, status=False):
        self.update_one(
            condition={
                "account": account,
            },
            data={"is_notice": status}
        )

    def update_exp_to(self, browser_port, exp_to=None):
        """
        设置程序过期时间 + 1h
        """
        hostname = common.get_sys_uname()
        if not exp_to:
            exp_to = common.get_second_utime() + 3600
        self.update_one(condition={
            "hostname": hostname,
            "browser_port": browser_port
        }, data={
            "exp_to": exp_to}
        )

    def delay_ask_ts(self, account):
        """
        设置程序过期时间 + 1h
        """
        current_ts = common.get_second_utime() + 1200
        current_time_str = common.formatTime(current_ts)
        print("delay_ask_ts: account:",account, ",current_time_str:", current_time_str)
        self.update_one(condition={
            "account": account
        }, data={
            "ask_last_time": current_time_str}
        )

    def check_is_active(self, browser_port):
        """
        检测程序是否到了过期时间
        """
        hostname = common.get_sys_uname()
        exp_end = common.get_second_utime()
        condition = {
            "hostname": hostname,
            "browser_port": browser_port,
            "$or": [
                {"exp_to": {"$lte": exp_end}},
                {"exp_to": {"$exists": False}}
            ]
        }
        ret = self.get(condition=condition)
        return ret

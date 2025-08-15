from .MongoBase import BaseModel
from config import gpt_conf

class PerplexityBrowserAuthModel(BaseModel):
    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称，子类必须重写该表名称
        self.table_name = gpt_conf.copilot_browser_auth_table
        print("*** check current products tables :%s", self.table_name)


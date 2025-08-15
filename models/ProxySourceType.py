from .MongoBase import BaseModel
from utils import env
from config import gpt_conf


class ProxySourceTypeModel(BaseModel):

    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "default"
        # 表名称
        self.table_name = "proxy_source_type_status"

        print("*** Synonyms tables :%s", self.table_name)

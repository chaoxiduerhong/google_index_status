from .MongoBase import BaseModel
from utils import env
from config import gpt_conf

class ProductsResultFailed(BaseModel):
    def __init__(self):
        super().__init__()
        # 要连接的数据库
        self.connection = "products"
        # 表名称，子类必须重写该表名称
        self.table_name = gpt_conf.product_table_result_failed
        print("*** check current product_result_failed tables :%s", self.table_name)

    def getFirstProduct(self):
        """
        获取第一个产品
        """
        result = self.get(
            start=0,
            length=1,
            order_by={"bid": 1}
        )
        return None if not result else result[0]

    def getFirstProductByAsync(self):
        """
        获取第一个产品
        """
        self.table_name = gpt_conf.product_table_result_failed
        result = self.get(
            start=0,
            length=1,
            order_by={"bid": 1}
        )
        return None if not result else result[0]

    def getLastProduct(self):
        """
        获取最后一个产品
        """
        result = self.get(
            start=0,
            length=1,
            order_by={"bid": -1}
        )
        return None if not result else result[0]

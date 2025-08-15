"""
产品队列
"""
from models import MProductsResultFailed
from models import MProducts
from config import gpt_conf
from utils import log, get_setting, set_setting


class ProductQueue:
    def __init__(self, lock, browser_port):
        self.lock = lock
        self.start_bid_key = "start_bid"
        self.start_bid_file = gpt_conf.start_bid_file
        self.browser_port = browser_port

    def get_start_bid_file(self):
        return self.start_bid_file

    def set_start_bid(self, value=0):
        key = self.start_bid_key
        set_setting(filename=self.get_start_bid_file(), key=key, value=str(value))

    def get_start_bid(self, value=0):
        key = self.start_bid_key
        client_min_bid = gpt_conf.client_min_bid
        ret = get_setting(filename=self.get_start_bid_file(), key=key, value=client_min_bid)
        if ret:
            return float(ret)
        return 0

    def set_port_bid(self, value=0):
        # 需要支持线程锁
        key = "bid_start_%s" % self.browser_port
        set_setting(filename=self.get_start_bid_file(), key=key, value=str(value))

    def get_port_bid(self, value=0):
        key = "bid_start_%s" % self.browser_port
        ret = get_setting(filename=self.get_start_bid_file(), key=key, value=value)
        if ret:
            return float(ret)
        return 0

    def get_product(self):
        with self.lock:
            # 先确认失败的列表中是否存在，存在则用该产品数据，取出产品后，删除该产品。
            product = MProductsResultFailed.getFirstProduct()
            if product:
                print("get_product for product_result_failed ")
                MProductsResultFailed.delete(condition={"bid": {"$eq": product['bid']}})
                return product
            start_bid = self.get_start_bid()
            product = MProducts.getFirstProduct(start_bid, gpt_conf.client_max_bid)
            if product:
                print(f" get product for product_queue, start bid {start_bid} / {gpt_conf.client_max_bid}...")
                self.set_start_bid(product['bid'])
                self.set_port_bid(product['bid'])
            else:
                print(f"not find product queue by this bid {start_bid}")
            return product

    @staticmethod
    def by_bid_get_product(bid):
        return MProducts.first(condition={
            "bid": {"$eq": bid}
        })

    # def check_exists(self):
    #     """
    #     检测结果表中该数据是否存在
    #     """
    #     if MProductsResult.total(
    #             condition={"bid": {"$eq": product['bid']}}) > 0:
    #         self.log("check product exists in gpt, continue")
    #         continue
    #     else:
    #         self.log("check product not exists in gpt, continue,bid: %s" % product['bid'])
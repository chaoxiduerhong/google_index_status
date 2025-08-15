from .Products import ProductsModel
from .ProductsResultModel import ProductsResultModel
from .ProductsResultFullModel import ProductsResultFullModel
from .ProductResultFailedModel import ProductsResultFailed
from .ProxyQueue import ProxyQueueModel
from .ProxySourceType import ProxySourceTypeModel
from .SessionQueue import SessionModel
from .SessionQueueLog import SessionLogModel
from .SessionQueueQueue import SessionQueueModel
from .EmailAddrModel import EmailAddrModel
from .PerplexityAuthModel import PerplexityAuthModel
from .PerplexityBrowserAuthModel import PerplexityBrowserAuthModel
from .ProductsResultLinkModel import ProductsResultLinkModel

# 实例化类
MProducts = ProductsModel()
MProductsResult = ProductsResultModel()
MProductsResultLink = ProductsResultLinkModel()
MProductsResultFailed = ProductsResultFailed()
MProxyQueue = ProxyQueueModel()
MProxySourceType = ProxySourceTypeModel()
MSession = SessionModel()
MSessionLog = SessionLogModel()
MSessionQueue = SessionQueueModel()
MEmailAddr = EmailAddrModel()
MPerplexityAuth = PerplexityAuthModel()
MPerplexityBrowserAuth = PerplexityBrowserAuthModel()

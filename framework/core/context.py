"""页面上下文模块。

Page context module.

Author: taobo.zhou
"""


class PageContext:
    """页面上下文数据对象。

    Page context data object.

    Author: taobo.zhou
    """
    def __init__(self, driver, locator_loader, logger, page_name=None):
        self.driver = driver
        self.locators = locator_loader
        self.logger = logger
        self.page_name = page_name

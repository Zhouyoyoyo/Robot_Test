class PageContext:
    """Author: taobo.zhou
    中文：页面上下文数据对象，保存页面级依赖。
    English: Page context data object storing page-level dependencies.
    """

    def __init__(self, driver, locator_loader, logger, page_name=None):
        """Author: taobo.zhou
        中文：初始化页面上下文数据。
        参数:
            driver: WebDriver 实例。
            locator_loader: 定位器加载器实例。
            logger: 日志记录器。
            page_name: 页面名称，可为空。
        """

        self.driver = driver
        self.locators = locator_loader
        self.logger = logger
        self.page_name = page_name

class PageContext:
    def __init__(self, driver, locator_loader, logger, page_name=None):
        self.driver = driver
        self.locators = locator_loader
        self.logger = logger
        self.page_name = page_name

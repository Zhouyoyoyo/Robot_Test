from selenium.webdriver import ActionChains


class MouseMixin:
    """Author: taobo.zhou
    鼠标交互混入类，提供鼠标点击操作。
    Mouse interaction mixin providing mouse click operations.
    """

    def click(self, name):
        """Author: taobo.zhou
        执行鼠标单击。
        
            name: 定位器名称。
        """

        el = self._find(name)
        self._log.info(f"[MOUSE_CLICK] {self._page_name}.{name}")
        ActionChains(self.__driver).click(el).perform()

    def double_click(self, name):
        """Author: taobo.zhou
        执行鼠标双击。
        
            name: 定位器名称。
        """

        el = self._find(name)
        self._log.info(f"[MOUSE_DOUBLE_CLICK] {self._page_name}.{name}")
        ActionChains(self.__driver).double_click(el).perform()

    def mouse_click(self, name, double: bool = False):
        """Author: taobo.zhou
        滚动到元素后执行单击或双击。
        
            name: 定位器名称。
            double: 是否执行双击。
        """

        self.scroll_and_wait(name)
        self.sleep(0.5)
        if double:
            self.double_click(name)
        else:
            self.click(name)

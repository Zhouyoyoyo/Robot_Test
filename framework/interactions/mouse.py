from selenium.webdriver import ActionChains


class MouseMixin:
    def click(self, name):
        el = self._find(name)
        self._log.info(f"[MOUSE_CLICK] {self._page_name}.{name}")
        ActionChains(self.__driver).click(el).perform()

    def double_click(self, name):
        el = self._find(name)
        self._log.info(f"[MOUSE_DOUBLE_CLICK] {self._page_name}.{name}")
        ActionChains(self.__driver).double_click(el).perform()

    def mouse_click(self, name, double: bool = False):
        self.scroll_and_wait(name)
        self.sleep(0.5)
        if double:
            self.double_click(name)
        else:
            self.click(name)

"""DOM 交互模块。

DOM interaction module.

作者: taobo.zhou
Author: taobo.zhou
"""

from selenium.webdriver.support.select import Select


class DomMixin:
    """DOM 交互混入类。

    DOM interaction mixin.

    作者: taobo.zhou
    Author: taobo.zhou
    """
    def _get_locator(self, name):
        return self._locators.get(name)

    def _find(self, name):
        by, value = self._get_locator(name)
        return self.__driver.find_element(by, value)

    def open(self, url: str):
        self._log.info(f"[OPEN] {self._page_name} -> {url}")
        self.__driver.get(url)

    def click(self, name):
        self._log.debug(f"[CLICK] {self._page_name}.{name}")
        self._find(name).click()

    def input(self, name, text):
        el = self._find(name)
        el.clear()
        el.send_keys(text)

    def select(self, name, option, by: str = "text"):
        self._log.info(f"[SELECT] {self._page_name}.{name} by={by} option={option}")
        element = self._find(name)
        select = Select(element)

        by = (by or "").lower()
        if by == "text":
            select.select_by_visible_text(str(option))
        elif by == "value":
            select.select_by_value(str(option))
        elif by == "index":
            select.select_by_index(int(option))
        else:
            raise ValueError("select(by=) only supports: text | value | index")

    def upload(self, name: str, file_path: str):
        if not isinstance(file_path, str) or not file_path:
            raise ValueError("upload file_path is empty")
        el = self._find(name)
        el.send_keys(file_path)

    def scroll_and_wait(self, name):
        element = self._find(name)
        self.__driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element,
        )

    def set_attr(self, name, attr, value):
        el = self._find(name)
        self.__driver.execute_script(
            "arguments[0].setAttribute(arguments[1], arguments[2])",
            el,
            attr,
            value,
        )

    def get_element_attr(self, name, attr_name):
        el = self._find(name)
        attr_value = el.get_attribute(attr_name)
        self._log.info(f"获取元素 {name} 的 {attr_name}属性值：{attr_value}")
        return attr_value

from selenium.webdriver.support.select import Select


class DomMixin:
    """Author: taobo.zhou
    中文：DOM 交互混入类，提供基础元素操作。
    English: DOM interaction mixin providing basic element operations.
    """

    def _get_locator(self, name):
        """Author: taobo.zhou
        中文：获取定位器配置。
        参数:
            name: 定位器名称。
        """

        return self._locators.get(name)

    def _find(self, name):
        """Author: taobo.zhou
        中文：查找并返回页面元素。
        参数:
            name: 定位器名称。
        """

        by, value = self._get_locator(name)
        return self.__driver.find_element(by, value)

    def open(self, url: str):
        """Author: taobo.zhou
        中文：打开指定 URL。
        参数:
            url: 目标页面地址。
        """

        self._log.info(f"[OPEN] {self._page_name} -> {url}")
        self.__driver.get(url)

    def click(self, name):
        """Author: taobo.zhou
        中文：点击指定元素。
        参数:
            name: 定位器名称。
        """

        self._log.debug(f"[CLICK] {self._page_name}.{name}")
        self._find(name).click()

    def input(self, name, text):
        """Author: taobo.zhou
        中文：清空后输入文本。
        参数:
            name: 定位器名称。
            text: 需要输入的文本。
        """

        el = self._find(name)
        el.clear()
        el.send_keys(text)

    def select(self, name, option, by: str = "text"):
        """Author: taobo.zhou
        中文：在下拉框中选择选项。
        参数:
            name: 定位器名称。
            option: 选项值。
            by: 选择方式，支持 text、value、index。
        """

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
        """Author: taobo.zhou
        中文：上传文件到指定输入框。
        参数:
            name: 定位器名称。
            file_path: 本地文件路径。
        """

        if not isinstance(file_path, str) or not file_path:
            raise ValueError("upload file_path is empty")
        el = self._find(name)
        el.send_keys(file_path)

    def scroll_and_wait(self, name):
        """Author: taobo.zhou
        中文：滚动到指定元素位置。
        参数:
            name: 定位器名称。
        """

        element = self._find(name)
        self.__driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element,
        )

    def set_attr(self, name, attr, value):
        """Author: taobo.zhou
        中文：设置元素属性值。
        参数:
            name: 定位器名称。
            attr: 属性名。
            value: 属性值。
        """

        el = self._find(name)
        self.__driver.execute_script(
            "arguments[0].setAttribute(arguments[1], arguments[2])",
            el,
            attr,
            value,
        )

    def get_element_attr(self, name, attr_name):
        """Author: taobo.zhou
        中文：获取元素属性值。
        参数:
            name: 定位器名称。
            attr_name: 属性名。
        """

        el = self._find(name)
        attr_value = el.get_attribute(attr_name)
        self._log.info(f"获取元素 {name} 的 {attr_name}属性值：{attr_value}")
        return attr_value

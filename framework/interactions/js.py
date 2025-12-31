class JsMixin:
    """Author: taobo.zhou
    JavaScript 交互混入类，提供脚本执行能力。
    JavaScript interaction mixin providing script execution.
    """

    def js_click(self, name):
        """Author: taobo.zhou
        通过 JavaScript 触发元素点击。
        
            name: 定位器名称。
        """

        self._log.info(f"[JS_CLICK] {self._page_name}.{name}")
        el = self._find(name)
        self.__driver.execute_script("arguments[0].click();", el)

    def execute_js(self, script, *args):
        """Author: taobo.zhou
        执行自定义 JavaScript 并返回结果。
        
            script: JavaScript 脚本字符串。
            *args: 传递给脚本的参数。
        """

        self._log.debug(f"[EXECUTE_JS] {self._page_name} script={script}")
        return self.__driver.execute_script(script, *args)

    def set_dom_property(self, locator_name, prop, value):
        """Author: taobo.zhou
        设置元素的 DOM 属性值。
        
            locator_name: 定位器名称。
            prop: DOM 属性名。
            value: DOM 属性值。
        """

        self._log.info(
            "[SET_DOM_PROPERTY] page=%s locator=%s prop=%s value=%s",
            self._page_name,
            locator_name,
            prop,
            value,
        )
        element = self._find(locator_name)
        self.__driver.execute_script(
            "arguments[0][arguments[1]] = arguments[2];",
            element,
            prop,
            value,
        )

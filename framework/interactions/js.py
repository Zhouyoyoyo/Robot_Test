"""JavaScript 交互模块。

JavaScript interaction module.

作者: taobo.zhou
Author: taobo.zhou
"""


class JsMixin:
    """JavaScript 交互混入类。

    JavaScript interaction mixin.

    作者: taobo.zhou
    Author: taobo.zhou
    """
    def js_click(self, name):
        self._log.info(f"[JS_CLICK] {self._page_name}.{name}")
        el = self._find(name)
        self.__driver.execute_script("arguments[0].click();", el)

    def execute_js(self, script, *args):
        self._log.debug(f"[EXECUTE_JS] {self._page_name} script={script}")
        return self.__driver.execute_script(script, *args)

    def set_dom_property(self, locator_name, prop, value):
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

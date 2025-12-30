"""Shadow DOM 交互模块。

Shadow DOM interaction module.

作者: taobo.zhou
Author: taobo.zhou
"""

from selenium.webdriver.common.by import By


class ShadowDomMixin:
    """Shadow DOM 交互混入类。

    Shadow DOM interaction mixin.

    作者: taobo.zhou
    Author: taobo.zhou
    """
    def _get_shadow_host_locator(self, name):
        if hasattr(self._locators, "get_shadow_host"):
            return self._locators.get_shadow_host(name)
        return self._get_locator(name)

    def get_shadow_element(self, locator_name):
        by, value = self._get_shadow_host_locator(locator_name)
        shadow_host = self.__driver.find_element(by, value)
        shadow_root = self.__driver.execute_script(
            "return arguments[0].shadowRoot", shadow_host
        )
        by, value = self._get_locator(locator_name)
        return shadow_root.find_element(by, value)

    def input_text_in_shadow_dom(
        self,
        locator_name: str,
        text: str,
        input_or_textarea: str = "input",
    ):
        self._log.info(
            f"Starting the process to upload file in Shadow DOM for locator: {locator_name}"
        )
        by, value = self._get_shadow_host_locator(locator_name)
        shadow_host = self.__driver.find_element(by, value)
        shadow_root = self.__driver.execute_script(
            "return arguments[0].shadowRoot", shadow_host
        )

        input_element = None
        match input_or_textarea:
            case "input":
                input_element = shadow_root.find_element(
                    By.CSS_SELECTOR, "input[type='text']"
                )
            case "textarea":
                input_element = shadow_root.find_element(
                    By.CSS_SELECTOR, "textarea[aria-invalid='false']"
                )
        if input_element is None:
            raise ValueError("Unsupported input_or_textarea type")
        input_element.send_keys(text)

    def click_shadow_dom(self, locator_name: str):
        self._log.info(
            f"Starting the process to upload file in Shadow DOM for locator: {locator_name}"
        )
        shadow_element = self.get_shadow_element(locator_name)
        shadow_element.click()

    def upload_in_shadow_dom(self, name: str, file_path: str):
        self._log.info(
            f"Starting the process to upload file in Shadow DOM for locator: {name}"
        )
        by, value = self._get_shadow_host_locator(name)
        shadow_host = self.__driver.find_element(by, value)
        shadow_root = self.__driver.execute_script(
            "return arguments[0].shadowRoot", shadow_host
        )
        input_element = shadow_root.find_element(By.CSS_SELECTOR, "#input")
        input_element.send_keys(file_path)

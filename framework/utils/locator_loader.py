import os

import yaml
from selenium.webdriver.common.by import By


class LocatorLoader:
    """Author: taobo.zhou
    定位器加载器，负责读取并校验定位器配置。
    Locator loader that reads and validates locator configurations.
    """

    def __init__(self, yaml_path):
        """Author: taobo.zhou
        初始化定位器加载器。
        
            yaml_path: 定位器 YAML 文件路径。
        """

        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Locator file not found: {yaml_path}")
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

    def validate_all(self):
        """Author: taobo.zhou
        校验定位器配置结构。
         无。
        """

        if not isinstance(self.data, dict):
            raise ValueError("Locator root must be a dict")

        for page, locators in self.data.items():
            if not isinstance(locators, dict):
                raise ValueError(f"Page {page} must be a dict")
            for name, locator in locators.items():
                if "by" not in locator or "value" not in locator:
                    raise ValueError(f"{page}.{name} missing by/value")

    def get(self, page, name):
        """Author: taobo.zhou
        获取指定页面的定位器配置。
        
            page: 页面名称。
            name: 定位器名称。
        """

        try:
            return self.data[page][name]
        except KeyError:
            raise KeyError(f"Locator not found: {page}.{name}")


class PageLocators:
    """Author: taobo.zhou
    页面定位器代理，转换为 Selenium 定位器。
    Page locator proxy that converts to Selenium locators.
    """

    def __init__(self, loader: LocatorLoader, page_name: str):
        """Author: taobo.zhou
        初始化页面定位器代理。
        
            loader: LocatorLoader 实例。
            page_name: 页面名称。
        """

        self._loader = loader
        self._page_name = page_name

    def get(self, name):
        """Author: taobo.zhou
        获取页面定位器并转换为 Selenium 定位器。
        
            name: 定位器名称。
        """

        locator = self._loader.get(self._page_name, name)
        return _convert_locator(locator["by"], locator["value"])

    def get_shadow_host(self, name):
        """Author: taobo.zhou
        获取 Shadow Host 的定位器。
        
            name: 定位器名称。
        """

        locator = self._loader.get(self._page_name, name)
        if "shadow_host" not in locator:
            raise KeyError(f"Locator not found: {self._page_name}.{name}.shadow_host")
        return _convert_locator(locator["by"], locator["shadow_host"])


def _convert_locator(locator_type: str, locator_value: str):
    """Author: taobo.zhou
    将定位器类型转换为 Selenium By。
    
        locator_type: 定位器类型字符串。
        locator_value: 定位器值。
    """

    locator_type = (locator_type or "").lower()
    if locator_type == "id":
        return By.ID, locator_value
    if locator_type == "xpath":
        return By.XPATH, locator_value
    if locator_type == "name":
        return By.NAME, locator_value
    if locator_type == "css":
        return By.CSS_SELECTOR, locator_value
    if locator_type == "class":
        return By.CLASS_NAME, locator_value
    raise ValueError(f"Unsupported locator type: {locator_type}")


def build_page_locators(locator_loader, page_name: str):
    """Author: taobo.zhou
    构建页面定位器代理或返回原加载器。
    
        locator_loader: 定位器加载器或代理。
        page_name: 页面名称。
    """

    if isinstance(locator_loader, PageLocators):
        return locator_loader
    if page_name is None:
        return locator_loader
    return PageLocators(locator_loader, page_name)

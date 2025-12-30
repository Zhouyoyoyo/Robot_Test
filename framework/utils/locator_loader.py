"""定位器加载模块。

Locator loader module.

Author: taobo.zhou
"""

import os

import yaml
from selenium.webdriver.common.by import By


class LocatorLoader:
    """定位器加载器。

    Locator loader.

    Author: taobo.zhou
    """
    def __init__(self, yaml_path):
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Locator file not found: {yaml_path}")
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

    def validate_all(self):
        if not isinstance(self.data, dict):
            raise ValueError("Locator root must be a dict")

        for page, locators in self.data.items():
            if not isinstance(locators, dict):
                raise ValueError(f"Page {page} must be a dict")
            for name, locator in locators.items():
                if "by" not in locator or "value" not in locator:
                    raise ValueError(f"{page}.{name} missing by/value")

    def get(self, page, name):
        try:
            return self.data[page][name]
        except KeyError:
            raise KeyError(f"Locator not found: {page}.{name}")


class PageLocators:
    """页面定位器代理。

    Page locator proxy.

    Author: taobo.zhou
    """
    def __init__(self, loader: LocatorLoader, page_name: str):
        self._loader = loader
        self._page_name = page_name

    def get(self, name):
        locator = self._loader.get(self._page_name, name)
        return _convert_locator(locator["by"], locator["value"])

    def get_shadow_host(self, name):
        locator = self._loader.get(self._page_name, name)
        if "shadow_host" not in locator:
            raise KeyError(f"Locator not found: {self._page_name}.{name}.shadow_host")
        return _convert_locator(locator["by"], locator["shadow_host"])


def _convert_locator(locator_type: str, locator_value: str):
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
    if isinstance(locator_loader, PageLocators):
        return locator_loader
    if page_name is None:
        return locator_loader
    return PageLocators(locator_loader, page_name)

import yaml
import os


class LocatorLoader:
    def __init__(self, yaml_path):
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Locator file not found: {yaml_path}")
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

    def validate_all(self):
        """只校验结构，不触碰 selenium"""
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

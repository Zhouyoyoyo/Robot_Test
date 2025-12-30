"""核心驱动管理模块。

Core driver manager module.

Author: taobo.zhou
"""

from framework.driver.driver_factory import create_driver


class DriverManager:
    """驱动管理器。

    Driver manager.

    Author: taobo.zhou
    """
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = create_driver()
        return cls._driver

    @classmethod
    def quit(cls):
        if cls._driver:
            cls._driver.quit()
            cls._driver = None

    @classmethod
    def quit_driver(cls):
        # alias for compatibility
        cls.quit()

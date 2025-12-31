from framework.driver.driver_factory import create_driver


class DriverManager:
    """Author: taobo.zhou
    中文：驱动管理器，统一创建与释放浏览器驱动。
    English: Driver manager that creates and disposes browser drivers.
    """

    _driver = None

    @classmethod
    def get_driver(cls):
        """Author: taobo.zhou
        中文：获取单例 WebDriver 实例，不存在则创建。
        参数:
            cls: 类对象。
        """

        if cls._driver is None:
            cls._driver = create_driver()
        return cls._driver

    @classmethod
    def quit(cls):
        """Author: taobo.zhou
        中文：关闭并清理 WebDriver 实例。
        参数:
            cls: 类对象。
        """

        if cls._driver:
            cls._driver.quit()
            cls._driver = None

    @classmethod
    def quit_driver(cls):
        """Author: taobo.zhou
        中文：兼容旧接口的退出方法。
        参数:
            cls: 类对象。
        """

        cls.quit()

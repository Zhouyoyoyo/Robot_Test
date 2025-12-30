from framework.driver.driver_factory import create_driver


class DriverManager:
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

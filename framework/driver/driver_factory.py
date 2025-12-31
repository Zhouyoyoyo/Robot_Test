from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from framework.utils.config_loader import load_config


def create_driver(browser: str | None = None):
    """Author: taobo.zhou
    中文：根据配置创建并返回浏览器驱动。
    参数:
        browser: 浏览器类型，可为 chrome、edge、firefox，未传则读取配置。
    """

    if browser is None:
        cfg = load_config()
        browser = cfg.get("project", {}).get("browser", "chrome")

    browser = browser.lower()

    if browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        return webdriver.Chrome(options=options)

    if browser == "edge":
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        return webdriver.Edge(options=options)

    if browser == "firefox":
        options = FirefoxOptions()
        return webdriver.Firefox(options=options)

    raise ValueError(f"Unsupported browser: {browser}")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from framework.utils.config_loader import load_config


def create_driver(browser: str | None = None):
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

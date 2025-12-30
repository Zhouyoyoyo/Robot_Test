from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def create_driver(browser: str):
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

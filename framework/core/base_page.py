from framework.interactions.dom import DomMixin
from framework.interactions.wait import WaitMixin
from framework.interactions.js import JsMixin
from framework.interactions.mouse import MouseMixin
from framework.interactions.shadow import ShadowDomMixin
from framework.utils.locator_loader import build_page_locators


class BasePage(
    DomMixin,
    WaitMixin,
    JsMixin,
    MouseMixin,
    ShadowDomMixin,
):
    def __init__(self, driver, locator_loader, page_name=None):
        self.__driver = driver
        self._locators = build_page_locators(locator_loader, page_name)
        self._page_name = page_name
        self._log = self._init_logger()
        self._bind_driver_to_mixins(driver)

    def _init_logger(self):
        from framework.utils.logger import get_page_logger

        return get_page_logger(self._page_name)

    def _bind_driver_to_mixins(self, driver):
        for mixin in (DomMixin, WaitMixin, JsMixin, MouseMixin, ShadowDomMixin):
            setattr(self, f"_{mixin.__name__}__driver", driver)

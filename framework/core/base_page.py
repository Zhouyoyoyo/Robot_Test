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
    """Author: taobo.zhou
    页面基类，提供通用交互与日志能力。
    Base page class providing common interactions and logging.
    """

    def __init__(self, driver, locator_loader, page_name=None):
        """Author: taobo.zhou
        初始化页面基类并绑定驱动与定位器。
        
            driver: WebDriver 实例。
            locator_loader: 定位器加载器实例。
            page_name: 页面名称，可为空。
        """

        self.__driver = driver
        self._locators = build_page_locators(locator_loader, page_name)
        self._page_name = page_name
        self._log = self._init_logger()
        self._bind_driver_to_mixins(driver)

    def _init_logger(self):
        """Author: taobo.zhou
        初始化页面级日志记录器。
         无。
        """

        from framework.utils.logger import get_page_logger

        return get_page_logger(self._page_name)

    def _bind_driver_to_mixins(self, driver):
        """Author: taobo.zhou
        将 WebDriver 绑定到各交互混入类。
        
            driver: WebDriver 实例。
        """

        for mixin in (DomMixin, WaitMixin, JsMixin, MouseMixin, ShadowDomMixin):
            setattr(self, f"_{mixin.__name__}__driver", driver)

    def _before_action(self, action: str, target: str | None = None):
        """Author: taobo.zhou
        动作执行前的钩子方法。
        
            action: 将要执行的动作名称。
            target: 目标元素或定位器名称，可为空。
        """

        pass

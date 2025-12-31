import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WaitMixin:
    """Author: taobo.zhou
    中文：等待交互混入类，提供页面与元素等待能力。
    English: Wait interaction mixin providing page and element waits.
    """

    def wait_page_ready(self, timeout=30):
        """Author: taobo.zhou
        中文：等待页面加载完成且无活动请求。
        参数:
            timeout: 最大等待时间（秒）。
        """

        WebDriverWait(self.__driver, timeout).until(
            lambda d: d.execute_script(
                """
                return document.readyState === 'complete'
                && (!window.jQuery || jQuery.active === 0)
            """
            )
        )

    def wait_dom_stable(self, seconds=0.5):
        """Author: taobo.zhou
        中文：等待指定秒数以确保 DOM 稳定。
        参数:
            seconds: 等待时间（秒）。
        """

        time.sleep(seconds)

    def wait_visible(self, name, timeout=30):
        """Author: taobo.zhou
        中文：等待元素可见。
        参数:
            name: 定位器名称。
            timeout: 最大等待时间（秒）。
        """

        by, value = self._get_locator(name)
        WebDriverWait(self.__driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_element_disabled_to_be_removed(self, name, timeout=30, poll_interval=0.5):
        """Author: taobo.zhou
        中文：等待元素的 disabled 属性被移除。
        参数:
            name: 定位器名称。
            timeout: 最大等待时间（秒）。
            poll_interval: 轮询间隔（秒）。
        """

        start_time = time.time()
        by, value = self._get_locator(name)

        self._log.info(
            f"[WAIT_DISABLED_REMOVE] {self._page_name}.{name} timeout={timeout}s"
        )

        while True:
            try:
                el = self.__driver.find_element(by, value)
                disabled = el.get_attribute("disabled")

                if disabled is None or str(disabled).lower() != "true":
                    elapsed = time.time() - start_time
                    self._log.info(
                        f"元素 {name} disabled 已移除，等待时间：{elapsed:.2f}s"
                    )
                    return True

            except Exception as exc:
                self._log.debug(f"获取元素 {name} disabled 失败：{exc}")

            if time.time() - start_time >= timeout:
                elapsed = time.time() - start_time
                self._log.error(
                    f"等待超时：元素 {name} disabled 仍为 true，等待时间：{elapsed:.2f}s"
                )
                return False

            time.sleep(poll_interval)

    def sleep(self, seconds: float):
        """Author: taobo.zhou
        中文：强制休眠指定时间。
        参数:
            seconds: 休眠时间（秒）。
        """

        self._log.warning(
            f"[SLEEP][FORCED] page={self._page_name} seconds={seconds}"
        )
        time.sleep(seconds)

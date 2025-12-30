"""等待交互模块。

Wait interaction module.

作者: taobo.zhou
Author: taobo.zhou
"""

import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WaitMixin:
    """等待交互混入类。

    Wait interaction mixin.

    作者: taobo.zhou
    Author: taobo.zhou
    """
    def wait_page_ready(self, timeout=30):
        WebDriverWait(self.__driver, timeout).until(
            lambda d: d.execute_script(
                """
                return document.readyState === 'complete'
                && (!window.jQuery || jQuery.active === 0)
            """
            )
        )

    def wait_dom_stable(self, seconds=0.5):
        time.sleep(seconds)

    def wait_visible(self, name, timeout=30):
        by, value = self._get_locator(name)
        WebDriverWait(self.__driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_element_disabled_to_be_removed(self, name, timeout=30, poll_interval=0.5):
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
        self._log.warning(
            f"[SLEEP][FORCED] page={self._page_name} seconds={seconds}"
        )
        time.sleep(seconds)

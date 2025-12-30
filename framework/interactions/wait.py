"""
WaitMixin 职责说明：

1. 页面级等待（page ready / dom stable）
2. 元素级显式等待（visible / clickable / disabled）
3. 不处理业务语义
4. 不包含截图 / 报告逻辑
"""

import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WaitMixin:
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
        """
        强制等待（兜底手段）
        ⚠️ 不推荐使用，优先使用显式 wait
        """
        self._log.warning(
            f"[SLEEP][FORCED] page={self._page_name} seconds={seconds}"
        )
        time.sleep(seconds)

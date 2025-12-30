import time
import logging
from typing import Union, Any

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    InvalidArgumentException,
    TimeoutException,
    JavascriptException,
)

from framework.utils.screenshot import take_screenshot
from framework.utils.config_loader import load_config


def _safe_cfg_get(cfg: dict, keys: list, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _mask_if_sensitive(name: str, text: str) -> str:
    n = (name or "").lower()
    sensitive_keywords = ("password", "passwd", "pwd", "otp", "token", "secret", "code")
    if any(k in n for k in sensitive_keywords):
        return "****"
    return text


class BasePage:
    def __init__(
        self,
        driver,
        locator_loader,
        page_name: str,
        timeout=None,
        screenshot_dir=None,
    ):
        # ✅ 统一从 config.yaml 获取默认值（只有在用户未传入时才启用）
        cfg = load_config()

        if timeout is None:
            timeout = _safe_cfg_get(cfg, ["selenium", "explicit_wait"], 10)

        if screenshot_dir is None:
            screenshot_dir = _safe_cfg_get(cfg, ["paths", "screenshots"], "output/screenshots")

        self.__driver = driver
        self._locator_loader = locator_loader
        self._page_name = page_name
        self._wait = WebDriverWait(driver, timeout)
        self._log = logging.getLogger("automation_logger")
        self._screenshot_dir = screenshot_dir

        try:
            implicit_wait = _safe_cfg_get(cfg, ["selenium", "implicit_wait"], None)
            if implicit_wait is not None:
                self.__driver.implicitly_wait(float(implicit_wait))
        except Exception:
            pass

    # 🚫 明确禁止 Page 层访问 driver
    @property
    def driver(self):
        raise RuntimeError("❌ 禁止在 Page 层直接访问 driver，请使用 BasePage API")

    def open(self, url: str):
        """打开页面。"""
        self._log.info(f"[OPEN] {self._page_name} -> {url}")
        self.__driver.get(url)

    def _get_locator(self, name: str):
        """
        从 LocatorLoader 获取定位器
        LocatorLoader.get(page_name, locator_name)
        """
        loc = self._locator_loader.get(self._page_name, name)
        locator_type = loc["by"]
        locator_value = loc["value"]

        # 根据 locator_type 来判断，返回对应的 By 类型
        if locator_type.lower() == "id":
            return By.ID, locator_value
        elif locator_type.lower() == "xpath":
            return By.XPATH, locator_value
        elif locator_type.lower() == "name":
            return By.NAME, locator_value
        elif locator_type.lower() == "css":
            return By.CSS_SELECTOR, locator_value
        elif locator_type.lower() == "class":
            return By.CLASS_NAME, locator_value
        else:
            raise ValueError(f"Unsupported locator type: {locator_type}")

    def _get_locator_shadow_host(self, name: str):
        """
        从 LocatorLoader 获取定位器
        LocatorLoader.get(page_name, locator_name)
        """
        loc = self._locator_loader.get(self._page_name, name)
        locator_type = loc["by"]
        locator_value = loc["shadow_host"]

        # 根据 locator_type 来判断，返回对应的 By 类型
        if locator_type.lower() == "id":
            return By.ID, locator_value
        elif locator_type.lower() == "xpath":
            return By.XPATH, locator_value
        elif locator_type.lower() == "name":
            return By.NAME, locator_value
        elif locator_type.lower() == "css":
            return By.CSS_SELECTOR, locator_value
        elif locator_type.lower() == "class":
            return By.CLASS_NAME, locator_value
        else:
            raise ValueError(f"Unsupported locator type: {locator_type}")

    # ========= find（懒加载：只在动作发生时才查找） =========
    def _find_presence(self, name: str) -> Any:
        by, value = self._get_locator(name)
        self._log.debug(f"[FIND_PRESENCE] {self._page_name}.{name} ({by}, {value})")
        try:
            return self._wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            screenshot = take_screenshot(self.__driver, self._screenshot_dir)
            raise AssertionError(
                f"Element not found (presence): {self._page_name}.{name}, screenshot={screenshot}"
            )

    def _find_visible(self, name: str) -> Any:
        by, value = self._get_locator(name)
        self._log.debug(f"[FIND_VISIBLE] {self._page_name}.{name} ({by}, {value})")
        try:
            return self._wait.until(EC.visibility_of_element_located((by, value)))
        except TimeoutException:
            screenshot = take_screenshot(self.__driver, self._screenshot_dir)
            self._log.warning(f"Element not found (visible):  {self._page_name}.{name} ({by}, {value})")
            raise AssertionError(
                f"Element not found (visible): {self._page_name}.{name}, screenshot={screenshot}"
            )

    def _find_clickable(self, name: str) -> Any:
        by, value = self._get_locator(name)
        self._log.debug(f"[FIND_CLICKABLE] {self._page_name}.{name} ({by}, {value})")
        try:
            return self._wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            screenshot = take_screenshot(self.__driver, self._screenshot_dir)
            raise AssertionError(
                f"Element not found (clickable): {self._page_name}.{name}, screenshot={screenshot}"
            )

    # ========= 动作 =========
    def click(self, name: str) -> None:
        self._log.info(f"[CLICK] {self._page_name}.{name}")
        self._find_clickable(name).click()

    def js_click(self, name: str) -> None:
        """JavaScript 点击"""
        self._log.info(f"[JS_CLICK] {self._page_name}.{name}")
        el = self._find_visible(name)
        try:
            self.__driver.execute_script("arguments[0].click();", el)
        except JavascriptException as e:
            screenshot = take_screenshot(self.__driver, self._screenshot_dir)
            raise AssertionError(
                f"JS click failed: {self._page_name}.{name}, err={e}, screenshot={screenshot}"
            )

    def mouse_click(self, name: str, double: bool = False) -> None:
        self.scroll_and_wait(name)
        self.sleep(0.5)
        el = self._find_visible(name)
        self._log.info(f"[MOUSE_CLICK] {self._page_name}.{name} double={double}")
        actions = ActionChains(self.__driver)
        if double:
            actions.double_click(el)
        else:
            actions.click(el)
        actions.perform()

    def input(self, name: str, text: str) -> None:
        masked = _mask_if_sensitive(name, text)
        self._log.info(f"[INPUT] {self._page_name}.{name} = {masked}")
        el = self._find_visible(name)
        el.clear()
        el.send_keys(text)


    def input_text_in_shadow_dom(self, locator_name: str, text: str, input_or_textarea: str = 'input'):
        # 定位 Shadow Host（宿主元素）
        self._log.info(f"Starting the process to upload file in Shadow DOM for locator: {locator_name}")

        # 获取定位器信息
        by, value = self._get_locator_shadow_host(locator_name)
        shadow_host = self.__driver.find_element(by, value)

        # 获取 Shadow Root
        shadow_root = self.__driver.execute_script("return arguments[0].shadowRoot", shadow_host)

        # # 在 Shadow DOM 内查找元素，例如：定位到 input 元素
        # by, value = self._get_locator(name)
        # print(f"by, value:{by, value}")
        input_element = None
        match input_or_textarea:
            case 'input':
                    input_element = shadow_root.find_element(By.CSS_SELECTOR, 'input[type="text"]')
            case 'textarea':
                    input_element = shadow_root.find_element(By.CSS_SELECTOR, 'textarea[aria-invalid="false"]')
        # 与 input 元素进行交互，例如：上传文件
        input_element.send_keys(text)  # 这里替换为需要上传的文件路径


    def click_shadow_dom(self, locator_name: str):
        # 定位 Shadow Host（宿主元素）
        self._log.info(f"Starting the process to upload file in Shadow DOM for locator: {locator_name}")

        # 获取定位器信息
        by, value = self._get_locator_shadow_host(locator_name)
        shadow_host = self.__driver.find_element(by, value)

        # 获取 Shadow Root
        shadow_root = self.__driver.execute_script("return arguments[0].shadowRoot", shadow_host)

        # # 在 Shadow DOM 内查找元素，例如：定位到 input 元素
        by, value = self._get_locator(locator_name)
        print(f"by, value:{by, value}")
        shadow_element = shadow_root.find_element(by, value)
        # 与 input 元素进行交互，例如：上传文件
        shadow_element.click()


    def select(self, name: str, option, by: str = "text"):
        """
        Select 下拉框选项
        :param name: locator key
        :param option: value / text / index
        :param by: text | value | index
        """
        self._log.info(f"[SELECT] {self._page_name}.{name} by={by} option={option}")
        element = self._find_visible(name)
        select = Select(element)

        by = (by or "").lower()
        if by == "text":
            select.select_by_visible_text(str(option))
        elif by == "value":
            select.select_by_value(str(option))
        elif by == "index":
            select.select_by_index(int(option))
        else:
            raise ValueError("select(by=) only supports: text | value | index")

    def upload(self, name: str, file_path: str):
        """file input 上传：通常只要求 presence"""
        self._log.info(f"[UPLOAD] {self._page_name}.{name} file={file_path}")
        if not isinstance(file_path, str) or not file_path:
            raise InvalidArgumentException("upload file_path is empty")
        el = self._find_presence(name)
        el.send_keys(file_path)

    def upload_in_shadow_dom(self, name: str, file_path: str):
        # 定位 Shadow Host（宿主元素）
        self._log.info(f"Starting the process to upload file in Shadow DOM for locator: {name}")

        # 获取定位器信息
        by, value = self._get_locator_shadow_host(name)
        shadow_host = self.__driver.find_element(by, value)

        # 获取 Shadow Root
        shadow_root = self.__driver.execute_script("return arguments[0].shadowRoot", shadow_host)

        # # 在 Shadow DOM 内查找元素，例如：定位到 input 元素
        # by, value = self._get_locator(name)
        # print(f"by, value:{by, value}")
        input_element = shadow_root.find_element(By.CSS_SELECTOR, "#input")  # 根据 id 定位

        # 与 input 元素进行交互，例如：上传文件
        input_element.send_keys(file_path)  # 这里替换为你需要上传的文件路径

    # ========= 等待 =========
    def wait_visible(self, name: str, timeout: Union[int, float, None] = None) -> None:
        cfg = load_config()
        if timeout is None:
            timeout = _safe_cfg_get(cfg, ["selenium", "explicit_wait"], 10)

        by, value = self._get_locator(name)
        self._log.info(f"[WAIT_VISIBLE] {self._page_name}.{name} timeout={timeout}")
        try:
            WebDriverWait(self.__driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
        except TimeoutException:
            screenshot = take_screenshot(self.__driver, self._screenshot_dir)
            raise AssertionError(
                f"Wait visible timeout: {self._page_name}.{name}, screenshot={screenshot}"
            )

    def wait_page_ready(self, timeout: Union[int, float, None] = None) -> None:
        """
        全局页面加载完成（document.readyState == 'complete'）
        """
        cfg = load_config()
        if timeout is None:
            timeout = _safe_cfg_get(cfg, ["selenium", "page_load_timeout"], 30)

        self._log.info(f"[WAIT_PAGE_READY] {self._page_name} timeout={timeout}")
        try:
            WebDriverWait(self.__driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            screenshot = take_screenshot(self.__driver, self._screenshot_dir)
            raise AssertionError(
                f"Wait page ready failed: {self._page_name}, err={e}, screenshot={screenshot}"
            )

    def scroll_and_wait(self, name, timeout=30):
        """滚动到元素并等待其可见"""
        # 滚动到元素
        element = self._find_presence(name)
        self.__driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)

    def sleep(self, seconds: Union[int, float]) -> None:
        """单位：秒"""
        self._log.info(f"[SLEEP] {self._page_name} seconds={seconds}")
        time.sleep(float(seconds))

    def set_dom_property(self, locator_name: str, prop: str, value):
        """
        通过 JS 设置 DOM property
        示例：
          set_dom_property("submit_btn", "disabled", False)
          set_dom_property("username", "value", "admin")
        """
        self._log.info(
            "[SET_DOM_PROPERTY] page=%s locator=%s prop=%s value=%s",
            self._page_name,
            locator_name,
            prop,
            value,
        )
        element = self._find_presence(locator_name)
        try:
            self.__driver.execute_script(
                "arguments[0][arguments[1]] = arguments[2];",
                element,
                prop,
                value,
            )
        except JavascriptException as e:
            raise AssertionError(
                f"set_dom_property failed: {locator_name} {prop}={value}, err={e}"
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

                # disabled 只要不是 true（None / false / ""）就认为可用
                if disabled is None or str(disabled).lower() != "true":
                    elapsed = time.time() - start_time
                    self._log.info(
                        f"元素 {name} disabled 已移除，等待时间：{elapsed:.2f}s"
                    )
                    return True

            except Exception as e:
                self._log.debug(f"获取元素 {name} disabled 失败：{e}")

            # 超时判断（防止死循环）
            if time.time() - start_time >= timeout:
                elapsed = time.time() - start_time
                self._log.error(
                    f"等待超时：元素 {name} disabled 仍为 true，等待时间：{elapsed:.2f}s"
                )
                return False

            time.sleep(poll_interval)


    def get_element_attr(self, name, attr_name):
        by, value = self._get_locator(name)
        el = self.__driver.find_element(by, value)
        attr_value = el.get_attribute(attr_name)
        self._log.info(f"获取元素 {name} 的 {attr_name}属性值：{attr_value}")

        return attr_value


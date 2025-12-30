"""登录页面模块。

Login page module.

作者: taobo.zhou
Author: taobo.zhou
"""

from framework.base_page import BasePage
from framework.pingid_reader import PingIDOtpManager


class LoginPage(BasePage):
    """登录页面对象。

    Login page object.

    作者: taobo.zhou
    Author: taobo.zhou
    """
    def __init__(self, driver, locator_loader):
        super().__init__(driver, locator_loader, page_name="LoginPage")

    def login(self, username: str, password: str):
        self.wait_visible("username_input"), "username_input 未出现"
        self.input("username_input", username)
        self.click("next_button")

        self.wait_visible("password_input"), "password_input 未出现"
        self.input("password_input", password)

        self.wait_visible("login_button"), "login_button 未出现"
        self.click("login_button")

        ping_id_manager = PingIDOtpManager.get()

        self.wait_page_ready()
        self.wait_visible("ping_id_input"), "pingID 未出现"

        with ping_id_manager.exclusive(shutdown_after=True):
            ping_id = ping_id_manager.copy_otp()
            self.input("ping_id_input", ping_id)
            self.sleep(0.2)

        self.mouse_click("ping_id_login_button")
        self.sleep(0.5)
        self.wait_page_ready()

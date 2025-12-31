from framework.core.base_page import BasePage
from framework.pingid_reader import PingIDOtpManager


class LoginPage(BasePage):
    """Author: taobo.zhou
    中文：登录页面对象，封装登录流程相关操作。
    English: Login page object that encapsulates login flow operations.
    """

    def __init__(self, driver, locator_loader):
        """Author: taobo.zhou
        中文：初始化登录页面对象。
        参数:
            driver: WebDriver 实例。
            locator_loader: 定位器加载器实例。
        """

        super().__init__(driver, locator_loader, page_name="LoginPage")

    def login(self, username: str, password: str):
        """Author: taobo.zhou
        中文：执行用户登录并完成 PingID 验证。
        参数:
            username: 登录用户名。
            password: 登录密码。
        """

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

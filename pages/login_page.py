from framework.base_page import BasePage
from framework.pingid_reader import PingIDOtpManager


class LoginPage(BasePage):
    def __init__(self, driver, locator_loader):
        super().__init__(driver, locator_loader, page_name="LoginPage")

    def login(self, username: str, password: str):
        # 对齐 locators/locator.yaml 的 key
        # 多步骤登录页：每一步都显式等待对应控件出现，避免“页面未就绪就操作”导致定位/点击失败
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

        # ✅ PingID 多线程互斥：同一时间只允许一个用例拿 OTP
        # 且“用完就关”，避免窗口/剪贴板状态污染下一个用例
        with ping_id_manager.exclusive(shutdown_after=True):
            ping_id = ping_id_manager.copy_otp()
            self.input("ping_id_input", ping_id)
            self.sleep(0.2)

        self.mouse_click("ping_id_login_button")
        self.sleep(0.5)
        self.wait_page_ready()

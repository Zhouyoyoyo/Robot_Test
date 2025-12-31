from framework.core.base_page import BasePage


class SoftwareContainerPage(BasePage):
    """Author: taobo.zhou
    中文：软件容器页面对象，封装版本创建与上传流程。
    English: Software container page object for version creation and upload flows.
    """

    def __init__(self, driver, locator_loader):
        """Author: taobo.zhou
        中文：初始化软件容器页面对象。
        参数:
            driver: WebDriver 实例。
            locator_loader: 定位器加载器实例。
        """

        super().__init__(driver, locator_loader, page_name="SoftwareContainerPage")

    def create_version(
        self,
        version: str,
        semantic_version: str,
        general_setting: str,
        software_part_number: str,
        software_YMP_version: str,
        dependencies: str,
        file_upload_ODX_F: str,
        file_upload_flashware: str,
    ):
        """Author: taobo.zhou
        中文：创建软件容器版本并完成文件上传。
        参数:
            version: 版本选择值。
            semantic_version: 语义版本号。
            general_setting: 通用设置选项。
            software_part_number: 软件零件号。
            software_YMP_version: 软件 YMP 版本。
            dependencies: 依赖项描述。
            file_upload_ODX_F: ODX_F 文件路径。
            file_upload_flashware: Flashware 文件路径。
        """

        self.wait_visible("create_version_button", 45)
        self.click("create_version_button")

        self.wait_visible("select_version")
        self.sleep(1.5)
        self.select("select_version", version)
        if self.get_element_attr("release_candidate", "class").strip().endswith("unchecked"):
            self.click("release_candidate")
        if self.get_element_attr("MB_conform_flashable", "class").strip().endswith("unchecked"):
            self.click("MB_conform_flashable")
        self.sleep(5.5)
        self.click("next_button")

        self.wait_visible("general_setting")
        self.wait_page_ready()
        self.select("general_setting", general_setting)
        self.sleep(1.5)
        self.input_text_in_shadow_dom("semantic_version", semantic_version)
        self.input_text_in_shadow_dom("software_part_number", software_part_number)
        self.input_text_in_shadow_dom("software_YMP_version", software_YMP_version)
        self.input_text_in_shadow_dom("dependencies", dependencies, "textarea")
        self.upload_in_shadow_dom("file_upload_ODX_F", file_upload_ODX_F)
        self.upload_in_shadow_dom("file_upload_flashware", file_upload_flashware)
        if not self.wait_for_element_disabled_to_be_removed("upload_button", 10):
            raise AssertionError("upload按钮无法点击，请检查！")
        self.mouse_click("upload_button")

        if not self.wait_for_element_disabled_to_be_removed("next_button", 60 * 5):
            raise AssertionError("next按钮无法点击，请检查！")
        self.mouse_click("next_button")

        if not self.wait_for_element_disabled_to_be_removed("version_confirm_button", 60):
            raise AssertionError("create version按钮无法点击，请检查！")

        self.mouse_click("version_confirm_button")

        self.wait_visible("succeeded", 60 * 5)

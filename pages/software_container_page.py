"""软件容器页面模块。

Software container page module.

Author: taobo.zhou
"""

from framework.base_page import BasePage


class SoftwareContainerPage(BasePage):
    """软件容器页面对象。

    Software container page object.

    Author: taobo.zhou
    """
    def __init__(self, driver, locator_loader):
        super().__init__(driver, locator_loader, page_name="SoftwareContainerPage")

    def create_version(self,
                       version: str,
                       semantic_version: str,
                       general_setting: str,
                       software_part_number: str,
                       software_YMP_version: str,
                       dependencies: str,
                       file_upload_ODX_F: str,
                       file_upload_flashware: str,
                       ):
        self.wait_visible("create_version_button",45)
        self.click("create_version_button")

        self.wait_visible("select_version")
        self.sleep(1.5)
        self.select("select_version", version)
        if self.get_element_attr("release_candidate","class").strip().endswith("unchecked"):
            self.click("release_candidate")
        if self.get_element_attr("MB_conform_flashable","class").strip().endswith("unchecked"):
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
        self.input_text_in_shadow_dom("dependencies", dependencies,'textarea')
        self.upload_in_shadow_dom("file_upload_ODX_F", file_upload_ODX_F)
        self.upload_in_shadow_dom("file_upload_flashware", file_upload_flashware)
        if not self.wait_for_element_disabled_to_be_removed("upload_button",10):
            raise AssertionError("upload按钮无法点击，请检查！")
        self.mouse_click("upload_button")

        if not self.wait_for_element_disabled_to_be_removed("next_button",60*5):
            raise AssertionError("next按钮无法点击，请检查！")
        self.mouse_click("next_button")

        if not self.wait_for_element_disabled_to_be_removed("version_confirm_button",60):
            raise AssertionError("create version按钮无法点击，请检查！")

        self.mouse_click("version_confirm_button")

        self.wait_visible("succeeded",60*5)








"""自动化上传测试模块。

Automated uploading test module.

作者: taobo.zhou
Author: taobo.zhou
"""

from pages.login_page import LoginPage
from framework.utils.excel_loader import load_excel_kv
from pages.software_container_page import SoftwareContainerPage


def test_software_container(driver, config):
    data = load_excel_kv(config["paths"]["data"])

    username = data["login.username"]
    password = data["login.password"]
    url = data.get("login.url", config["project"]["aurix_app_url"])

    page_login = LoginPage(driver, config["locator_loader"])
    page_login.open(url)
    page_login.wait_page_ready()

    page_login.wait_visible("next_button"), (
        "登录页加载失败：next_button 不可见（检查 url / locator / 页面是否可访问）"
    )

    page_login.login(username, password)

    page = SoftwareContainerPage(driver, config["locator_loader"])
    page.create_version(
        data["version"],
        data["semantic_version"],
        data["general_setting"],
        data["software_part_number"],
        data["software_YMP_version"],
        data["dependencies"],
        data["file_upload_ODX_F"],
        data["file_upload_flashware"],
    )


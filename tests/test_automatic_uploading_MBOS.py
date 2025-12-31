from pages.login_page import LoginPage
from pages.software_container_page import SoftwareContainerPage


def test_automatic_uploading_MBOS(
    driver,
    config,
    sheet_name,
    case_data,
    base_url,
):
    """Author: taobo.zhou
    中文：执行自动化上传用例。
    参数:
        driver: WebDriver 实例，用于页面操作。
        config: 全局配置字典，包含定位器加载器等信息。
        sheet_name: 用例数据所在的 sheet 名称。
        case_data: 用例数据字典。
        base_url: 用例对应的基础 URL。
    """

    data = case_data
    url = base_url

    username = data["login.username"]
    password = data["login.password"]

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

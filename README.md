# Robot_Test

## 📌 项目简介 / Project Overview

`Robot_Test` 是一个基于 **Selenium + Pytest** 的自动化测试框架，  
支持 **数据驱动测试（Excel）**、**多 Sheet 执行**、**失败重跑**，并在  
**每个测试用例执行过程中自动保存浏览器页面截图**，  
最终统一生成 **JSON 结果、日志与测试报告**，用于后续汇总与邮件发送。

---

## 🚀 使用步骤 / Usage Steps

### 1️⃣ 环境准备 / Environment Setup

#### Python 环境

- **Python 版本要求**：`Python 3.10+`
- 推荐使用虚拟环境（venv / virtualenv）

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
安装依赖 / Install Dependencies
bash
复制代码
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
主要依赖包括（但不限于）：

selenium

pytest

openpyxl

pyyaml

psutil

pywin32

2️⃣ 配置文件准备 / Configuration
2.1 全局配置 / Global Config
编辑 config.yaml，配置 Selenium 与输出路径等信息：

yaml
复制代码
selenium:
  browser: chrome
  implicit_wait: 5
  page_load_timeout: 30

paths:
  output: output
  logs: logs
  screenshots: screenshots
2.2 元素定位配置 / Locator Config
编辑：

bash
复制代码
locators/locator.yaml
用于集中管理页面元素定位方式（id / xpath / css / shadow dom 等），
避免在 Page Object 中硬编码定位器。

2.3 测试数据准备 / Test Data
编辑 Excel 文件：

bash
复制代码
data/testdata.xlsx
说明：

每个 Sheet 表示一组测试场景

支持通过命令行参数指定 Sheet 执行

测试数据会自动注入 pytest 用例

3️⃣ 执行测试 / Run Tests
方式一：通过 run.py（推荐）
bash
复制代码
python run.py
特点：

自动创建 run 目录

支持多 Sheet 串行执行

自动汇总每个 Sheet 的测试结果

生成统一 JSON 结果文件

方式二：直接使用 pytest
bash
复制代码
pytest
或指定 Sheet：

bash
复制代码
pytest --pw-sheet aurix_app
4️⃣ 浏览器截图机制说明 / Browser Screenshot Mechanism
📸 截图行为说明
每个测试用例都会生成 一张 Selenium 浏览器页面截图

截图内容为 用例执行时浏览器中的真实页面

适用于：

用例成功（PASSED）

用例失败（FAILED）

异常中断（ERROR）

跳过执行（SKIPPED）

❌ 不保存浏览器关闭后的截图
❌ 不截取 Windows 桌面或系统窗口

截图文件示例：

复制代码
aurix_fbl__tests_test_automatic_uploading_MBOS_CALL.png
5️⃣ 输出结构 / Output Structure
测试执行完成后，将生成如下目录结构：

lua
复制代码
output/
└── runs/
    └── 20260104_141333/
        ├── aurix_app/
        │   ├── screenshots/
        │   ├── reports/
        │   │   └── results.json
        │   └── logs/
        └── aurix_fbl/
            ├── screenshots/
            ├── reports/
            └── logs/
6️⃣ 结果与日志 / Results & Logs
运行日志：logs/

测试结果 JSON：reports/results.json

截图路径：

已统一转换为字符串

可直接用于邮件、HTML 报告、后处理脚本

✅ 设计要点总结 / Design Highlights
✔ 自动保存 Selenium 浏览器页面截图

✔ 不影响现有用例执行流程

✔ driver 生命周期保持原样

✔ 结果数据可安全序列化为 JSON

✔ 支持本地与 CI 环境

✔ 易扩展邮件与报告系统

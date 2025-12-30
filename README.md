# Robot_Test

## 使用步骤 / Usage Steps

1. 安装 Python 3.10+ 并创建虚拟环境，然后安装依赖   `pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`
（如 selenium、pytest、openpyxl、pyyaml、psutil、pywin32）。
   Install Python 3.10+ and create a virtual environment, then install dependencies (e.g., selenium, pytest, openpyxl, pyyaml, psutil, pywin32).
2. 配置 `config.yaml`、`locators/locator.yaml`，并在 `data/testdata.xlsx` 中准备测试数据。
   Configure `config.yaml`, `locators/locator.yaml`, and prepare test data in `data/testdata.xlsx`.
3. 运行测试：`python run.py` 或 `pytest`。
   Run tests: `python run.py` or `pytest`.
4. 查看输出结果与报告：`output/`、`logs/`。
   Review outputs and reports in `output/` and `logs/`.

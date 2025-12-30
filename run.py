"""运行入口模块。

Run entry module.

作者: taobo.zhou
Author: taobo.zhou
"""

from framework.utils.pytest_args import build_pytest_args

if __name__ == "__main__":
    import pytest
    import sys

    args = build_pytest_args()
    code = pytest.main(args)
    sys.exit(code)

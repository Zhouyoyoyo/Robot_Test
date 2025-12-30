"""pytest 参数构建模块。

pytest args builder module.

作者: taobo.zhou
Author: taobo.zhou
"""

import sys


def build_pytest_args() -> list[str]:
    return sys.argv[1:]

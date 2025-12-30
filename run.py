import sys
import pytest


def main() -> int:
    # 只启动 pytest，不做任何业务逻辑
    args = [
        "-q",
    ]
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())

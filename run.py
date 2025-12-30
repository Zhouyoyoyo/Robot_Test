from framework.utils.pytest_args import build_pytest_args

if __name__ == "__main__":
    import pytest
    import sys

    args = build_pytest_args()
    code = pytest.main(args)
    sys.exit(code)

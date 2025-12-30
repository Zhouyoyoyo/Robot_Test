import pytest


def main() -> int:
    return pytest.main(["-q"])


if __name__ == "__main__":
    raise SystemExit(main())

import sys
import unittest


MIN_VERSION = (3, 8)


class TestPythonVersion(unittest.TestCase):
    """Fail fast if running on an unsupported Python version.

    This encodes the minimum Python version expected for ControlCamera,
    matching the README badge (3.8+).
    """

    def test_python_version_supported(self):
        current = sys.version_info[:2]
        self.assertGreaterEqual(
            current,
            MIN_VERSION,
            msg=f"ControlCamera requires Python {MIN_VERSION[0]}.{MIN_VERSION[1]} or newer, "
                f"but tests are running on {current[0]}.{current[1]}",
        )


if __name__ == "__main__":
    unittest.main()

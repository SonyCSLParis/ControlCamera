import unittest
from unittest.mock import patch
from pathlib import Path
import importlib

from ControlCamera import ControlCamera
cc_module = importlib.import_module("ControlCamera.ControlCamera")


# MMconfig path as used in regular usage; CI will run tests from the
# Tests directory so relative paths inside the JSON remain valid.
MMCONFIG_DIR = "MMconfig"
CONFIG_FILE = MMCONFIG_DIR + "/Daheng.json"


class FakeCore:
    """Minimal fake Micro-Manager core for parameter tests.

    It records setProperty/getProperty calls in-memory and ignores
    configuration loading so no real hardware or MM installation is needed.
    """

    def __init__(self):
        self.properties = {}

    def loadSystemConfiguration(self, cfg_path):
        # No-op in tests
        self.loaded_cfg = cfg_path

    def setProperty(self, device, key, value):
        self.properties[(device, key)] = value

    def getProperty(self, device, key):
        return self.properties.get((device, key), None)


class TestControlCameraParams(unittest.TestCase):
    """Hardware‑free tests focusing on camera parameter handling."""

    def setUp(self):
        # Patch CMMCorePlus.instance() as used in the ControlCamera implementation
        # module so that it returns our FakeCore instead of real hardware.
        self._patcher = patch.object(cc_module, "CMMCorePlus")
        MockCoreClass = self._patcher.start()

        self.fake_core = FakeCore()
        MockCoreClass.instance.return_value = self.fake_core

        cam_params = {"Exposure(us)": "10"}
        self.camera = ControlCamera(str(CONFIG_FILE), cam_params)

    def tearDown(self):
        self._patcher.stop()

    def test_update_and_get_param_roundtrip(self):
        # Changing a parameter should be visible via get_param
        self.camera.update_param("Exposure(us)", "20")
        value = self.camera.get_param("Exposure(us)")
        self.assertEqual(value, "20")

    def test_initial_config_applies_some_properties(self):
        # __init__ should have pushed at least one property into the core
        self.assertGreater(len(self.fake_core.properties), 0)


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import subprocess

import pytest

CHIP_PATH = "/dev/gpiochip0"
SIM_PATH = "/sys/devices/platform/gpio-sim.0/gpiochip0"


class GpioSim:
    def __init__(self):
        self.p = Path(SIM_PATH)

    def poke(self, num, val):
        p = self.p / f"sim_gpio{num}" / "pull"
        p.write_text("pull-up" if val else "pull-down")

    def peek(self, n):
        p = self.p / f"sim_gpio{n}" / "value"
        return int(p.read_text())


@pytest.fixture
def chip_path():
    assert Path(CHIP_PATH).exists(), "gpiochip not found"
    assert Path(SIM_PATH).exists(), "gpio-sim not configured"
    return CHIP_PATH


@pytest.fixture
def gpiosim():
    return GpioSim()


@pytest.fixture(scope="session")
def c_data():
    subprocess.run("make")
    return json.load(open("data.json", "rb"))

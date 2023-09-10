import json
import time
import gpio


def test_get_chip_info(chip_path):
    chip = gpio.chip(chip_path)
    info = chip.info()
    assert info["name"] == "gpiochip0"
    assert info["label"] == "gpiochip0"
    assert len(info["lines"]) == 24


def test_line_request_wo_args(chip_path):
    chip = gpio.chip(chip_path)
    line = chip.request([1, 2, 3])
    assert line.get_bits(0xF) == 0


def test_line_request_w_consumer(chip_path):
    chip = gpio.chip(chip_path)
    line = chip.request([3], consumer="test!")
    info = chip.info()
    assert info["lines"][3]["consumer"] == "test!"


def test_line_request_w_flags(chip_path):
    flags = ["ACTIVE_LOW", "OUTPUT", "OPEN_DRAIN"]
    chip = gpio.chip(chip_path)
    line = chip.request([2, 3], flags=flags)
    info = chip.info()
    assert info["lines"][1]["flags"] == ["INPUT"]
    assert info["lines"][2]["flags"] == ["USED"] + flags
    assert info["lines"][3]["flags"] == ["USED"] + flags


def test_get_set(chip_path, gpiosim):
    flags = ["OUTPUT"]
    chip = gpio.chip(chip_path)
    line = chip.request([6, 7, 4, 5], consumer="test", flags=flags)

    line.set({4: True, 5: False, 6: False, 7: True})
    values = line.get()
    assert values[4] == True
    assert values[5] == False
    assert values[6] == False
    assert values[7] == True

    assert gpiosim.peek(4) == 1
    assert gpiosim.peek(5) == 0
    assert gpiosim.peek(6) == 0
    assert gpiosim.peek(7) == 1

    line.set({"7": 0, "6": 1})
    values = line.get()
    assert values[6] == True
    assert values[7] == False

    assert gpiosim.peek(6) == 1
    assert gpiosim.peek(7) == 0


def test_line_request_w_attrs(chip_path):
    attrs = [
        {"flags": ["OUTPUT", "OPEN_DRAIN"], "mask": 1},
        {"flags": ["OUTPUT", "OPEN_SOURCE"], "mask": 2},
    ]

    chip = gpio.chip(chip_path)
    line = chip.request([8, 9], attrs=attrs)
    info = chip.info()

    assert info["lines"][8]["flags"] == ["USED", "OUTPUT", "OPEN_DRAIN"]
    assert info["lines"][9]["flags"] == ["USED", "OUTPUT", "OPEN_SOURCE"]


def test_round_tripped_line_request(chip_path):
    data = {
        "offsets": [10, 11, 12, 13],
        "consumer": "test again",
        "flags": ["INPUT", "BIAS_DISABLED"],
        "attrs": [
            {"flags": ["OUTPUT", "OPEN_DRAIN"], "mask": 0b10},
            {"flags": ["INPUT", "BIAS_PULL_UP"], "mask": 0b100},
        ],
    }

    req = json.loads(json.dumps(data))
    chip = gpio.chip(chip_path)
    line = chip.request(**req)
    info = chip.info()

    assert info["lines"][10]["flags"] == ["USED", "INPUT", "BIAS_DISABLED"]
    assert info["lines"][11]["flags"] == ["USED", "OUTPUT", "OPEN_DRAIN"]
    assert info["lines"][12]["flags"] == ["USED", "INPUT", "BIAS_PULL_UP"]
    assert info["lines"][13]["flags"] == ["USED", "INPUT", "BIAS_DISABLED"]


def test_wait_timeout(chip_path):
    flags = ["INPUT", "EDGE_RISING", "EDGE_FALLING"]
    chip = gpio.chip(chip_path)
    line = chip.request([14, 15], flags=flags)
    event = line.wait(2)
    assert event == None


def test_wait_line_event(chip_path, gpiosim):
    flags = ["INPUT", "EDGE_RISING", "EDGE_FALLING"]
    chip = gpio.chip(chip_path)
    line = chip.request([14, 15], flags=flags)
    gpiosim.poke(14, 1)
    time.sleep(1)
    gpiosim.poke(14, 0)

    event = line.wait(1)
    assert event["timestamp_ns"]
    assert event["id"] == "RISING_EDGE"
    assert event["offset"] == 14
    assert event["seqno"] == 1
    assert event["line_seqno"] == 1

    event = line.wait(1)
    assert event["timestamp_ns"]
    assert event["id"] == "FALLING_EDGE"
    assert event["offset"] == 14
    assert event["seqno"] == 2
    assert event["line_seqno"] == 2


def test_wait_line_info_changed(chip_path):
    chip = gpio.chip(chip_path)
    chip.watch(7)

    def req():
        line = chip.request([7], consumer="test10", flags=["INPUT"])
        event = chip.wait(1)
        assert event["timestamp_ns"]
        assert event["event_type"] == "LINE_REQUESTED"
        assert event["info"]["consumer"] == "test10"
        assert event["info"]["offset"] == 7
        assert event["info"]["flags"] == ["USED", "INPUT"]

    req()
    event = chip.wait(1)
    assert event["timestamp_ns"]
    assert event["event_type"] == "LINE_RELEASED"
    assert event["info"]["consumer"] == ""
    assert event["info"]["offset"] == 7
    assert event["info"]["flags"] == ["INPUT"]

    chip.unwatch(7)
    assert chip.wait(1) == None


def test_wait_config_changed(chip_path):
    chip = gpio.chip(chip_path)
    chip.watch(16)
    line = chip.request([16], consumer="a")
    chip.wait(0.1)

    flags = ["INPUT", "EDGE_RISING"]
    attrs = [
        {"flags": ["INPUT", "BIAS_PULL_UP"], "mask": 1},
    ]
    line.set_config(flags=flags, attrs=attrs)

    event = chip.wait(0.1)
    assert event["timestamp_ns"]
    assert event["event_type"] == "CONFIG_CHANGED"
    assert event["info"]["consumer"] == "a"
    assert event["info"]["offset"] == 16
    assert event["info"]["flags"] == [
        "USED",
        "INPUT",
        "BIAS_PULL_UP",
    ]

    chip.unwatch(16)
    assert chip.wait(0.1) == None

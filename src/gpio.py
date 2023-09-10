# MIT License
#
# Copyright (c) 2023 mkfoo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Library for interfacing with Linux GPIO character device API
"""

__version__ = "0.0.0-alpha1"

from fcntl import ioctl
from ctypes import (
    Structure,
    Union,
    c_char,
    c_int32,
    c_uint32,
    c_uint64,
    sizeof,
)
from io import FileIO
import select
from typing import Dict, List, Optional

############################################################################
# Userspace declarations:
# https://github.com/torvalds/linux/blob/master/include/uapi/linux/gpio.h#L1

GPIO_MAX_NAME_SIZE = 32  # L23


class gpiochip_info(Structure):  # L32
    _fields_ = [
        ("name", c_char * GPIO_MAX_NAME_SIZE),
        ("label", c_char * GPIO_MAX_NAME_SIZE),
        ("lines", c_uint32),
    ]


GPIO_V2_LINES_MAX = 64  # L45

GPIO_V2_LINE_NUM_ATTRS_MAX = 10  # L51

# gpio_v2_line_flag
GPIO_V2_LINE_FLAG_USED = 1 << 0  # L73

GPIO_V2_LINE_FLAG_ACTIVE_LOW = 1 << 1  # L74

GPIO_V2_LINE_FLAG_INPUT = 1 << 2  # L75

GPIO_V2_LINE_FLAG_OUTPUT = 1 << 3  # L76

GPIO_V2_LINE_FLAG_EDGE_RISING = 1 << 4  # L77

GPIO_V2_LINE_FLAG_EDGE_FALLING = 1 << 5  # L78

GPIO_V2_LINE_FLAG_OPEN_DRAIN = 1 << 6  # L79

GPIO_V2_LINE_FLAG_OPEN_SOURCE = 1 << 7  # L80

GPIO_V2_LINE_FLAG_BIAS_PULL_UP = 1 << 8  # L81

GPIO_V2_LINE_FLAG_BIAS_PULL_DOWN = 1 << 9  # L82

GPIO_V2_LINE_FLAG_BIAS_DISABLED = 1 << 10  # L83

GPIO_V2_LINE_FLAG_EVENT_CLOCK_REALTIME = 1 << 11  # L84

GPIO_V2_LINE_FLAG_EVENT_CLOCK_HTE = 1 << 12  # L85


class gpio_v2_line_values(Structure):  # L96
    _pack_ = 8
    _fields_ = [
        ("bits", c_uint64),
        ("mask", c_uint64),
    ]


# gpio_v2_line_attr_id
GPIO_V2_LINE_ATTR_ID_FLAGS = 1  # L109

GPIO_V2_LINE_ATTR_ID_OUTPUT_VALUES = 2  # L110

GPIO_V2_LINE_ATTR_ID_DEBOUNCE = 3  # L111


class _attr_union(Union):
    _pack_ = 8
    _fields_ = [
        ("flags", c_uint64),
        ("values", c_uint64),
        ("debounce_period_us", c_uint32),
    ]


class gpio_v2_line_attribute(Structure):  # L130
    _pack_ = 8
    _anonymous = ("u",)
    _fields_ = [
        ("id", c_uint32),
        ("padding", c_uint32),
        ("u", _attr_union),
    ]


class gpio_v2_line_config_attribute(Structure):  # L148
    _pack_ = 8
    _fields_ = [
        ("attr", gpio_v2_line_attribute),
        ("mask", c_uint64),
    ]


class gpio_v2_line_config(Structure):  # L167
    _pack_ = 8
    _fields_ = [
        ("flags", c_uint64),
        ("num_attrs", c_uint32),
        ("padding", c_uint32 * 5),
        ("attrs", gpio_v2_line_config_attribute * GPIO_V2_LINE_NUM_ATTRS_MAX),
    ]


class gpio_v2_line_request(Structure):  # L196
    _fields_ = [
        ("offsets", c_uint32 * GPIO_V2_LINES_MAX),
        ("consumer", c_char * GPIO_MAX_NAME_SIZE),
        ("config", gpio_v2_line_config),
        ("num_lines", c_uint32),
        ("event_buffer_size", c_uint32),
        ("padding", c_uint32 * 5),
        ("fd", c_int32),
    ]


class gpio_v2_line_info(Structure):  # L224
    _pack_ = 8
    _fields_ = [
        ("name", c_char * GPIO_MAX_NAME_SIZE),
        ("consumer", c_char * GPIO_MAX_NAME_SIZE),
        ("offset", c_uint32),
        ("num_attrs", c_uint32),
        ("flags", c_uint64),
        ("attrs", gpio_v2_line_attribute * GPIO_V2_LINE_NUM_ATTRS_MAX),
        ("padding", c_uint32 * 4),
    ]


# gpio_v2_line_changed_type
GPIO_V2_LINE_CHANGED_REQUESTED = 1  # L243

GPIO_V2_LINE_CHANGED_RELEASED = 2  # L244

GPIO_V2_LINE_CHANGED_CONFIG = 3  # L245


class gpio_v2_line_info_changed(Structure):  # L257
    _pack_ = 8
    _fields_ = [
        ("info", gpio_v2_line_info),
        ("timestamp_ns", c_uint64),
        ("event_type", c_uint32),
        ("padding", c_uint32 * 5),
    ]


# gpio_v2_line_event_id
GPIO_V2_LINE_EVENT_RISING_EDGE = 1  # L271

GPIO_V2_LINE_EVENT_FALLING_EDGE = 2  # L272


class gpio_v2_line_event(Structure):  # L293
    _pack_ = 8
    _fields_ = [
        ("timestamp_ns", c_uint64),
        ("id", c_uint32),
        ("offset", c_uint32),
        ("seqno", c_uint32),
        ("line_seqno", c_uint32),
        ("padding", c_uint32 * 6),
    ]


GPIO_GET_CHIPINFO_IOCTL = 0x8044B401  # L505

GPIO_GET_LINEINFO_UNWATCH_IOCTL = 0xC004B40C  # L506

GPIO_V2_GET_LINEINFO_IOCTL = 0xC100B405  # L511

GPIO_V2_GET_LINEINFO_WATCH_IOCTL = 0xC100B406  # L512

GPIO_V2_GET_LINE_IOCTL = 0xC250B407  # L513

GPIO_V2_LINE_SET_CONFIG_IOCTL = 0xC110B40D  # L514

GPIO_V2_LINE_GET_VALUES_IOCTL = 0xC010B40E  # L515

GPIO_V2_LINE_SET_VALUES_IOCTL = 0xC010B40F  # L516

##################################################################################

U32_MAX = 0xFFFFFFFF

U64_MAX = 0xFFFFFFFFFFFFFFFF


class Lines:
    """
    Abstraction over a set of configured GPIO lines.
    """

    def __init__(self, fd, offsets):
        """
        Constructor is subject to change; do not use.
        """
        self._epoll = None
        self._file = FileIO(fd)
        self._bit_offsets = dict((v, i) for (i, v) in enumerate(offsets))
        self._values = gpio_v2_line_values()

    def get_bits_unchecked(self, mask: int) -> int:
        """
        Get GPIO line states as a bitmask without checking for overflow.
        """
        self._values.bits = 0
        self._values.mask = mask
        ioctl(self._file.fileno(), GPIO_V2_LINE_GET_VALUES_IOCTL, self._values)
        return self._values.bits

    def set_bits_unchecked(self, bits: int, mask: int):
        """
        Set GPIO line states from a bitmask without checking for overflow.
        """
        self._values.bits = bits
        self._values.mask = mask
        ioctl(self._file.fileno(), GPIO_V2_LINE_SET_VALUES_IOCTL, self._values)

    def get_bits(self, mask: int) -> int:
        """
        Lower-level function to directly get GPIO line states as a bitmask.
        """
        assert 0 <= mask <= U64_MAX, "mask out of range"
        return self.get_bits_unchecked(mask)

    def set_bits(self, bits: int, mask: int):
        """
        Lower-level function to directly set GPIO line states from a bitmask.
        """
        assert 0 <= bits <= U64_MAX, "bits out of range"
        assert 0 <= mask <= U64_MAX, "mask out of range"
        self.set_bits_unchecked(bits, mask)

    def get(self) -> Dict[int, bool]:
        """
        Convenience function to get GPIO line states as a dict of offsets and values.
        """
        bits = self.get_bits(U64_MAX)
        return dict((k, bool(bits & 1 << v)) for (k, v) in self._bit_offsets.items())

    def set(self, values: Dict[int, bool]):
        """
        Convenience function to set GPIO line states from a dict of offsets and values.
        """
        bits = 0
        mask = 0

        for k, v in values.items():
            offset = int(k)
            assert offset in self._bit_offsets, f"offset {offset} not configured"
            shift = self._bit_offsets[offset]
            bits |= bool(v) << shift
            mask |= 1 << shift

        self.set_bits(bits, mask)

    def set_config(
        self, flags: Optional[List[str]] = None, attrs: Optional[List[Dict]] = None
    ):
        """
        Reconfigure this set of GPIO lines.
        """
        attrs = list(Chip._build_attrs(attrs or []))
        num_attrs = len(attrs)
        config = gpio_v2_line_config(
            flags=Chip._build_flags(flags), num_attrs=num_attrs
        )
        config.attrs[:num_attrs] = attrs
        ioctl(self._file.fileno(), GPIO_V2_LINE_SET_CONFIG_IOCTL, config)

    def wait(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        Wait for the next edge event on this set of GPIO lines.
        """
        if not self._epoll:
            self._epoll = select.epoll()
            fd = self._file.fileno()
            self._epoll.register(fd, select.EPOLLIN)

        fds = self._epoll.poll(timeout=timeout)

        if not fds:
            return None

        assert not fds[0][1] & select.EPOLLERR, "EPOLLERR"
        event = gpio_v2_line_event()
        ret = self._file.readinto(event)
        assert ret == sizeof(gpio_v2_line_event)

        return {
            "timestamp_ns": event.timestamp_ns,
            "id": "RISING_EDGE"
            if event.id == GPIO_V2_LINE_EVENT_RISING_EDGE
            else "FALLING_EDGE"
            if event.id == GPIO_V2_LINE_EVENT_FALLING_EDGE
            else "???",
            "offset": event.offset,
            "seqno": event.seqno,
            "line_seqno": event.line_seqno,
        }


class Chip:
    """
    Abstraction over one logical device that manages multiple GPIO lines.
    """

    _flags = dict(
        (k, v) for (k, v) in globals().items() if k.startswith("GPIO_V2_LINE_FLAG_")
    )

    def __init__(self, path):
        """
        Constructor is subject to change; do not use.
        """
        self._epoll = None
        self._file = FileIO(path)

    def _get_chip_info(self):
        chip_info = gpiochip_info()
        ioctl(self._file.fileno(), GPIO_GET_CHIPINFO_IOCTL, chip_info)
        return chip_info

    def _get_line_info(self, offset):
        line_info = gpio_v2_line_info(offset=offset)
        ioctl(self._file.fileno(), GPIO_V2_GET_LINEINFO_IOCTL, line_info)
        return line_info

    def _get_line(self, offsets, consumer, flags, attrs, event_buffer_size=0):
        num_lines = len(offsets)
        num_attrs = len(attrs)
        config = gpio_v2_line_config(flags=flags, num_attrs=num_attrs)
        config.attrs[:num_attrs] = attrs

        request = gpio_v2_line_request(
            config=config,
            num_lines=num_lines,
            event_buffer_size=event_buffer_size,
        )

        if consumer:
            request.consumer = consumer.encode()

        request.offsets[:num_lines] = offsets
        ioctl(self._file.fileno(), GPIO_V2_GET_LINE_IOCTL, request)
        return request.fd

    def _iter_lines(self, lines):
        for i in range(lines):
            line_info = self._get_line_info(i)
            yield line_info

    def _iter_flags(self, flags):
        for name, value in self._flags.items():
            if flags & value:
                yield name.replace("GPIO_V2_LINE_FLAG_", "")

    @classmethod
    def _build_flags(cls, flags):
        ret = 0

        if flags:
            for name in flags:
                value = cls._flags.get("GPIO_V2_LINE_FLAG_" + name, 0)
                ret |= value

        return ret

    @staticmethod
    def _iter_attrs(num_attrs, attrs):
        for i in range(num_attrs):
            attr = attrs[i]

            if attr.id == GPIO_V2_LINE_ATTR_ID_FLAGS:
                yield {"flags": attr.u.flags}
            elif attr.id == GPIO_V2_LINE_ATTR_ID_OUTPUT_VALUES:
                yield {"values": attr.u.values}
            elif attr.id == GPIO_V2_LINE_ATTR_ID_DEBOUNCE:
                yield {"debounce_period_us": attr.u.debounce_period_us}
            else:
                pass

    @classmethod
    def _build_attrs(cls, attrs):
        assert len(attrs) <= GPIO_V2_LINE_NUM_ATTRS_MAX, "too many attributes"

        for a in attrs:
            mask = a["mask"]
            assert 0 <= mask <= U64_MAX, "mask out of range"

            if "flags" in a:
                flags = cls._build_flags(a["flags"])
                attr = gpio_v2_line_attribute()
                attr.id = GPIO_V2_LINE_ATTR_ID_FLAGS
                attr.u.flags = flags
                yield gpio_v2_line_config_attribute(mask=mask, attr=attr)
            elif "values" in a:
                values = a["values"]
                assert 0 <= values <= U64_MAX, "values out of range"
                attr = gpio_v2_line_attribute()
                attr.id = GPIO_V2_LINE_ATTR_ID_OUTPUT_VALUES
                attr.u.values = values
                yield gpio_v2_line_config_attribute(mask=mask, attr=attr)
            elif "debounce_period_us" in a:
                attr = gpio_v2_line_attribute()
                attr.id = GPIO_V2_LINE_ATTR_ID_DEBOUNCE
                attr.u.debounce_period_us = a["debounce_period_us"]
                yield gpio_v2_line_config_attribute(mask=mask, attr=attr)
            else:
                continue

    def _line_info(self, li):
        return {
            "name": li.name.decode(errors="replace"),
            "consumer": li.consumer.decode(errors="replace"),
            "offset": li.offset,
            "flags": list(self._iter_flags(li.flags)),
            "attrs": list(self._iter_attrs(li.num_attrs, li.attrs)),
        }

    def info(self) -> Dict:
        """
        Get all available info on this chip and the lines it manages.
        """
        chip_info = self._get_chip_info()

        data = {
            "name": chip_info.name.decode(errors="replace"),
            "label": chip_info.name.decode(errors="replace"),
            "lines": [self._line_info(li) for li in self._iter_lines(chip_info.lines)],
        }

        return data

    def request(
        self,
        offsets: List[int],
        consumer: Optional[str] = None,
        flags: Optional[List[str]] = None,
        attrs: Optional[List[Dict]] = None,
    ) -> Lines:
        """
        Configure a set of GPIO lines with the given settings.
        """
        assert len(offsets) <= GPIO_V2_LINES_MAX, "too many lines"

        for i in offsets:
            assert 0 <= i <= U32_MAX, f"offset out of range: {i}"
            assert offsets.count(i) == 1, f"duplicate offset: {i}"

        fd = self._get_line(
            offsets,
            consumer=consumer,
            flags=self._build_flags(flags),
            attrs=list(self._build_attrs(attrs or [])),
        )

        return Lines(fd, offsets)

    def watch(self, offset: int):
        """
        Start watching for line_info_changed events on this GPIO chip.
        """
        assert 0 <= offset <= U32_MAX
        line_info = gpio_v2_line_info(offset=offset)
        ioctl(self._file.fileno(), GPIO_V2_GET_LINEINFO_WATCH_IOCTL, line_info)

    def unwatch(self, offset: int):
        """
        Stop watching for line_info_changed events on this GPIO chip.
        """
        assert 0 <= offset <= U32_MAX
        c_offset = c_uint32(offset)
        ioctl(
            self._file.fileno(),
            GPIO_GET_LINEINFO_UNWATCH_IOCTL,
            c_offset,
        )

    def wait(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        Wait for the next line_info_changed event on this GPIO chip.
        """
        if not self._epoll:
            self._epoll = select.epoll()
            fd = self._file.fileno()
            self._epoll.register(fd, select.EPOLLIN)

        fds = self._epoll.poll(timeout=timeout)

        if not fds:
            return None

        assert not fds[0][1] & select.EPOLLERR, "EPOLLERR"
        event = gpio_v2_line_info_changed()
        ret = self._file.readinto(event)
        assert ret == sizeof(gpio_v2_line_info_changed)
        et = event.event_type

        return {
            "info": self._line_info(event.info),
            "timestamp_ns": event.timestamp_ns,
            "event_type": "LINE_REQUESTED"
            if et == GPIO_V2_LINE_CHANGED_REQUESTED
            else "LINE_RELEASED"
            if et == GPIO_V2_LINE_CHANGED_RELEASED
            else "CONFIG_CHANGED"
            if et == GPIO_V2_LINE_CHANGED_CONFIG
            else "???",
        }


def chip(path: str) -> Chip:
    """
    Public constructor.
    """
    return Chip(path)

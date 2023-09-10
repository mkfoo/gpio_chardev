from ctypes import alignment, sizeof

import gpio


def test_alignof_on_current_platform(c_data):
    def assert_align(ident):
        assert alignment(getattr(gpio, ident)) == c_data[ident]["alignof"]

    assert_align("gpiochip_info")
    assert_align("gpio_v2_line_info")
    assert_align("gpio_v2_line_request")
    assert_align("gpio_v2_line_config")
    assert_align("gpio_v2_line_values")
    assert_align("gpio_v2_line_attribute")
    assert_align("gpio_v2_line_config_attribute")
    assert_align("gpio_v2_line_info_changed")
    assert_align("gpio_v2_line_event")


def test_sizeof_on_current_platform(c_data):
    def assert_size(ident):
        assert sizeof(getattr(gpio, ident)) == c_data[ident]["sizeof"]

    assert_size("gpiochip_info")
    assert_size("gpio_v2_line_info")
    assert_size("gpio_v2_line_request")
    assert_size("gpio_v2_line_config")
    assert_size("gpio_v2_line_values")
    assert_size("gpio_v2_line_attribute")
    assert_size("gpio_v2_line_config_attribute")
    assert_size("gpio_v2_line_info_changed")
    assert_size("gpio_v2_line_event")


def test_ioctls_on_current_platform(c_data):
    def assert_ioctl(ident):
        assert getattr(gpio, ident) == c_data[ident]

    assert_ioctl("GPIO_GET_CHIPINFO_IOCTL")
    assert_ioctl("GPIO_V2_GET_LINEINFO_IOCTL")
    assert_ioctl("GPIO_V2_GET_LINEINFO_WATCH_IOCTL")
    assert_ioctl("GPIO_V2_GET_LINE_IOCTL")
    assert_ioctl("GPIO_GET_LINEINFO_UNWATCH_IOCTL")
    assert_ioctl("GPIO_V2_LINE_SET_CONFIG_IOCTL")
    assert_ioctl("GPIO_V2_LINE_GET_VALUES_IOCTL")
    assert_ioctl("GPIO_V2_LINE_SET_VALUES_IOCTL")

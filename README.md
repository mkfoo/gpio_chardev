# gpio_chardev
Yet another pure-Python GPIO library.

For setting GPIO values, this library exposes a dict-based convenience API as well as a lower-level bitmask API with less overhead.

```python
"""Blink two leds in turn, using values dict."""
import time
import gpio

LED_1 = 23
LED_2 = 24

chip = gpio.chip("/dev/gpiochip0")
line = chip.request([LED_1, LED_2], flags=["OUTPUT"])
values = {LED_1: False, LED_2: True}

try:
    while True:
        line.set(values)
        values[LED_1] = not values[LED_1]
        values[LED_2] = not values[LED_2]
        time.sleep(1)
except KeyboardInterrupt:
    line.set({LED_1: False, LED_2: False})
```

```python
"""Blink two leds in turn, using bitmasks."""
import time
import gpio

chip = gpio.chip("/dev/gpiochip0")
line = chip.request([23, 24], flags=["OUTPUT"])
bits = 0b10

try:
    while True:
        line.set_bits(bits, 0b11)
        bits ^= 0b11
        time.sleep(1)
except KeyboardInterrupt:
    line.set_bits(0b00, 0b11)
```

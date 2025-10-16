import sys
import types
import unittest
from copy import deepcopy


class PinStub:
    def __init__(self):
        self.value = 0
        self.writes = []

    def read_digital(self):
        return self.value

    def write_digital(self, value):
        self.value = value
        self.writes.append(value)


class ButtonStub:
    def __init__(self):
        self.pressed = False

    def is_pressed(self):
        return self.pressed


class DisplayStub:
    def __init__(self):
        self.show_calls = []
        self.cleared = 0
        self.pixels = {}

    def show(self, value):
        self.show_calls.append(value)

    def clear(self):
        self.cleared += 1

    def set_pixel(self, x, y, value):
        self.pixels[(x, y)] = value

    def reset(self):
        self.show_calls.clear()
        self.cleared = 0
        self.pixels.clear()


class SleepStub:
    def __init__(self):
        self.calls = []

    def __call__(self, duration):
        self.calls.append(duration)

    def reset(self):
        self.calls.clear()


class RadioStub:
    def __init__(self):
        self.reset()

    def reset(self):
        self.sent_messages = []
        self.queue = []
        self.config_calls = []
        self.on_calls = 0

    def config(self, **kwargs):
        self.config_calls.append(kwargs)

    def on(self):
        self.on_calls += 1

    def send(self, message):
        self.sent_messages.append(message)

    def receive(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def enqueue(self, *messages):
        self.queue.extend(messages)


# Install stub modules before importing the code under test
microbit_module = types.ModuleType("microbit")
microbit_module.pin0 = PinStub()
microbit_module.pin1 = PinStub()
microbit_module.button_a = ButtonStub()
microbit_module.display = DisplayStub()
microbit_sleep = SleepStub()
microbit_module.sleep = microbit_sleep
sys.modules["microbit"] = microbit_module

radio_stub = RadioStub()

radio_module = types.ModuleType("radio")
radio_module.stub = radio_stub
radio_module.config = radio_stub.config
radio_module.on = radio_stub.on
radio_module.send = radio_stub.send
radio_module.receive = radio_stub.receive
sys.modules["radio"] = radio_module

import multidisplay.multidisplay as multidisplay


def original_animate(sprite, sprite_width, sprite_height, sprite_y, total_width, initial_x, buffer_):
    sprite_x = initial_x + 1
    if sprite_x > total_width:
        sprite_x = 0 - sprite_width

    start_col = 0
    end_col = sprite_width

    if sprite_x < 0:
        start_col = -sprite_x

    if sprite_x + sprite_width > total_width:
        end_col = total_width - sprite_x

    for row in range(sprite_height):
        for col in range(start_col, end_col):
            buffer_[row + sprite_y][col + sprite_x] = sprite[row][col]

    return sprite_x


def original_master_buffer(animation_buffer, screens, display_size):
    master_buffer = [[0] * display_size for _ in range(display_size)]
    messages = []

    for screen in range(screens):
        if screen == 0:
            for row in range(display_size):
                for col in range(display_size):
                    master_buffer[row][col] = animation_buffer[row][col]
        else:
            screen_data = ""
            for row in range(display_size):
                for col in range(screen * display_size, (screen * display_size) + display_size):
                    screen_data += str(animation_buffer[row][col])
            messages.append(str(screen) + screen_data)

    return master_buffer, messages


def original_decode(buffer_data, display_size):
    decoded = [[0] * display_size for _ in range(display_size)]
    for row in range(display_size):
        for col in range(display_size):
            row_start = display_size * row
            decoded[row][col] = int(buffer_data[row_start + col : row_start + col + 1])
    return decoded


class MultiDisplayLogicTest(unittest.TestCase):
    def setUp(self):
        radio_stub.reset()
        microbit_module.pin0.value = 0
        microbit_module.pin0.writes.clear()
        microbit_module.pin1.value = 0
        microbit_module.pin1.writes.clear()
        microbit_module.button_a.pressed = False
        microbit_module.display.reset()
        microbit_sleep.reset()

        multidisplay.total_width = multidisplay.DISPLAY_SIZE
        multidisplay.animation_buffer = [
            [0] * multidisplay.DISPLAY_SIZE for _ in range(multidisplay.DISPLAY_SIZE)
        ]
        multidisplay.local_buffer = [
            [0] * multidisplay.DISPLAY_SIZE for _ in range(multidisplay.DISPLAY_SIZE)
        ]
        multidisplay.number_of_screens = 1
        multidisplay.sprite_x = 2
        multidisplay.screen_number = -1

    def test_animate_matches_original_logic(self):
        total_width = multidisplay.DISPLAY_SIZE * 3
        multidisplay.total_width = total_width
        test_positions = [-2, -1, 0, total_width - 1, total_width]

        for initial_x in test_positions:
            multidisplay.sprite_x = initial_x
            multidisplay.animation_buffer = [
                [0] * total_width for _ in range(multidisplay.DISPLAY_SIZE)
            ]
            expected_buffer = deepcopy(multidisplay.animation_buffer)
            expected_x = original_animate(
                multidisplay.sprite,
                multidisplay.sprite_width,
                multidisplay.sprite_height,
                multidisplay.sprite_y,
                total_width,
                initial_x,
                expected_buffer,
            )

            multidisplay.animate()

            self.assertEqual(multidisplay.sprite_x, expected_x)
            self.assertEqual(multidisplay.animation_buffer, expected_buffer)

    def test_reset_buffer_clears_all_entries(self):
        multidisplay.animation_buffer = [
            [row * 10 + col for col in range(multidisplay.DISPLAY_SIZE * 2)]
            for row in range(multidisplay.DISPLAY_SIZE)
        ]

        multidisplay.reset_buffer()

        for row in multidisplay.animation_buffer:
            self.assertTrue(all(value == 0 for value in row))

    def test_distribute_buffers_matches_original_logic(self):
        multidisplay.number_of_screens = 3
        multidisplay.total_width = multidisplay.DISPLAY_SIZE * multidisplay.number_of_screens
        multidisplay.animation_buffer = [
            [col + row * multidisplay.total_width for col in range(multidisplay.total_width)]
            for row in range(multidisplay.DISPLAY_SIZE)
        ]

        expected_local, expected_messages = original_master_buffer(
            multidisplay.animation_buffer,
            multidisplay.number_of_screens,
            multidisplay.DISPLAY_SIZE,
        )

        multidisplay.distribute_screen_buffers()

        self.assertEqual(multidisplay.local_buffer, expected_local)
        self.assertEqual(radio_stub.sent_messages, expected_messages)

    def test_load_local_buffer_decodes_identically(self):
        payload = "".join(
            str((row * multidisplay.DISPLAY_SIZE + col) % 10)
            for row in range(multidisplay.DISPLAY_SIZE)
            for col in range(multidisplay.DISPLAY_SIZE)
        )

        multidisplay.load_local_buffer(payload)

        expected = original_decode(payload, multidisplay.DISPLAY_SIZE)
        self.assertEqual(multidisplay.local_buffer, expected)

    def test_wait_for_buffer_data_uses_same_selection_logic(self):
        multidisplay.screen_number = 2
        valid_payload = "".join(
            str((row * multidisplay.DISPLAY_SIZE + col) % 10)
            for row in range(multidisplay.DISPLAY_SIZE)
            for col in range(multidisplay.DISPLAY_SIZE)
        )
        radio_stub.enqueue("1" + valid_payload, "2" + valid_payload)

        multidisplay.wait_for_buffer_data()

        expected = original_decode(valid_payload, multidisplay.DISPLAY_SIZE)
        self.assertEqual(multidisplay.local_buffer, expected)

    def test_wait_for_render_only_renders_on_trigger(self):
        multidisplay.local_buffer = [
            [row * multidisplay.DISPLAY_SIZE + col for col in range(multidisplay.DISPLAY_SIZE)]
            for row in range(multidisplay.DISPLAY_SIZE)
        ]
        radio_stub.enqueue("IGNORED", multidisplay.RENDER_MSG)

        multidisplay.wait_for_render()

        expected_pixels = {
            (col, row): multidisplay.local_buffer[row][col]
            for row in range(multidisplay.DISPLAY_SIZE)
            for col in range(multidisplay.DISPLAY_SIZE)
        }
        self.assertEqual(microbit_module.display.pixels, expected_pixels)

    def test_clear_radio_buffer_drains_messages(self):
        radio_stub.enqueue("A", "B", "C")

        multidisplay._clear_radio_buffer()

        self.assertFalse(radio_stub.queue)

    def test_request_screen_number_matches_original_flow(self):
        radio_stub.enqueue(None, f"{multidisplay.ASSIGN_NUMBER_MSG}3")

        assigned = multidisplay._request_screen_number()

        self.assertEqual(assigned, 3)
        self.assertIn(multidisplay.REQUEST_NUMBER_MSG, radio_stub.sent_messages)


if __name__ == "__main__":
    unittest.main()

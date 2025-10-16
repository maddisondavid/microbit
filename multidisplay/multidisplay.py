from microbit import *
import radio

#
# Performs an animation over several connected Micro:bit screens that self organize

RADIO_GROUP = 1
REQUEST_NUMBER_MSG = "REQUEST"
ASSIGN_NUMBER_MSG = "ASSIGN"
RENDER_MSG = "RENDER"

START_SETUP_PIN = pin0
NOTIFY_NEXT_PIN = pin1

# Screen number will be -1 until assigned
MASTER_SCREEN_NUMBER = 0
screen_number = -1

DISPLAY_SIZE = 5
FRAME_TRIGGER_DELAY_MS = 5

total_width = DISPLAY_SIZE
animation_buffer = []
local_buffer = [[0] * DISPLAY_SIZE for _ in range(DISPLAY_SIZE)]
number_of_screens = 1

# Sprite Information
sprite = [
    [3, 5, 9, 0],
    [5, 7, 9, 9],
    [3, 5, 9, 0],
]
sprite_height = len(sprite)
sprite_width = len(sprite[0])
sprite_x = 2
sprite_y = 1


def initialize():
    """Initialise the system by waiting to see if we're a Master or Slave Node"""
    global screen_number

    NOTIFY_NEXT_PIN.write_digital(0)

    radio.config(group=RADIO_GROUP)
    radio.on()

    display.show("--")
    while True:
        if button_a.is_pressed():
            master_setup()
            break

        if START_SETUP_PIN.read_digital() == 1:
            _clear_radio_buffer()
            screen_number = _request_screen_number()
            NOTIFY_NEXT_PIN.write_digital(1)
            break

        sleep(100)

    display.show(screen_number)
    sleep(1000)
    display.clear()


def _clear_radio_buffer():
    """Discard any pending radio messages to avoid stale data during setup."""
    while radio.receive() is not None:
        pass


def _request_screen_number():
    """Request a screen number from the master and return it once assigned."""
    radio.send(REQUEST_NUMBER_MSG)

    number_assign = None
    while number_assign is None:
        number_assign = radio.receive()

    return int(number_assign[len(ASSIGN_NUMBER_MSG) :])


def master_setup():
    """Main loop for Master node setup that waits assigning numbers to screens when requested"""
    global screen_number, number_of_screens

    screen_number = MASTER_SCREEN_NUMBER
    display.show(screen_number)

    NOTIFY_NEXT_PIN.write_digital(1)

    next_screen_number = 1

    while START_SETUP_PIN.read_digital() != 1:
        request = radio.receive()
        if request == REQUEST_NUMBER_MSG:
            radio.send(ASSIGN_NUMBER_MSG + str(next_screen_number))
            next_screen_number += 1
        sleep(100)

    number_of_screens = next_screen_number


def create_animation_buffer():
    """Creates the main animation buffer based on the number of screens"""
    global animation_buffer, total_width

    total_width = DISPLAY_SIZE * number_of_screens
    animation_buffer = [[0] * total_width for _ in range(DISPLAY_SIZE)]


def animate():
    """Perform animation into the animation buffer"""
    global sprite_x

    sprite_x += 1

    if sprite_x > total_width:
        sprite_x = 0 - sprite_width

    visible_start_col = 0
    visible_end_col = sprite_width

    if sprite_x < 0:
        visible_start_col = -sprite_x

    if sprite_x + sprite_width > total_width:
        visible_end_col = total_width - sprite_x

    for row in range(sprite_height):
        for col in range(visible_start_col, visible_end_col):
            animation_buffer[row + sprite_y][col + sprite_x] = sprite[row][col]


def reset_buffer():
    """Clear the whole animation buffer"""
    for row in animation_buffer:
        for col in range(len(row)):
            row[col] = 0


def distribute_screen_buffers():
    """Break up the animation buffer into screen buffers and send to slave Micro:bits"""

    for screen in range(number_of_screens):
        if screen == 0:
            for row in range(DISPLAY_SIZE):
                local_buffer[row][:] = animation_buffer[row][:DISPLAY_SIZE]
        else:
            screen_data = "".join(
                str(animation_buffer[row][col])
                for row in range(DISPLAY_SIZE)
                for col in range(screen * DISPLAY_SIZE, (screen * DISPLAY_SIZE) + DISPLAY_SIZE)
            )
            radio.send(str(screen) + screen_data)


def wait_for_buffer_data():
    """Called by a slave node when it needs to wait to receive the next frame information from the master"""
    while True:
        buffer_data = radio.receive()
        if buffer_data is None:
            continue

        buffer_data_str = str(buffer_data)
        if buffer_data_str.startswith(str(screen_number)):
            load_local_buffer(buffer_data_str[1:])
            return


def load_local_buffer(buffer_data):
    """Decode the new frame information into the local buffer"""
    for row in range(DISPLAY_SIZE):
        row_start = DISPLAY_SIZE * row
        for col in range(DISPLAY_SIZE):
            local_buffer[row][col] = int(buffer_data[row_start + col])


def wait_for_render():
    """Called by slave when it needs to wait to receive the render tick"""
    while True:
        msg = radio.receive()
        if msg == RENDER_MSG:
            render_local()
            return


def trigger_render():
    """Send out the command to render"""
    radio.send(RENDER_MSG)


def render_local():
    """Render the local buffer data onto the screen"""
    for row in range(DISPLAY_SIZE):
        for col in range(DISPLAY_SIZE):
            display.set_pixel(col, row, local_buffer[row][col])


def main():
    initialize()
    create_animation_buffer()

    while True:
        if screen_number == MASTER_SCREEN_NUMBER:
            reset_buffer()
            animate()

            distribute_screen_buffers()
            # Small sleep before render is triggered to give Slave Micro:bits enough time to decode screen data
            sleep(FRAME_TRIGGER_DELAY_MS)

            trigger_render()
            render_local()
        else:
            wait_for_buffer_data()
            wait_for_render()
            render_local()


if __name__ == "__main__":
    main()

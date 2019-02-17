from microbit import *
import radio

#
# Perform an animation across multiple Micro:bit displays... in sync
#
#  Main Loop:
#     - Animate into Frame Buffer
#     - Chop FrameBuffer up into FrameSections and distribute
#     - Render FrameSection
#

RENDER_MSG = "RENDER"
NEED_NUMBER_MSG = "NEEDSCREEN"
ASSIGN_NUMBER_MSG = "ASSIGN"

screen_number = -1
animation_buffer = []
localBuffer = [[0] * 5 for i in range(5)]

spriteX = 2
spriteY = 1
sprite_reversed = False
ballDirection = -1

number_of_screens = 3

max_cols = 5

sprite_width = 4
sprite_height = 3
sprite = [[3,5,9,0],
          [5,7,9,9],
          [3,5,9,0]]

def initialize():
    global is_master, screen_number

    pin0.write_digital(0)
    pin1.write_digital(0)

    radio.config(group=1)
    radio.on()

    # wait here to be assigned a role
    display.show("--")
    while True:
        if button_a.is_pressed():
            screen_number = 0

            master_setup()
            break

        if pin0.read_digital() == 1:
            # Clear radio buffer since other comms traffic will been received
            while radio.receive() is not None:
                None

            radio.send(NEED_NUMBER_MSG)

            # Wait here for response
            number_assign = None
            while number_assign is None:
                number_assign = radio.receive()

            # Extract screen number
            print("MSG="+number_assign)
            screen_number = int(number_assign[len(ASSIGN_NUMBER_MSG):])
            display.show(screen_number)

            # Trigger next Node
            pin1.write_digital(1)

            break

        sleep(100)

    display.show(screen_number)
    sleep(500)

    display.clear()

def master_setup():
    global number_of_screens

    display.show("0")

    # Trigger chain reaction
    pin1.write_digital(1)

    next_screen = 1

    print("Master Setup Start")
    all_assigned = False
    while not all_assigned:
        screen_setup_msg = radio.receive()

        if screen_setup_msg is not None:
            if screen_setup_msg == NEED_NUMBER_MSG:
                radio.send(ASSIGN_NUMBER_MSG + str(next_screen))
                next_screen += 1

        # We're finished if it loops around
        all_assigned = pin0.read_digital() == 1

        sleep(100)

    number_of_screens = next_screen
    print("Master Setup Finished")


def create_animation_buffer():
    global number_of_screens, animation_buffer, max_cols

    max_cols = 5 * number_of_screens
    animation_buffer = [[0] * max_cols for i in range(5)]


def animate():
    """Perform animation into the animation buffer"""
    global spriteX, spriteY, sprite_width, sprite_height, sprite_reversed, ballDirection

    # Move Sprite Along
    spriteX += 1

    if spriteX > max_cols:
        spriteX = 0 - sprite_width

    start_col = 0
    end_col = sprite_width

    # If the sprite is before the start of the animation buffer only render the bit showing
    if spriteX < 0:
        start_col = spriteX * -1

    # If the sprite is at the end of the animation buffer, render just the part showing
    if spriteX + sprite_width > max_cols:
        end_col = max_cols - spriteX

    # Render sprite into animation buffer
    for row in range(0,sprite_height):
        for col in range(start_col, end_col):
            animation_buffer[row + spriteY][col+spriteX] = sprite[row][col]


def reset_buffer():
    """Clear the whole animation buffer"""
    for row in range (0, 5):
        for col in range(0, len(animation_buffer[row])):
            animation_buffer[row][col] = 0


def distribute_screen_buffers():
    """Break up the animation buffer into screen buffers and send to Microbits"""
    global number_of_screens, localBuffer

    for screen in range(0, number_of_screens):
        if screen == 0:
            for row in range(0, 5):
                for col in range(0, 5):
                    localBuffer[row][col] = animation_buffer[row][col]
        else:
            screen_data = ""
            for row in range(0, 5):
                for col in range(screen*5, (screen*5)+5):
                    screen_data += str(animation_buffer[row][col])

            radio.send(str(screen)+screen_data)


def trigger_render():
    """Send out the command to render"""
    radio.send(RENDER_MSG)


def renderLocal():
    """Render the local buffer data onto the screen"""
    for row in range(0, 5):
        for col in range(0, 5):
            display.set_pixel(col, row, localBuffer[row][col])


def wait_for_buffer_data():
    """Wait for frame buffer data to be sent by master"""
    data_loaded = False
    while not data_loaded:
        buffer_data = None
        while buffer_data is None:
            buffer_data = radio.receive()

        buffer_data_str = str(buffer_data)

        if buffer_data_str.startswith(str(screen_number)):
            load_local_buffer(buffer_data_str[1:])
            data_loaded = True


def load_local_buffer(buffer_data):
    """Load received buffer data into our local buffer"""
    for row in range(0, 5):
        for col in range(0, 5):
            row_start = 5 * row

            localBuffer[row][col] = int(buffer_data[row_start+col:row_start+col+1])


def wait_for_render():
    """Wait for render command to be sent by master """
    render_received = False
    while not render_received:
        msg = None
        while msg is None:
            msg = radio.receive()

        if msg == RENDER_MSG:
            renderLocal()
            render_received = True


initialize()
create_animation_buffer()
print("Start Main Loop")
while True:
    if screen_number == 0:
        reset_buffer()
        animate()
        distribute_screen_buffers()
        sleep(5)
        trigger_render()

        renderLocal()
    else:
        wait_for_buffer_data()
        wait_for_render()
        renderLocal()


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

screen_number = -1
animation_buffer = []
localBuffer = [[0] * 5 for i in range(5)]

ballX = 2
ballDirection = -1

is_master = False
number_of_screens = 2

max_cols = 5*number_of_screens


def initialize():
    global is_master, screen_number

    # wait here to be assigned a role
    display.show("--")
    while screen_number == -1:
        if button_a.is_pressed():
            is_master = True
            screen_number = 0

        if button_b.is_pressed():
            screen_number = 1

        sleep(100)

    display.show(screen_number)
    sleep(500)

    display.clear()
    radio.config(group=1)
    radio.on()



def create_animation_buffer():
    global number_of_screens, animation_buffer

    animation_buffer = [[0] * max_cols for i in range(5)]


def animate():
    global ballX, ballDirection

    if ballX == 0:
        ballDirection = 1

    if ballX == max_cols-1:
        ballDirection = -1

    ballX += ballDirection
    animation_buffer[2][ballX] = 9


def reset_buffer():
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


def load_local_buffer(buffer_data):
    """Load"""
    for row in range(0, 5):
        for col in range(0, 5):
            row_start = 5 * row

            localBuffer[row][col] = int(buffer_data[row_start+col:row_start+col+1])


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
    buffer_data = None
    data_loaded = False
    while not data_loaded:
        while buffer_data is None:
            buffer_data = radio.receive()

        buffer_data_str = str(buffer_data)

        if buffer_data_str.startswith(str(screen_number)):
            load_local_buffer(buffer_data_str[1:])
            data_loaded = True


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


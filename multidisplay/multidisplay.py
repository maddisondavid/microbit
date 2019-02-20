from microbit import *
import radio

#
# Performs an animation over several connected Micro:bit screens that self organize

REQUEST_NUMBER_MSG = "REQUEST"
ASSIGN_NUMBER_MSG = "ASSIGN"
RENDER_MSG = "RENDER"

START_SETUP_PIN = pin0
NOTIFY_NEXT_PIN = pin1

# Screen number will be -1 until assigned
MASTER_SCREEN_NUMBER = 0
screen_number = -1

total_width = 5
animation_buffer = []
localBuffer = [[0] * 5 for i in range(5)]
number_of_screens = 1

# Sprite Information
spriteX = 2
spriteY = 1
sprite_width = 4
sprite_height = 3
sprite = [[3,5,9,0],
          [5,7,9,9],
          [3,5,9,0]]

def initialize():
    """Initialise the system by waiting to see if we're a Master or Slave Node"""
    global screen_number

    # Make sure our 'notification' pin is 0
    NOTIFY_NEXT_PIN.write_digital(0)

    radio.config(group=1)
    radio.on()

    # wait here to be assigned a role
    display.show("--")
    while True:
        if button_a.is_pressed():
            master_setup()
            break

        if pin0.read_digital() == 1:
            # Other bits traffic would have been received while waiting, so clear the buffer
            while radio.receive() is not None:
                None

            # Ask the Master Bit for a number
            radio.send(REQUEST_NUMBER_MSG)

            # Wait here for response
            number_assign = None
            while number_assign is None:
                number_assign = radio.receive()

            # Extract screen number from message
            screen_number = int(number_assign[len(ASSIGN_NUMBER_MSG):])

            # Notify next bit in line
            NOTIFY_NEXT_PIN.write_digital(1)
            break

        sleep(100)

    display.show(screen_number)
    sleep(1000)

    display.clear()


def master_setup():
    """Main loop for Master node setup that waits assigning numbers to screens when requested"""
    global screen_number, number_of_screens

    screen_number = MASTER_SCREEN_NUMBER
    display.show(screen_number)

    # Notify next bit
    NOTIFY_NEXT_PIN.write_digital(1)

    next_screen = 1

    # Keep looping until we get a SETUP request, which means we've gone through all the screens
    while not START_SETUP_PIN.read_digital() == 1:
        screen_setup_msg = radio.receive()

        if screen_setup_msg is not None:
            # If this is a request for a number, send one back
            if screen_setup_msg == REQUEST_NUMBER_MSG:
                radio.send(ASSIGN_NUMBER_MSG + str(next_screen))
                next_screen += 1

        sleep(100)

    number_of_screens = next_screen


def create_animation_buffer():
    """Creates the main animation buffer based on the number of screens"""
    global number_of_screens, animation_buffer, total_width

    total_width = 5 * number_of_screens
    animation_buffer = [[0] * total_width for i in range(5)]


def animate():
    """Perform animation into the animation buffer"""
    global spriteX, spriteY, sprite_width, sprite_height

    # Move Sprite Along
    spriteX += 1

    if spriteX > total_width:
        spriteX = 0 - sprite_width

    start_col = 0
    end_col = sprite_width

    # If the sprite is before the start of the animation buffer only render the bit showing
    if spriteX < 0:
        start_col = spriteX * -1

    # If the sprite is at the end of the animation buffer, render just the part showing
    if spriteX + sprite_width > total_width:
        end_col = total_width - spriteX

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
    """Break up the animation buffer into screen buffers and send to slave Micro:bits"""
    global number_of_screens, localBuffer

    for screen in range(0, number_of_screens):
        # If this is for ourselves (the master) then just copy directly to local buffer
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


def wait_for_buffer_data():
    """Called by a slave node when it needs to wait to receive the next frame information from the master"""
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
    """Decode the new frame information into the local buffer"""
    for row in range(0, 5):
        for col in range(0, 5):
            row_start = 5 * row

            localBuffer[row][col] = int(buffer_data[row_start+col:row_start+col+1])


def wait_for_render():
    """Called by slave when it needs to wait to receive the render tick"""
    render_received = False
    while not render_received:
        msg = None
        while msg is None:
            msg = radio.receive()

        if msg == RENDER_MSG:
            render_local()
            render_received = True


def trigger_render():
    """Send out the command to render"""
    radio.send(RENDER_MSG)


def render_local():
    """Render the local buffer data onto the screen"""
    for row in range(0, 5):
        for col in range(0, 5):
            display.set_pixel(col, row, localBuffer[row][col])


initialize()
create_animation_buffer()

while True:
    if screen_number == MASTER_SCREEN_NUMBER:
        reset_buffer()
        animate()

        distribute_screen_buffers()
        # Small sleep before render is triggered to give Slave Micro:bits enough time to decode screen data
        sleep(5)

        trigger_render()
        render_local()
    else:
        wait_for_buffer_data()
        wait_for_render()
        render_local()

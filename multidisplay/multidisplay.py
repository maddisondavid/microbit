from microbit import *

#
# Perform an animation across multiple Micro:bit displays... in sync
#
#  Main Loop:
#     - Animate into Frame Buffer
#     - Chop FrameBuffer up into FrameSections and distribute
#     - Render FrameSection
#

animation_buffer = []
localBuffer = [[0] * 5 for i in range(5)]

ballX = 2
ballDirection = -1

is_master = True
number_of_screens = 2

max_cols = 5*number_of_screens

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


def distribute():
    global number_of_screens, localBuffer

    for screen in range(0, number_of_screens):
        if screen == 0:
            for row in range(0, 5):
                for col in range(0, 5):
                    localBuffer[row][col] = animation_buffer[row][col]
        else:
            # Pack Data
            screen_data = ""
            for row in range(0, 5):
                for col in range(screen*5, (screen*5)+5):
                    screen_data += str(animation_buffer[row][col])

def render():
    for row in range(0, 5):
        for col in range(0, 5):
            display.set_pixel(col, row, localBuffer[row][col])

create_animation_buffer()

while True:
    # Send out RENDER! message
    render()

    if is_master:
        reset_buffer()
        animate()
        distribute()

    sleep(10)


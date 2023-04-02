import time
import random
import board
import neopixel
import digitalio
import busio
import adafruit_dotstar
import supervisor
import math

# Command header for uart interface
HEADER = "GB23"

# Periods for animations
SUNRISE_PERIOD_MS = 3900
MOONLIGHT_PERIOD_MS = 50

# Gamma value for correction
GAMMA = 1.8

# Max values for sunrise animation
blueMax = 45
greenMax = 130
sunmax = 230

# Initialize onboard LED
led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

# Initialize UART
uart = busio.UART(board.TX, board.RX, baudrate=9600)

# NeoPixel control pin
pixel_pin = board.D5

# The number of NeoPixels
num_pixels = 40

# Initial brightness
pixel_brightness = 1

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

# Initialize neopixels
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=pixel_brightness, auto_write=False,
                           pixel_order=ORDER)
pixels.fill((0,0,0))
pixels.show()

# A colour cycling function for the "rainbow" mode
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b) if ORDER == neopixel.RGB or ORDER == neopixel.GRB else (r, g, b, 0)

# Define a function to apply the gamma filter to a color tuple
def gamma_correct(color):
    return tuple(int(pow(c / 255.0, GAMMA) * 255) for c in color)

# The a single "frame" of the rainbow mode. Meant to be called periodically to produce an animation
def rainbow_cycle(frame):
    for i in range(num_pixels):
        pixel_index = (i * 256 // num_pixels) + frame
        pixels[i] = wheel(pixel_index & 255)
    pixels.show()
    frame = frame + 1
    if(frame > 255):
        frame = 0
    return frame

#global data for the moonlight mode
pixel_colour = [[130,0,255]]*20
pixel_index = [-1]*20
pixel_position = [0]*20
num_flashing = 20

# A single frame of the moonlight mode. Meant to be called periodically to produce an animation.
# For this one the frame matters less than the other modes. The global data above stores LED values, etc.
def moonlight_shimmer(frame):
    global pixel_colour
    global pixel_index
    global pixel_position
    global num_flashing

    # Generate random number (1 to 200)
    num = random.uniform(0,2)
    num = int(num*100)

    # If number is mod10, add a new yellow shimmering pixel (random position)
    if(num%10 == 0):
        num = int(num/10)
        #print(num)
        if(pixel_index[num] == -1):
            pixel_index[num] = 0
            pixel_position[num] = int(random.uniform(0,40))

    #Fill LEDs with purple on frame 0
    if(frame == 0):
        pixels.fill((130, 0, 255))

    # Advance shimmer animation for all yellow LEDs in list
    for i in range(num_flashing):
        if(pixel_index[i] == -1):
            continue
        elif(pixel_index[i] == 0):
            pixel_colour[i] = [130, 0, 255]
        elif(pixel_index[i] == 100):
            pixel_colour[i] = [130, 0, 255]
        elif(pixel_index[i] < 50):
            pixel_colour[i][0] += 2.4
            pixel_colour[i][1] += 3.0
            pixel_colour[i][2] -= 4.0
        else:
            pixel_colour[i][0] -= 2.4
            pixel_colour[i][1] -= 2.8
            pixel_colour[i][2] += 3.8

        pixel_index[i] += 1
        if(pixel_index[i] > 100):
            pixel_index[i] = -1 # Animation is complete, disable shimmering on this led

        # Round and gamma correct generated pixel. Store in neopixel frame
        rounded_pix = (int(round(pixel_colour[i][0],0)),int(round(pixel_colour[i][1],0)) , int(round(pixel_colour[i][2],0)))
        pixels[pixel_position[i]] = gamma_correct(rounded_pix)

    # Show pixels
    pixels.show()

    # Increment and return frame
    frame += 1;
    if(frame > 100):
        frame = 0
    return frame

# Fill the ring with a solid colour
def fill_colour(r,g,b):
    pixels.fill((r, g, b))
    pixels.show()

#def fill_red():
#    pixels.fill((255,0,0))
#    pixels.show()

# One frame of the sunrise animation. Meant to be called periodically with a relatively slow period
def sunrise(frame):
    # Fill all pixels with the next colour
    pixels.fill((r_sun(frame),g_sun(frame),b_sun(frame)))
    pixels.show()

    # Advance frame until max reached
    if(frame < sunmax):
        frame = frame + 1
    return frame

# Red value helper function for sunrise animation
def r_sun(index):
    if(index < 85):
        value = index*3
    else:
        value = 255
    return value

# green value helper function for sunrise animation
def g_sun(index):
    value = index-20
    if(value < 0):
        value = 0
    elif(value > greenMax):
        value = greenMax
    return value

# Blue value helper function for sunrise animation
def b_sun(index):
    value = index - 170;
    if(value < 0):
        value = 0
    elif(value > blueMax):
        value = blueMax
    return value

# Permanent setting for on-board LED
led.brightness = 0.5
led[0] = (25, 0, 0)

# initialize variables
mode = 0
curr_frame = 0
frame_time = 0

# Starting brightness
pixels.brightness = 1

# Infinite loop
while True:

    # Check for a new command in the buffer
    if(uart.in_waiting > 0):
        command = uart.readline()
        command_string = ''.join([chr(b) for b in command])
        print(command_string, end="")
        parsed_command = command_string.split(' ')
        # Check command for a valid header
        if(parsed_command[0] == HEADER):
            # Parse and execute command
            if(parsed_command[1] == "rainbow"): # Enable rainbow animation (no argument)
                mode = 1
                curr_frame = 0
            elif(parsed_command[1] == "off"): # Turn off all animations (no argument
                mode = 0
                fill_colour(0,0,0)
            elif(parsed_command[1] == "colour"): # Set ring to a single colour (3 x uint8 arguments for R,G,B values)
                mode = 0
                fill_colour(int(parsed_command[2]), int(parsed_command[3]), int(parsed_command[4]))
            elif(parsed_command[1] == "sunrise"): # Enable sunrise animation (no argument)
                mode = 2
                curr_frame = 0
                frame_time = 0
                pixels.brightness = 1
            elif(parsed_command[1] == "brightness"): # Change brightness of the display (brightness float from 0.0 to 1.0)
                setting = float(parsed_command[2])
                if(setting < 0 or setting > 1):
                    setting = 1
                pixels.brightness = setting
                pixels.show()
            elif(parsed_command[1] == "moonlight"): # Enable moonlight mode (no argument)
                mode = 3
                curr_frame = 0
                frame_time = 0
            else:
                print("Invalid command")

    # Get time in ms
    # This value can roll over but it shouldn't cause a significant issue
    curr_time = supervisor.ticks_ms()

    # Update the LEDs depending on mode
    if(mode == 1):
        curr_frame = rainbow_cycle(curr_frame)
    elif(mode == 2 and (abs(curr_time - frame_time)) >= SUNRISE_PERIOD_MS):
        curr_frame = sunrise(curr_frame)
        frame_time = curr_time
    elif(mode == 3 and (abs(curr_time - frame_time)) >= MOONLIGHT_PERIOD_MS):
        curr_frame = moonlight_shimmer(curr_frame)
        frame_time = curr_time

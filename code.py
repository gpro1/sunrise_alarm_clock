import time
import board
import neopixel
import digitalio
import adafruit_dotstar
import supervisor

#command headers for uart interface
HEADER = "GB23"

#Onboard LED
led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

#NeoPixel control pin
pixel_pin = board.D5

# The number of NeoPixels
num_pixels = 40

pixel_brightness = 1

#Max values for sunrise function
blueMax = 45
greenMax = 130
sunmax = 230

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=pixel_brightness, auto_write=False,
                           pixel_order=ORDER)
pixels.fill((0,0,0))
pixels.show()

def rainbow_cycle(frame):
    for i in range(num_pixels):
        pixel_index = (i * 256 // num_pixels) + frame
        pixels[i] = wheel(pixel_index & 255)
    pixels.show()
    frame = frame + 1
    if(frame > 255):
        frame = 0
    return frame

def fill_colour(r,g,b):
    pixels.fill((r, g, b))
    pixels.show()

def fill_red():
    pixels.fill((255,0,0))
    pixels.show()

def sunrise(frame):
    pixels.fill((r_sun(frame),g_sun(frame),b_sun(frame)))
    pixels.show()
    if(frame < sunmax):
        frame = frame + 1
    return frame

def r_sun(index):
    if(index < 85):
        value = index*3
    else:
        value = 255
    return value

def g_sun(index):
    value = index-20
    if(value < 0):
        value = 0
    elif(value > greenMax):
        value = greenMax
    return value

def b_sun(index):
    value = index - 170;
    if(value < 0):
        value = 0
    elif(value > blueMax):
        value = blueMax
    return value

led.brightness = 0.5
led[0] = (0,0,0)
mode = 0
curr_frame = 0
led[0] = (25, 0, 0)

#TODO: Add some sort of delay option for the animations
while True:

    # Check for a new command in the buffer
    if(supervisor.runtime.serial_bytes_available == True):
        command = input()
        parsed_command = command.split(' ')
        if(parsed_command[0] == HEADER): # Command has a valid header

            #Parse command
            if(parsed_command[1] == "rainbow"):
                mode = 1
                curr_frame = 0
            elif(parsed_command[1] == "off"):
                mode = 0
                fill_colour(0,0,0)
            elif(parsed_command[1] == "colour"):
                mode = 0
                fill_colour(int(parsed_command[2]), int(parsed_command[3]), int(parsed_command[4]))
            elif(parsed_command[1] == "sunrise"):
                mode = 2
                curr_frame = 0
            else:
                print("Invalid command")

    #Update the LEDs depending on mode
    if(mode == 1):
        curr_frame = rainbow_cycle(curr_frame)
    elif(mode == 2):
        curr_frame = sunrise(curr_frame)
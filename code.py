import time
import board
import neopixel
import digitalio
import adafruit_dotstar
import supervisor

HEADER = "GB23"

led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

pixel_pin = board.D5
rpi_trigger = digitalio.DigitalInOut(board.D7)
rpi_trigger.direction = digitalio.Direction.INPUT

# The number of NeoPixels
num_pixels = 40

pixel_brightness = 1
blueMax = 45
greenMax = 130

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=pixel_brightness, auto_write=False,
                           pixel_order=ORDER)
pixels.fill((0,0,0))
pixels.show()

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


def rainbow_cycle_blocking(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        #time.sleep(wait)

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

sunmax = 230

def sunrise_blocking(wait):
    for j in range(sunmax):
        pixels.fill((r_sun(j),g_sun(j),b_sun(j)))
        pixels.show()
        time.sleep(wait)

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
while True:

    if(supervisor.runtime.serial_bytes_available == True):
        command = input()
        parsed_command = command.split(' ')
        if(parsed_command[0] == HEADER):

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


    #sunrise(3.9)
    if(mode == 1):
        curr_frame = rainbow_cycle(curr_frame)
    elif(mode == 2):
        curr_frame = sunrise(curr_frame)
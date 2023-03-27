import time
import random
import board
import neopixel
import digitalio
import busio
import adafruit_dotstar
import supervisor
import math

#command headers for uart interface
HEADER = "GB23"

SUNRISE_PERIOD_S = 0.05
MOONLIGHT_PERIOD_S = 0.05



#Onboard LED
led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

#NeoPixel control pin
pixel_pin = board.D5

# The number of NeoPixels
num_pixels = 40
GAMMA = 1.8
pixel_brightness = 1

#Max values for sunrise function
blueMax = 45
greenMax = 130
sunmax = 230



# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

uart = busio.UART(board.TX, board.RX, baudrate=9600)

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


def rainbow_cycle(frame):
    for i in range(num_pixels):
        pixel_index = (i * 256 // num_pixels) + frame
        pixels[i] = wheel(pixel_index & 255)
    pixels.show()
    frame = frame + 1
    if(frame > 255):
        frame = 0
    return frame


# Define a function to apply the gamma filter to a color tuple
def gamma_correct(color):
    return tuple(int(pow(c / 255.0, GAMMA) * 255) for c in color)

pixel_colour = [[130,0,255]]*20
pixel_index = [-1]*20
pixel_position = [0]*20
num_flashing = 20

def moonlight_shimmer(frame):
    global pixel_colour
    global pixel_index

    num = random.uniform(0,2)
    num = int(num*100)
    if(num%10 == 0):

        num = int(num/10)
        print(num)
        if(pixel_index[num] == -1):
            pixel_index[num] = 0
            pixel_position[num] = int(random.uniform(0,40))

    if(frame == 0):
        pixels.fill((130, 0, 255))

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
            pixel_index[i] = -1


        rounded_pix = (int(round(pixel_colour[i][0],0)),int(round(pixel_colour[i][1],0)) , int(round(pixel_colour[i][2],0)))
        pixels[pixel_position[i]] = gamma_correct(rounded_pix)

    pixels.show()



    frame += 1;
    if(frame > 100):
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
mode = 3
curr_frame = 0
frame_time = 0
led[0] = (25, 0, 0)
pixels.brightness = 0.1

#TODO: Add some sort of delay option for the animations
while True:

    # Check for a new command in the buffer
    if(uart.in_waiting > 0):
        command = uart.read()
        command_string = ''.join([chr(b) for b in command])
        print(command_string, end="")
        parsed_command = command_string.split(' ')
        if(parsed_command[0] == HEADER): # Command has a valid header

            #Parse command
            if(parsed_command[1] == "rainbow"):
                mode = 1
                curr_frame = 0
                pixels.brightness = 1
            elif(parsed_command[1] == "off"):
                mode = 0
                pixels.brightness = 1
                fill_colour(0,0,0)
            elif(parsed_command[1] == "colour"):
                mode = 0
                pixels.brightness = 1
                fill_colour(int(parsed_command[2]), int(parsed_command[3]), int(parsed_command[4]))
            elif(parsed_command[1] == "sunrise"):
                mode = 2
                curr_frame = 0
                frame_time = 0
                pixels.brightness = 1
            elif(parsed_command[1] == "brightness"):
                setting = float(parsed_command[2])
                if(setting < 0 or setting > 1):
                    setting = 1
                pixels.brightness = setting
                pixels.show()
            else:
                print("Invalid command")

    #curr_time = supervisor.ticks_ms()
    curr_time = time.monotonic()
    #print(curr_frame)

    #Update the LEDs depending on mode
    if(mode == 1):
        curr_frame = rainbow_cycle(curr_frame)
    elif(mode == 2 and (abs(curr_time - frame_time)) >= SUNRISE_PERIOD_S):
        curr_frame = sunrise(curr_frame)
        frame_time = curr_time
    elif(mode == 3 and (abs(curr_time - frame_time)) >= MOONLIGHT_PERIOD_S):

        curr_frame = moonlight_shimmer(curr_frame)
        frame_time = curr_time
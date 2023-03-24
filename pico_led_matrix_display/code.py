import board, time, displayio, rgbmatrix, framebufferio, digitalio
from digitalio import DigitalInOut, Pull
import adafruit_imageload, os, random

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=128, bit_depth=2,
    rgb_pins=[board.GP1, board.GP6, board.GP0, board.GP7, board.GP8, board.GP2],    # G,B swapped
    addr_pins=[board.GP9, board.GP3, board.GP10, board.GP4],
    clock_pin=board.GP11, latch_pin=board.GP5, output_enable_pin=board.GP12)
display = framebufferio.FramebufferDisplay(matrix)

pin_hex_sw_01 = DigitalInOut(board.GP28)
pin_hex_sw_02 = DigitalInOut(board.GP27)
pin_hex_sw_04 = DigitalInOut(board.GP26)
pin_hex_sw_08 = DigitalInOut(board.GP22)
pin_hex_sw_11 = DigitalInOut(board.GP21)
pin_hex_sw_12 = DigitalInOut(board.GP20)
pin_hex_sw_14 = DigitalInOut(board.GP19)
pin_hex_sw_18 = DigitalInOut(board.GP18)
pin_hold_sw = DigitalInOut(board.GP17)

pin_hex_sw_01.pull = Pull.UP
pin_hex_sw_02.pull = Pull.UP
pin_hex_sw_04.pull = Pull.UP
pin_hex_sw_08.pull = Pull.UP
pin_hex_sw_11.pull = Pull.UP
pin_hex_sw_12.pull = Pull.UP
pin_hex_sw_14.pull = Pull.UP
pin_hex_sw_18.pull = Pull.UP
pin_hold_sw.pull = Pull.UP

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

bmpspath = "bmp/"
first_time = True
last_filename  = ""
sub_dir_list = os.listdir(bmpspath)
sub_dir_num = len(sub_dir_list)
mode = pin_hold_sw.value        # Hold-Reset then Roulette Mode
led.value = not mode

def read_interval_pos():
    pos = pin_hex_sw_01.value + pin_hex_sw_02.value * 2 + pin_hex_sw_04.value * 4 + pin_hex_sw_08.value * 8
    return pos

def read_directory_pos():
    pos = pin_hex_sw_11.value + pin_hex_sw_12.value * 2 + pin_hex_sw_14.value * 4 + pin_hex_sw_18.value * 8
    return pos

def displaybmp(filename): # Displays a bmp on your LED Matrix
    g = displayio.Group()
    b, p = adafruit_imageload.load(filename)
    t = displayio.TileGrid(b, pixel_shader=p)
    g.append(t)
    display.show(g)

def display_and_delay(filename):
    displaybmp(filename)
    print(filename)
    start_time = time.time()
    interval_sec = read_interval_pos()
    while time.time() < (start_time + interval_sec):  #
        time.sleep(0.1)
    while pin_hold_sw.value == 0:
        time.sleep(0.1)

def get_filename_random():
    i = random.randrange(len(sub_dir_list))
    display_dir = bmpspath + sub_dir_list[i] +'/'
    bmp_file_list = os.listdir(display_dir)
    j = random.randrange(len(bmp_file_list))
    filename = display_dir + bmp_file_list[j]
    return filename

while True:
    if(mode):
        for i in range(sub_dir_num):
            if first_time:
                directory_pos = read_directory_pos()
                if directory_pos < sub_dir_num:
                    i = directory_pos
                first_time = False
            display_dir = bmpspath + sub_dir_list[i] +'/'
            for bmp_file in os.listdir(display_dir):
                filename = display_dir + bmp_file
                display_and_delay(filename)

    else:       # Random, Roulette Mode
        filename = get_filename_random()
        if last_filename != filename:
            last_filename = filename
            display_and_delay(filename)


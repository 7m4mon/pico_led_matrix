import board, time, displayio, rgbmatrix, framebufferio, digitalio, simpleio
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
pin_push_sw = DigitalInOut(board.GP17)

pin_hex_sw_01.pull = Pull.UP
pin_hex_sw_02.pull = Pull.UP
pin_hex_sw_04.pull = Pull.UP
pin_hex_sw_08.pull = Pull.UP
pin_hex_sw_11.pull = Pull.UP
pin_hex_sw_12.pull = Pull.UP
pin_hex_sw_14.pull = Pull.UP
pin_hex_sw_18.pull = Pull.UP
pin_push_sw.pull = Pull.UP

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

BUTTON_BUFFER_SIZE = 1
button_history = [0] * BUTTON_BUFFER_SIZE
button_history_index = 0
last_button_history_sum = 0
roulette_stopped = False

bmp_path = "bmp/"
last_file_path = ""
last_file_name = ""
bmpfile_list = os.listdir(bmp_path)

atari_file_name = ["hydrogen.png_.bmp", "cassiopeia_sapporo-1.png_.bmp","extra_beer.png_.bmp",
                   "polestar2_1.png_.bmp","polestar2_2.png_.bmp","polestar2_3.png_.bmp","polestar2_4.png_.bmp",
                   "out of service_summer1.png_.bmp","out of service_summer2.png_.bmp",
                   "out of service_winter1.png_.bmp","out of service_winter2.png_.bmp",
                   "expo.bmp","extra_beer.png_.bmp","sounyan01.bmp","sounyan02.bmp","ensoku.png_.bmp"
                   ]

beep_melody = [
    [[2000,0.1],[1000,0.1],[500,0.1]],
    [[500,0.1],[1000,0.1],[2000,0.1],[4000,0.1],[500,0.1],[1000,0.1],[2000,0.1],[4000,0.1],[500,0.1],[1000,0.1],[2000,0.1],[4000,0.1],[8000,0.1]]   # HIT!
]

def play_melody(num):
    for note in beep_melody[num]:
        simpleio.tone(board.GP15, note[0], duration=note[1])

def atari_judge():
    melody_num = 0
    for fn in atari_file_name:
        if fn == last_file_name :
            melody_num = 1
    play_melody(melody_num)

def read_interval_pos():
    pos = pin_hex_sw_01.value + pin_hex_sw_02.value * 2 + pin_hex_sw_04.value * 4 + pin_hex_sw_08.value * 8
    return pos

def read_directory_pos():
    pos = pin_hex_sw_11.value + pin_hex_sw_12.value * 2 + pin_hex_sw_14.value * 4 + pin_hex_sw_18.value * 8
    return pos

def sum_button_history():
    n = 0
    for s in button_history:
        n += s
    return n
        
def det_button_pushed():
    global button_history_index, last_button_history_sum
    det_pushed = False
    btn = not pin_push_sw.value
    button_history[button_history_index] = int(btn)
    button_history_index += 1
    if button_history_index > BUTTON_BUFFER_SIZE - 1:
        button_history_index = 0
    sum = sum_button_history()
    if last_button_history_sum == 0 and sum != 0:
        det_pushed = True
    last_button_history_sum = sum
    return det_pushed

def displaybmp(filepath): # Displays a bmp on your LED Matrix
    g = displayio.Group()
    b, p = adafruit_imageload.load(filepath)
    t = displayio.TileGrid(b, pixel_shader=p)
    g.append(t)
    display.show(g)

def display_and_delay(filepath):
    displaybmp(filepath)
    simpleio.tone(board.GP15, 4000, duration=0.02)
    start_time = time.time()
    interval_sec = read_interval_pos()
    while time.time() < (start_time + interval_sec): 
        time.sleep(0.1)


def do_roulette():
    global roulette_stopped
    if det_button_pushed():
        roulette_stopped = True
        atari_judge()
        while roulette_stopped:
            if det_button_pushed():
                roulette_stopped = False
            time.sleep(0.1)

def get_filepath_random():
    global last_file_name
    i = random.randrange(len(bmpfile_list))
    filepath = bmp_path + bmpfile_list[i]
    last_file_name = bmpfile_list[i]
    return filepath

mode = pin_push_sw.value
led.value = not mode

if mode:
    while True:
        filepath = get_filepath_random()
        if last_file_path != filepath:
            last_file_path = filepath
            display_and_delay(filepath)
            do_roulette()
else :
    det_button_pushed()
    while True:
        for bmpfile in bmpfile_list:
            filepath = bmp_path + bmpfile
            display_and_delay(filepath)
            while not det_button_pushed():
                time.sleep(0.1)


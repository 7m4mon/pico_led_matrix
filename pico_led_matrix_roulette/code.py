'''
pico_led_matrix
Raspberry Pi PicoでLED方向幕のルーレットを作ってみよう！
2023,2024
author: 7M4MON
https://nomulabo.com/pico_led_matrix/
'''

import board, time, displayio, rgbmatrix, framebufferio, digitalio, simpleio, analogio
from digitalio import DigitalInOut, Pull
import adafruit_imageload, os, random

# Pins: GP0-12=matrix, GP15=Beep, GP13,14,16,22=HexSw0, GP18-21=HexSw1, GP23-25=N/A, GP26-28=ADC
# All pins are occupied.

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=128, bit_depth=2,
    rgb_pins=[board.GP1, board.GP6, board.GP0, board.GP7, board.GP8, board.GP2],    # G,B swapped
    addr_pins=[board.GP9, board.GP3, board.GP10, board.GP4],
    clock_pin=board.GP11, latch_pin=board.GP5, output_enable_pin=board.GP12)
display = framebufferio.FramebufferDisplay(matrix)

# display interval time (x100ms)
pin_hex_sw_01 = DigitalInOut(board.GP13)        # 28 -> 13
pin_hex_sw_02 = DigitalInOut(board.GP14)        # 27 -> 14
pin_hex_sw_04 = DigitalInOut(board.GP16)        # 26 -> 16
pin_hex_sw_08 = DigitalInOut(board.GP22)
# restert hold time (sec)
pin_hex_sw_11 = DigitalInOut(board.GP21)
pin_hex_sw_12 = DigitalInOut(board.GP20)
pin_hex_sw_14 = DigitalInOut(board.GP19)
pin_hex_sw_18 = DigitalInOut(board.GP18)
pin_push_sw = DigitalInOut(board.GP17)

pin_train_sens_0 = analogio.AnalogIn(board.A0)    #GP26
pin_train_sens_1 = analogio.AnalogIn(board.A1)    #GP27
pin_train_sens_threshold = analogio.AnalogIn(board.A2)    #GP28

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

def read_holdtime_pos():
    pos = pin_hex_sw_11.value + pin_hex_sw_12.value * 2 + pin_hex_sw_14.value * 4 + pin_hex_sw_18.value * 8
    return pos

def sum_button_history():
    n = 0
    for s in button_history:
        n += s
    return n

def det_button_pushed(single_mode = False):
    global button_history_index, last_button_history_sum
    det_pushed = False
    btn = not pin_push_sw.value
    if single_mode:     
        return btn                                  # シングルモードは即判定する。
    button_history[button_history_index] = int(btn) # チャタリング防止で回数分だけ0だったら押されたと判定する。
    button_history_index += 1
    if button_history_index > BUTTON_BUFFER_SIZE - 1:
        button_history_index = 0
    sum = sum_button_history()
    if last_button_history_sum == 0 and sum != 0:
        det_pushed = True
    last_button_history_sum = sum
    return det_pushed

history_sens_0 = [0] * 8
history_sens_1 = [0] * 8
index_sens = 0

def det_train_passing():
    global index_sens, history_sens_0, history_sens_1
    thres = pin_train_sens_threshold.value >> 6     # 250くらいでOK
    sens_0 = pin_train_sens_0.value >> 4      # high = 3670, low = 2000
    sens_1 = pin_train_sens_1.value >> 4      # high = 3370, low = 2000
    avg_sens_0 = sum(history_sens_0) >> 3     # devide by 8
    history_sens_0[index_sens] = sens_0 # prepare next average
    history_sens_1[index_sens] = sens_1 # prepare next average
    index_sens += 1
    if index_sens == 8:
        index_sens = 0
    avg_sens_1 = sum(history_sens_1) >> 3     # devide by 8
    retval = False
    print("sens0:" + str(sens_0) + ", avg0:" + str(avg_sens_0) + " ,thres:" + str(thres))
    print("sens1:" + str(sens_1) + ", avg1:" + str(avg_sens_1) + " ,index:" + str(index_sens))
    if (avg_sens_0 - sens_0) > thres or (avg_sens_1 - sens_1) > thres:
        retval = True
    print("Detect:" + str(retval))
    return retval


def displaybmp(filepath): # Displays a bmp on your LED Matrix
    g = displayio.Group()
    b, p = adafruit_imageload.load(filepath)
    t = displayio.TileGrid(b, pixel_shader=p)
    g.append(t)
    display.show(g)

def display_and_delay(filepath):
    displaybmp(filepath)
    simpleio.tone(board.GP15, 4000, duration=0.02)
    for i in range(read_interval_pos()): 
        time.sleep(0.1)


def do_roulette():
    global roulette_stopped
    if det_button_pushed(single_mode = True) or det_train_passing():
        roulette_stopped = True
        atari_judge()
        tot = read_holdtime_pos() * 100
        while roulette_stopped:
            tot -= 1
            if det_button_pushed(single_mode = True) or tot < 1:
                roulette_stopped = False
            time.sleep(0.01)

def get_filepath_random():
    global last_file_name
    i = random.randrange(len(bmpfile_list))
    filepath = bmp_path + bmpfile_list[i]
    last_file_name = bmpfile_list[i]
    return filepath

roulette_mode = pin_push_sw.value       # 電源投入時にボタンが押されていたら順繰り表示
led.value = not roulette_mode

if roulette_mode:
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


# a PICO W powered drag race "Chistmas Tree" designed to be used at Pinewood Derbies.
# Created at Maker Alliance Summer Camp, on August 4, 2022 in Elizabethtown, Kentucky.
# Software and hardware were donated to a local Cub Scout pack at the end of Camp.
# Software is provided as-is and without warranty
# Contributors:
#  Sean O'Steen - @TinkeringRocks - sean@tinkeringrocks.com
#  Halbert Walston - halbert.walston@gmail.com
#
import utime, array
from machine import Pin
import rp2
import random
import socket
import network
import _thread
from secrets import secrets


# Configure the number of WS2812 LEDs, pins and brightness.
NUM_LEDS = 37
PIN_NUM = 22
brightness = .5
 
 
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
 
 
# Create the StateMachine with the ws2812 program, outputting on Pin(16).
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))
sm.active(1)
ar = array.array("I", [0 for _ in range(NUM_LEDS)])
 
def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    utime.sleep_ms(10)
 
def pixels_set(i, color):
    ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]
    
def pixel_group_set(pg, color):
    for i in range(len(pg)):
        pixels_set(pg[i], color)
 
def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)
 
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

#####################################################
#Pixel Groups
ALL = [0,1,2,3,4,5,6,7,8,9,10,11,
           12,13,14,15,16,17,18,19,20,21,22,23,
           24,25,26,27,28,29,30,31,32,33,34,35,
           36]
LR = [0,1,2,3,4,5,6,7,8]
LF = [17,16,15,14,13,12,11,10,9]
RR = [36,35,34,33,32,31,30,29,28]
RF = [19,20,21,22,23,24,25,26,27]
HEADLIGHTS = [14,15,16,17,18,19,20,21,22,23]
BRAKES = [0,1,2,3,4,5,36,35,34,33,32,31]

#####################################################
# Animations
def chase():
    color = COLORS[random.randint(0,len(COLORS)-1)]
    for i in range(0,len(ALL)):
        pixels_set(ALL[i], color)
        pixels_show()
        utime.sleep(.02)

def randomSet():
    color = COLORS[random.randint(0,len(COLORS)-1)]
    pixel = ALL[random.randint(0,len(ALL)-1)]
    pixels_set(pixel, color)
    pixels_show()
    utime.sleep(0.2)
        
def leftTurn():
    pixels_fill(BLACK)
    for blink in range(0,2):
        for i in range(0,len(LR)):
            pixels_set(LR[i], YELLOW)
            pixels_set(LF[i], YELLOW)
            pixels_show()
            utime.sleep(.02)
        pixel_group_set(LR, BLACK)
        pixel_group_set(LF, BLACK)
        pixels_show()
        utime.sleep(.5)

def rightTurn():
    pixels_fill(BLACK)
    for blink in range(0,2):
        for i in range(0,len(RR)):
            pixels_set(RR[i], YELLOW)
            pixels_set(RF[i], YELLOW)
            pixels_show()
            utime.sleep(.02)
        pixel_group_set(RR, BLACK)
        pixel_group_set(RF, BLACK)
        pixels_show()
        utime.sleep(.5)

def hazardLights():
    pixels_fill(BLACK)
    for blink in range(0,2):
        for i in range(0,len(LR)):
            pixels_set(LR[i], YELLOW)
            pixels_set(LF[i], YELLOW)
            pixels_set(RR[i], YELLOW)
            pixels_set(RF[i], YELLOW)
            pixels_show()
            utime.sleep(.02)
        pixel_group_set(LR, BLACK)
        pixel_group_set(LF, BLACK)
        pixel_group_set(RR, BLACK)
        pixel_group_set(RF, BLACK)
        pixels_show()
        utime.sleep(.5)

def headlights():
    pixels_fill(BLACK)
    pixel_group_set(HEADLIGHTS, WHITE)
    pixels_show()
    utime.sleep(1)
    
def brakes():
    pixels_fill(BLACK)
    for blink in range(0,3):
        pixel_group_set(BRAKES, RED)
        pixels_show()
        utime.sleep(.1)
        pixels_fill(BLACK)
        pixels_show()
        utime.sleep(.1)
    pixel_group_set(BRAKES, RED)
    pixels_show()
    utime.sleep(5)
    pixels_fill(BLACK)
    pixels_show()
    utime.sleep(2)
    blank()
    print("brakes released")
                   
    
# Shared variable between two threads
ANIMATION = ""
LASTREQUEST = 0

def blank():
    global ANIMATION
    global LASTREQUEST
    ANIMATION = ""
    pixels_fill(BLACK)
    pixels_show()
    LASTREQUEST = 0
    
#####################################################
# Set Up Webserver Thread

def ws_thread(s):
    global ANIMATION
    global LASTREQUEST
    
    print('Starting second thread for the webserver answer loop')
    
    html = """<!DOCTYPE html>
    <html>
        <head> <title>Pinewood Derby Start Lights</title>
        <style>
            body { background-color: #E30B5D; }
            .link {
                color: #FFFFFF;
                font-size: 80px;
                font-family: Arial, Helvetica, sans-serif;
                font-weight: bold;
                background-color: #e3b6c7;
                padding: 50px;
                margin: 20px;
                left-margin: auto;
                right-margin: auto;
                border-radius: 20px;
            }
            a, a:visited { color: #FFFFFF; text-decoration: none;}
            a:active { color: #E30B5D; }
        </style>
        </head>
        <body> 
            <p class='link'><a href='/?headlights'>HEADLIGHTS</a></p>
            <p class='link'><a href='/?brakes'>BRAKE LIGHTS</a></p>
            <p class='link'><a href='/?left'>LEFT TURN</a></p>
            <p class='link'><a href='/?right'>RIGHT TURN</a></p>
            <p class='link'><a href='/?hazards'>HAZARD LIGHTS</a></p>
            <p class='link'><a href='/?cancel'>CANCEL</a></p>
        </body>
    </html>


    """
    # Listen for connections
    while True:
        try:
            cl, addr = s.accept()
            print('client connected from', addr)
            
            cl.settimeout(1.0) #keep iphone from holding open a connection
            request = cl.recv(1024)
            request = str(request)
            
            hazards = request.find('?hazards ')
            if hazards >= 0:
                ANIMATION = 'hazards'
            
            left = request.find('?left ')
            if left >= 0:
                ANIMATION = 'left'
                
            right = request.find('?right ')
            if right >= 0:
                ANIMATION = 'right'
                
            headlights = request.find('?headlights ')
            if headlights >= 0:
                ANIMATION = 'headlights'
            
            brakes = request.find('?brakes ')
            if brakes >= 0:
                ANIMATION = 'brakes'
            
            cancel = request.find('?cancel ')
            if cancel >= 0:
                ANIMATION = ''
                LASTREQUEST = 0
                
            print("Client requested :",ANIMATION)
            
            if ANIMATION != '':
                LASTREQUEST = int(utime.time())

            response = html

            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(response)
            cl.close()
            print('connection closed')
            
        except OSError as e:
            cl.close()
            print('connection closed on error')

#Start the Access point and web server

ap = network.WLAN(network.AP_IF)
ap.config(essid=secrets['ssid'], password=secrets['pass'])
ap.active(True)

max_wait = 10
while max_wait > 0:
    if ap.status() < 0 or ap.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    utime.sleep(1)

if ap.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = ap.ifconfig()
    print( 'ip = ' + status[0] )

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

def animThread():
    global ANIMATION
    global LASTREQUEST
    print('Starting main animation thread')
    while True:
        if ANIMATION == "left":
            leftTurn()
        elif ANIMATION == "right":
            rightTurn()
        elif ANIMATION == "hazards":
            hazardLights()
        elif ANIMATION == "headlights":
            headlights()
        elif ANIMATION == "brakes":
            brakes()
        else:
            #chase()
            randomSet()
        
        #Check to see if the last command was more than 30 seconds ago
        if LASTREQUEST != 0:
            timeout = int(utime.time() - LASTREQUEST)
            if timeout > 30:
                print("Animation Timed out, resetting.")
                blank()

#####################################################
# Start the animation loop on the second RP2040 core
second_thread = _thread.start_new_thread(animThread, ())

#####################################################
# Start the main thread Loop for the web service
ws_thread(s)
    



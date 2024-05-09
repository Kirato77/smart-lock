from machine import Pin
import machine
import utime

# Mappage des touches du clavier à leurs lettres correspondantes

key_map = [['0', 'F', 'E', 'D'],
           ['7', '8', '9', 'C'],
           ['4', '5', '6', 'B'],
           ['1', '2', '3', 'A']]

keypad_rows = [4,5,6,7]
keypad_columns = [0,1,2,3]

led_pins = [Pin(16, Pin.OUT), Pin(17, Pin.OUT), Pin(18, Pin.OUT), Pin(19, Pin.OUT)]

servo_pin = machine.Pin(27)

pwm = machine.PWM(servo_pin)

pwm.freq(50)

col_pins = []
row_pins = []

guess = []

secret_pin = ['1','2']

unlockLED = Pin(20, Pin.OUT)
lockedLED = Pin(21, Pin.OUT)

for i in range(0,4):
    row_pins.append(Pin(keypad_rows[i], Pin.OUT))
    col_pins.append(Pin(keypad_columns[i], Pin.IN, Pin.PULL_DOWN))

def set_angle(angle):
    duty = int(((angle / 180) * 1000) + 500)
    pwm.duty_u16(duty * 65535 // 10000)
    
def display(decimal):
    for i in range(3, -1, -1):
        led_pins[3 - i].value((decimal >> i) & 1)
        
def scankeys():
    for row in range(4):
        for col in range(4):
            row_pins[row].high()
            key = None
            
            if col_pins[col].value() == 1:
                key_press = key_map[row][col]
                if key_press.isdigit() and 0 <= int(key_press) <= 9:
                    display(int(key_press))
                elif key_press == 'E':
                    display(12)
                    openDoor()
                    clear_guess()
                    continue
                elif key_press == 'B':
                    display(15)
                    clear_guess()
                elif key_press == 'A':
                    display(11)
                    utime.sleep(0.3)
                    changeCode()
                    clear_guess()
                    continue
                else:
                    display(15)
                    
                print("You pressed", key_press)
                utime.sleep(0.3)
                guess.append(key_press)
                
        row_pins[row].low()

def lock():
    lockedLED.on()
    unlockLED.off()
    set_angle(45)  # Déplace le servo à 45 degrés
    utime.sleep(1)

def unlock():
    lockedLED.off()
    unlockLED.on()
    set_angle(0)  # Déplace le servo à 0 degré
    utime.sleep(5)

def checkPin():
    if guess == secret_pin:
        print("good pin")
        return True
    else:
        print("wrong pin")
        return False
        
def openDoor():
    if checkPin():
        unlock()
        utime.sleep(2)
        lock()
    else:
        blink_red()
        
def changeCode():
    global secret_pin
    global guess
    
    if checkPin():
        backup_pin = secret_pin
        secret_pin = []

        print("entered in edit mode")
        unlockLED.on()
        clear_guess()

        while True:
            for row in range(4):
                for col in range(4):
                    row_pins[row].high()
                    key = None
                    
                    if col_pins[col].value() == 1:
                        key_press = key_map[row][col]
                        if key_press.isdigit() and 0 <= int(key_press) <= 9:
                            display(int(key_press))
                        elif key_press == 'B':
                            print("no modifications")
                            secret_pin = backup_pin
                            unlockLED.off()
                            return None
                        elif key_press == 'A':
                            display(11)
                            utime.sleep(0.5)
                            if len(secret_pin) > 0:
                                print("pin modified")
                            else:
                                print("no modifications")
                                secret_pin = backup_pin
                            unlockLED.off()
                            return None
                        else:
                            display(15)
                            
                        print("You pressed", key_press)
                        utime.sleep(0.3)
                        if key_press.isdigit() and 0 <= int(key_press) <= 9:
                            secret_pin.append(key_press)
                        
                row_pins[row].low()
    else:
        blink_red()

def clear_guess():
    for x in range(len(guess)):
        guess.pop()
        
def blink_red():
    for i in range(3):
        lockedLED.off()
        utime.sleep(0.5)
        lockedLED.on()
        utime.sleep(0.5)

def blink_green():
    for i in range(3):
        unlockLED.off()
        utime.sleep(0.5)
        unlockLED.on()
        utime.sleep(0.5)
        
print("Enter the password")
i = 0  
while True:
    while i < 1:
        
        lockedLED.on()
        unlockLED.off()
        i += 1
    scankeys()

import network
import socket
import machine
import _thread
import utime
from machine import Pin, PWM

global guess, secret_pin

# Mappage des touches du clavier à leurs lettres correspondantes
key_map = [['0', 'F', 'E', 'D'],
           ['7', '8', '9', 'C'],
           ['4', '5', '6', 'B'],
           ['1', '2', '3', 'A']]

keypad_rows = [4,5,6,7]
keypad_columns = [0,1,2,3]

col_pins = [Pin(col, Pin.IN, Pin.PULL_DOWN) for col in keypad_columns]
row_pins = [Pin(row, Pin.OUT) for row in keypad_rows]
    
# Définition des broches des LED
led_pins = [Pin(pin, Pin.OUT) for pin in range(16, 20)]
unlockLED = Pin(20, Pin.OUT)
lockedLED = Pin(21, Pin.OUT)

# Définition du servo et de la fréquence PWM
servo_pin = machine.Pin(27)
pwm = machine.PWM(servo_pin)
pwm.freq(50)

# Password and WiFi credentials
secret_pin = ['1', '2']
guess = []
ssid = 'ssid'
password = 'password'

def connect():
    # Fonction de connexion au réseau WiFi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Waiting for connection...')
        utime.sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Fonction pour ouvrir un socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection

def webpage():
    # Fonction pour générer la page web
    return """
        <!DOCTYPE html>
        <html>
            <header>
                <title> Unsmart Lock </title>
            </header>
            <body>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                    }

                    header {
                        background-color: #333;
                        color: #fff;
                        padding: 10px 0;
                        text-align: center;
                    }

                    section {
                        padding: 20px;
                        text-align: center;
                    }

                    h1 {
                        color: #333;
                        font-size: 50px;
                    }

                    input[type="text"] {
                        width: 200px;
                        padding: 10px;
                        margin-bottom: 10px;
                    }

                    button {
                        padding: 10px 20px;
                        background-color: #333;
                        color: #fff;
                        border: none;
                        cursor: pointer;
                        font-weight: bold;
                    }

                    button:hover {
                        background-color: #7d7d7d;
                    }
                </style>
                <section>
                    <h1>Smart Lock Remote</h1>
                    <input type="text" placeholder="Enter password" id="guess" />
                    <button onClick="check()"> Unlock </button>
                </section>
            
                <script>
                    function check(){
                        var code = document.getElementById("guess").value;
                        var xhttp = new XMLHttpRequest();
                        xhttp.open('GET', '/check/'+code, true);
                        xhttp.send();
                    }
                    function update(){
                        location.reload(true);
                    }
                </script>
            </body>
        </html>
        """

def serve(connection):
    # Fonction pour servir les requêtes HTTP
    global secret_pin
    
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            split_request = request.split()
            split2_request = split_request[1].split('/')
            code = split2_request[2]
            print(code)
        except IndexError:
            pass
        if request.find('/check/') == 6:
            split_code = [str(char) for char in code]
            if split_code == secret_pin:
                unlock()
                utime.sleep(2)
                lock()
            else:
                print("Website: wrong code")
        html = webpage()
        client.send(html)
        client.close()
        
def set_angle(angle):
    # Fonction pour définir l'angle du servo
    duty = int(((angle / 180) * 1000) + 500)
    pwm.duty_u16(duty * 65535 // 10000)
        
def lock():
    # Fonction pour verrouiller la porte
    lockedLED.on()
    unlockLED.off()
    set_angle(45)  # Déplace le servo à 45 degrés
    utime.sleep(1)

def unlock():
    # Fonction pour déverrouiller la porte
    lockedLED.off()
    unlockLED.on()
    set_angle(0)  # Déplace le servo à 0 degré
    utime.sleep(5)

def check_pin():
    # Fonction pour vérifier le code PIN
    if guess == secret_pin:
        print("good pin")
        return True
    else:
        print("wrong pin")
        return False
        
def open_door():
    # Fonction pour ouvrir la porte
    if check_pin():
        unlock()
        utime.sleep(2)
        lock()
    else:
        blink_led(lockedLED, 3)
        
def blink_led(led, times):
    # Blink LED
    for _ in range(times):
        led.off()
        utime.sleep(0.5)
        led.on()
        utime.sleep(0.5)
        
def change_code():
    # Change the PIN
    global secret_pin
    global guess
    if check_pin():
        backup_pin = secret_pin
        secret_pin = []
        print("Entered edit mode")
        unlockLED.on()
        clear_guess()
        while True:
            for row in range(4):
                for col in range(4):
                    row_pins[row].high()
                    if col_pins[col].value() == 1:
                        key_press = key_map[row][col]
                        if key_press.isdigit() and 0 <= int(key_press) <= 9:
                            display(int(key_press))
                        elif key_press == 'B':
                            print("No modifications")
                            secret_pin = backup_pin
                            unlockLED.off()
                            clear_guess()
                            return None
                        elif key_press == 'A':
                            display(11)
                            utime.sleep(0.5)
                            print("PIN modified" if len(secret_pin) > 0 else "No modifications")
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
        blink_led(lockedLED, 3)

def clear_guess():
    global guess
    # Clear guess list
    for x in range(len(guess)):
        guess.pop()
    
def display(decimal):
    # Display decimal value on LEDs
    for i in range(3, -1, -1):
        led_pins[3 - i].value((decimal >> i) & 1)
        
def scan_keys():
    # Scan keypad keys
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
                    open_door()
                    clear_guess()
                    continue
                elif key_press == 'B':
                    display(15)
                    clear_guess()
                elif key_press == 'A':
                    display(11)
                    utime.sleep(0.3)
                    change_code()
                    clear_guess()
                    continue
                else:
                    display(15)
                print("You pressed", key_press)
                utime.sleep(0.3)
                if key_press.isdigit() and 0 <= int(key_press) <= 9:
                    guess.append(key_press)
        row_pins[row].low()
    
def main():
    print("Enter the password")
    i = 0  
    while True:
        while i < 1:
            lockedLED.on()
            unlockLED.off()
            i += 1
        scan_keys()

try:
    _thread.start_new_thread(main, ())
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()

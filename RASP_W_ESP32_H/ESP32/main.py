import network
import time
import urequests
import socket
from machine import Pin

PI_IP = "192.168.4.2"
FLASK_BUTTON_URL = f"http://{PI_IP}:5000/api/button-event"

led_18 = Pin(18, Pin.OUT)
led_19 = Pin(19, Pin.OUT)
button = Pin(21, Pin.IN, Pin.PULL_UP)

led_18.value(1)
led_19.value(1)
time.sleep(1)
led_18.value(0)
led_19.value(0)

print("[WIFI] Starting ESP32 Hotspot...")
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="esp32_hotspot", password="pass_1234", authmode=3)

while not ap.active():
    time.sleep(1)

print(f"[WIFI] Hotspot Active! ESP32 IP: {ap.ifconfig()[0]}")

def notify_boot():
    try:
        data = {"device": "ESP32", "status": "rebooted"}
        headers = {"Content-Type": "application/json"}
        resp = urequests.post(f"http://{PI_IP}:5000/api/boot-sync", json=data, headers=headers)
        resp.close()
    except Exception as e:
        print("Boot sync error:", e)

def notify_flask(state_str):
    try:
        data = {
            "device": "ESP32",
            "pin": 21,
            "state": state_str,
            "event": f"GPIO 21 Button {state_str}",
            "source": "Physical Button",
            "device_id": "HW-GPIO21"
        }
        headers = {"Content-Type": "application/json"}
        resp = urequests.post(FLASK_BUTTON_URL, json=data, headers=headers)
        resp.close()
    except Exception as e:
        print("Network error:", e)

def check_led_state():
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        response_state = "OFF"
        
        if '/api/gpio18/toggle' in request:
            led_18.value(not led_18.value())
            response_state = "ON" if led_18.value() == 1 else "OFF"
        elif '/api/gpio19/toggle' in request:
            led_19.value(not led_19.value())
            response_state = "ON" if led_19.value() == 1 else "OFF"
        
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{{\"status\":\"success\", \"state\":\"{response_state}\"}}")
        conn.close()
    except OSError:
        pass

notify_boot()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)
s.setblocking(False)

last_btn_state = button.value()

while True:
    current_btn_state = button.value()
    if current_btn_state != last_btn_state:
        time.sleep_ms(20)
        current_btn_state = button.value()
        if current_btn_state != last_btn_state:
            last_btn_state = current_btn_state
            notify_flask("Pressed" if current_btn_state == 0 else "Released")
    
    check_led_state()
    time.sleep(0.05)
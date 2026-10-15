import network
import time
import socket
import json
from machine import Pin

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

print(f"[WIFI] Hotspot Active! IP: {ap.ifconfig()[0]}")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)
s.setblocking(False)

last_btn_state = button.value()
event_counter = 1
latest_event = {
    "id": event_counter,
    "event": "System Initialized",
    "state": "IDLE",
    "source": "System",
    "device_id": "SYS-000"
}

def serve_file(conn, filepath, content_type):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n\r\n{content}")
    except OSError:
        conn.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nFile Not Found")

print("[SYSTEM] Standalone Web Server Running...")

while True:
    current_btn_state = button.value()
    if current_btn_state != last_btn_state:
        time.sleep_ms(20)
        current_btn_state = button.value()
        if current_btn_state != last_btn_state:
            last_btn_state = current_btn_state
            state_str = "Pressed" if current_btn_state == 0 else "Released"
            event_counter += 1
            latest_event = {
                "id": event_counter,
                "event": f"GPIO 21 Button {state_str}",
                "state": state_str,
                "source": "Physical Button",
                "device_id": "HW-GPIO21"
            }

    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        if 'GET / ' in request or 'GET /index.html' in request:
            serve_file(conn, 'templates/index.html', 'text/html')
            
        elif 'styles.css' in request:
            serve_file(conn, 'static/styles.css', 'text/css')
            
        elif 'script.js' in request:
            serve_file(conn, 'static/script.js', 'application/javascript')
            
        elif 'GET /api/status' in request:
            status = {"18": "ON" if led_18.value() else "OFF", "19": "ON" if led_19.value() else "OFF"}
            conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{json.dumps(status)}")
            
        elif '/api/gpio18/toggle' in request or '/api/gpio19/toggle' in request:
            pin_num = '18' if 'gpio18' in request else '19'
            target_pin = led_18 if pin_num == '18' else led_19
            
            target_pin.value(not target_pin.value())
            state_str = "ON" if target_pin.value() else "OFF"
            
            source_device = "Web Dashboard"
            device_id = "UNKNOWN"
            
            for line in request.split('\r\n'):
                if line.startswith("X-Device-Source:"):
                    source_device = line.split(":", 1)[1].strip()
                elif line.startswith("X-Device-ID:"):
                    device_id = line.split(":", 1)[1].strip()

            event_counter += 1
            latest_event = {
                "id": event_counter,
                "event": f"Pin {pin_num} toggled {state_str}",
                "state": state_str,
                "source": source_device,
                "device_id": device_id
            }
            
            conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{json.dumps({'pin': pin_num, 'state': state_str})}")
            
        elif 'GET /api/latest-event' in request:
            conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{json.dumps(latest_event)}")
            
        else:
            conn.send("HTTP/1.1 404 Not Found\r\n\r\nNot Found")
            
        conn.close()
    except OSError:
        pass
        
    time.sleep(0.05)
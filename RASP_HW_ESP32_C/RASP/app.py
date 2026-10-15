import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

esp32_ip_cache = {"ip": None}
led_states = {"18": "OFF", "19": "OFF"}
event_counter = 1
latest_button_event = {
    "id": event_counter,
    "event": "System Initialized",
    "state": "IDLE",
    "source": "System",
    "device_id": "SYS-000"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(led_states)

@app.route('/api/boot-sync', methods=['POST'])
def boot_sync():
    global led_states
    data = request.get_json(silent=True) or {}
    if "ip" in data:
        esp32_ip_cache["ip"] = data["ip"]
        print(f"[SERVER] ESP32 registered at IP: {data['ip']}")
    led_states = {"18": "OFF", "19": "OFF"}
    return jsonify({"success": True, "states": led_states})

@app.route('/api/gpio<int:pin>/toggle', methods=['POST'])
def toggle_gpio(pin):
    global event_counter, latest_button_event
    pin_str = str(pin)
    if pin_str in led_states:
        new_state = "ON" if led_states[pin_str] == "OFF" else "OFF"
        target_ip = esp32_ip_cache.get("ip")
        
        if not target_ip:
            return jsonify({"error": "ESP32 not connected yet"}), 503

        source_device = request.headers.get("X-Device-Source", "Web Dashboard")
        device_id = request.headers.get("X-Device-ID", "UNKNOWN")

        try:
            response = requests.get(f"http://{target_ip}/api/gpio{pin_str}/toggle", timeout=2)
            data = response.json()
            led_states[pin_str] = data.get("state", new_state)
        except Exception:
            led_states[pin_str] = new_state

        event_counter += 1
        latest_button_event = {
            "id": event_counter,
            "event": f"Pin {pin_str} toggled {led_states[pin_str]}",
            "state": led_states[pin_str],
            "source": source_device,
            "device_id": device_id
        }

        return jsonify({"pin": pin_str, "state": led_states[pin_str]})
    return jsonify({"error": "Invalid pin"}), 400

@app.route('/api/button-event', methods=['POST'])
def receive_button_event():
    global latest_button_event, event_counter
    data = request.get_json(silent=True) or {}
    state = data.get("state", "UNKNOWN")
    
    event_counter += 1
    latest_button_event = {
        "id": event_counter,
        "event": data.get("event", f"GPIO 21 Button {state}"),
        "state": state,
        "source": data.get("source", "Physical Button"),
        "device_id": data.get("device_id", "HW-GPIO21")
    }
    return jsonify({"success": True})

@app.route('/api/latest-event', methods=['GET'])
def get_latest_event():
    return jsonify(latest_button_event)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
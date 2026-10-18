# Raspberry Pi x ESP32 IoT Hub - System Architecture Guide

This is the **Raspberry Pi x ESP32 IoT Hub** sample project repository. This document outlines the four distinct networking and compute architectures designed to bridge MicroPython (ESP32 hardware) and Flask (Python web server), featuring a modern, multi-device synchronized web interface with real-time logging.

---

## Global Network Credentials Reference

- **Raspberry Pi Hotspot (`rasp_hotspot`)**: Used in Architecture #1
  - SSID: `rasp_hotspot`
  - Password: `pass_1234`
- **ESP32 Hotspot (`esp32_hotspot`)**: Used in Architectures #3 and #4
  - SSID: `esp32_hotspot`
  - Password: `pass_1234`

---

## Architecture Overview & File Layouts

### Architecture #1: `RASP_HW_ESP32_C`
- **Topology**: The Raspberry Pi acts as the Wi-Fi Access Point (`rasp_hotspot`) and Flask Web Server host. The ESP32 connects to it as a network client (`STA_IF`), dynamically registering its IP address upon boot via `boot-sync`.
- **File Structure**:
  ```text
  RASP_HW_ESP32_C/
  ├── RASP/
  │   ├── app.py
  │   ├── static/
  │   │   ├── styles.css
  │   │   └── script.js
  │   └── templates/
  │       └── index.html
  └── ESP32/
      └── main.py
  ```

### Architecture #2: `RASP_H_ESP32_W` (Unused)
- **Topology**: The Raspberry Pi acts strictly as a Wi-Fi router hotspot (`H`), while the ESP32 hosts both the hardware and the web server (`W`). (Note: Bypassed in practice due to unnecessary Pi resource overhead and dynamic IP complexity).

### Architecture #3: `RASP_W_ESP32_H`
- **Topology**: The ESP32 broadcasts the Wi-Fi hotspot (`esp32_hotspot`) and handles physical hardware interrupts (GPIO 18, 19, 21). The Raspberry Pi connects to this hotspot as a client and runs the Flask web server (`app.py`), communicating with the ESP32 over local sockets.
- **File Structure**:
  ```text
  RASP_W_ESP32_H/
  ├── RASP/
  │   ├── app.py
  │   ├── static/
  │   │   ├── styles.css
  │   │   └── script.js
  │   └── templates/
  │       └── index.html
  └── ESP32/
      └── main.py
  ```

### Architecture #4: `RASP_C_ESP32_HW`
- **Topology**: The ESP32 does everything. It broadcasts the Wi-Fi hotspot (`esp32_hotspot`), stores and serves all static web files (`index.html`, `styles.css`, `script.js`) directly from its flash storage via a MicroPython socket server, and controls physical LEDs and buttons. The Raspberry Pi (along with PCs and phones) acts simply as a client.
- **File Structure**:
  ```text
  RASP_C_ESP32_HW/
  ├── RASP/
  │   └── none.txt (ignore file)
  └── ESP32/
      ├── main.py
      ├── templates/
      │   └── index.html
      └── static/
          ├── styles.css
          └── script.js
  ```

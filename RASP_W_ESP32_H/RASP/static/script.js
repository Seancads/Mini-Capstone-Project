let lastSeenEventId = 0;

let clientId = sessionStorage.getItem("iot_client_id");
if (!clientId) {
    clientId = 'DEV-' + Math.random().toString(36).substring(2, 8).toUpperCase();
    sessionStorage.setItem("iot_client_id", clientId);
}

window.onload = () => {
    fetch('/api/status')
        .then(res => res.json())
        .then(data => {
            updateButtonUI(18, data["18"]);
            updateButtonUI(19, data["19"]);
            showToast("Connected to IoT Hub", "info");
        })
        .catch(() => showToast("Connection failed", "warning"));

    setInterval(checkSystemEvents, 150);
};

function checkSystemEvents() {
    fetch('/api/latest-event')
        .then(res => res.json())
        .then(data => {
            if (data.id && data.id > lastSeenEventId) {
                lastSeenEventId = data.id;
                
                const timestamp = new Date().toLocaleTimeString();
                appendLogRow(timestamp, data.event, data.source, data.device_id || "SYSTEM", data.state);

                if (data.event.includes("Pin 18")) {
                    updateButtonUI(18, data.state);
                } else if (data.event.includes("Pin 19")) {
                    updateButtonUI(19, data.state);
                }
            }
        })
        .catch(err => console.error("Polling error:", err));
}

function toggleLED(pin) {
    const isMobile = /Mobi|Android/i.test(navigator.userAgent);
    const deviceType = isMobile ? "Mobile Web" : "PC Web";

    fetch(`/api/gpio${pin}/toggle`, {
        method: 'POST',
        headers: {
            'X-Device-Source': deviceType,
            'X-Device-ID': clientId
        }
    })
    .then(res => res.json())
    .then(data => {
        updateButtonUI(pin, data.state);
    })
    .catch(() => {
        showToast(`Failed to toggle Pin ${pin}`, "warning");
        const checkbox = document.getElementById(`toggle-${pin}`);
        checkbox.checked = !checkbox.checked;
    });
}

function updateButtonUI(pin, state) {
    const checkbox = document.getElementById(`toggle-${pin}`);
    const badge = document.getElementById(`status-${pin}`);
    if (!checkbox || !badge) return;
    
    badge.innerText = state;
    badge.className = `state-badge ${state.toLowerCase()}`;
    checkbox.checked = (state === "ON");
}

function appendLogRow(time, event, source, deviceId, state) {
    const tbody = document.getElementById('log-body');
    const emptyRow = tbody.querySelector('.empty-row');
    if (emptyRow) emptyRow.remove();

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${time}</td>
        <td>${event}</td>
        <td>${source}</td>
        <td>${deviceId}</td>
        <td><b>${state}</b></td>
    `;
    
    tbody.appendChild(tr);
    const container = document.querySelector('.table-container');
    container.scrollTop = container.scrollHeight;
}

function clearLogs() {
    const tbody = document.getElementById('log-body');
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">Log cleared. Waiting for events...</td></tr>';
}

function showToast(message, type = "info", duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    while (container.children.length >= 3) {
        container.firstChild.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        toast.addEventListener('animationend', () => toast.remove());
    }, duration);
}
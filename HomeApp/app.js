// espServer UI JavaScript (MQTT version)

// Import secrets from a separate file (make sure to serve as a module)
import { MQTT_BROKER, MQTT_USER, MQTT_PASS } from './mqtt_secrets.js';

// Spinner SVG for animation
const spinnerSVG = `<svg class="spin" width="18" height="18" viewBox="0 0 50 50" style="vertical-align:middle;">
  <circle cx="25" cy="25" r="20" fill="none" stroke="#00b894" stroke-width="5" stroke-linecap="round" stroke-dasharray="31.4 31.4" transform="rotate(-90 25 25)">
    <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.8s" repeatCount="indefinite"/>
  </circle>
</svg>`;

// Update connect button state only (not clickable)
function updateConnectBtn(state) {
    const btn = document.getElementById('connectBtn');
    if (!btn) return;
    btn.disabled = true;
    if (state === 'connecting') {
        btn.innerHTML = `${spinnerSVG} Connecting...`;
        btn.style.background = 'linear-gradient(90deg,#fdcb6e 60%,#ffeaa7 100%)';
    } else if (state === 'connected') {
        btn.textContent = 'Connected';
        btn.style.background = 'linear-gradient(90deg,#27ae60 60%,#00b894 100%)';
    } else {
        btn.textContent = 'Disconnected';
        btn.style.background = 'linear-gradient(90deg,#e17055 60%,#d63031 100%)';
    }
    // Also update the status label
    updateConnectionLabel(state === 'connected');
}

// Update connection label
function updateConnectionLabel(isConnected) {
    const label = document.getElementById('connectionStateLabel');
    if (label) {
        label.textContent = isConnected ? 'Connected' : 'Disconnected';
        label.style.color = isConnected ? '#27ae60' : '#e74c3c';
    }
    console.log('Connection label updated:', isConnected ? 'Connected' : 'Disconnected');
}

// Update relay state label
function updateRelayStateLabel(relay, state) {
    const label = document.getElementById(`relay${relay}StateLabel`);
    if (label) {
        label.textContent = state ? 'ON' : 'OFF';
        label.style.color = state ? '#27ae60' : '#e74c3c';
    }
}

// Update relay button
function updateRelayBtn(relay, state) {
    const btn = document.getElementById(`relay${relay}Btn`);
    if (btn) {
        btn.textContent = `Relay ${relay} Toggle (${state ? 'ON' : 'OFF'})`;
        btn.style.background = state ? 'linear-gradient(90deg,#27ae60 60%,#00b894 100%)' : '';
    }
    updateRelayStateLabel(relay, state);
    console.log(`Relay ${relay} button updated:`, state ? 'ON' : 'OFF');
}

// MQTT topics
const RELAY1_STATE_TOPIC = 'home/relay1/state';
const RELAY2_STATE_TOPIC = 'home/relay2/state';
const RELAY1_SET_TOPIC = 'home/relay1/set';
const RELAY2_SET_TOPIC = 'home/relay2/set';

// Check if mqtt is loaded
if (typeof mqtt === 'undefined') {
    console.error('MQTT.js is not loaded! Make sure <script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script> is included in your HTML.');
} else {
    console.log('MQTT.js loaded.');
}

// On page load, set connection label and button to disconnected
window.onload = function() {
    updateConnectBtn('disconnected');
    console.log('Window loaded, initial connection label set.');
};

// Connect to MQTT broker
updateConnectBtn('connecting');
const client = mqtt.connect(MQTT_BROKER, {
    username: MQTT_USER,
    password: MQTT_PASS,
    clean: true,
    connectTimeout: 4000,
    reconnectPeriod: 4000
});

client.on('connect', () => {
    console.log('MQTT connected!');
    client.subscribe([RELAY1_STATE_TOPIC, RELAY2_STATE_TOPIC], (err) => {
        if (err) {
            console.error('Subscription error:', err);
        } else {
            console.log('Subscribed to relay state topics.');
        }
    });
    updateConnectBtn('connected');
});

client.on('reconnect', () => {
    console.log('MQTT reconnecting...');
    updateConnectBtn('connecting');
});
client.on('offline', () => {
    console.log('MQTT offline.');
    updateConnectBtn('disconnected');
});
client.on('close', () => {
    console.log('MQTT connection closed.');
    updateConnectBtn('disconnected');
});
client.on('error', (err) => {
    console.error('MQTT error:', err);
    updateConnectBtn('disconnected');
});

// Handle incoming relay state messages
client.on('message', (topic, message) => {
    const msg = message.toString();
    console.log('MQTT message received:', topic, msg);
    if (topic === RELAY1_STATE_TOPIC) {
        updateRelayBtn(1, msg === 'ON');
    }
    if (topic === RELAY2_STATE_TOPIC) {
        updateRelayBtn(2, msg === 'ON');
    }
});

// Button handlers
document.getElementById('relay1Btn').onclick = function() {
    console.log('Relay 1 button clicked. Publishing TOGGLE.');
    client.publish(RELAY1_SET_TOPIC, 'TOGGLE');
};
document.getElementById('relay2Btn').onclick = function() {
    console.log('Relay 2 button clicked. Publishing TOGGLE.');
    client.publish(RELAY2_SET_TOPIC, 'TOGGLE');
};

import json
import queue
import threading
import os
import paho.mqtt.client as mqtt


# Single global MQTT client — imported by views, apps.py, etc.
_mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
_is_connected = False

# Thread-safe dictionary mapping topics -> list of active queues
_topic_listeners = {}
_lock = threading.Lock()


def subscribe_and_listen(topics) -> queue.Queue:
    """Subscribe to one or more MQTT topics and return a shared queue.

    ``topics`` can be a single topic string or a list of topic strings.
    If the broker is not connected the subscribe calls are skipped so the
    server can still start; the queue will simply never receive messages.
    """
    if isinstance(topics, str):
        topics = [topics]

    message_queue = queue.Queue()

    with _lock:
        for topic in topics:
            if topic not in _topic_listeners:
                _topic_listeners[topic] = []
            _topic_listeners[topic].append(message_queue)

    if _is_connected:
        for topic in topics:
            _mqtt_client.subscribe(topic)
    else:
        print(f"[MQTT] Skipping subscribe to {topics} broker not connected.")

    return message_queue



def unsubscribe_listeners(topic: str, message_queue: queue.Queue):
    """Clean up the queue after the view finishes execution."""
    with _lock:
        if topic in _topic_listeners and message_queue in _topic_listeners[topic]:
            _topic_listeners[topic].remove(message_queue)
            if not _topic_listeners[topic]:
                del _topic_listeners[topic]


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT] Connected: {reason_code}")


def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()
    with _lock:
        listeners = []

        for subscribed_topic, queue in _topic_listeners.items():
            if mqtt.topic_matches_sub(subscribed_topic, topic):
                listeners.extend(queue)

    for message_queue in listeners:
        message_queue.put(payload)


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f"[MQTT] Subscription acknowledged by broker for mid={mid}")


# Register MQTT Event Callbacks
_mqtt_client.on_connect = on_connect
_mqtt_client.on_message = on_message
_mqtt_client.on_subscribe = on_subscribe


# Public API
def get_mqtt_client() -> mqtt.Client:
    """Return the single global MQTT client (already connected & looping)."""
    return _mqtt_client


def start_mqtt():
    """Connect and start the background network loop.

    The MQTT broker address can be overridden with the ``MQTT_BROKER_HOST`` environment
    variable.  If the connection fails (e.g., the broker is unreachable), we log the
    error and continue without raising this allows the Django server to start even
    when MQTT is unavailable (useful for local development or CI environments).
    """
    global _is_connected
    if _is_connected:
        return

    # Resolve broker host – default to localhost for safety.
    broker_host = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))

    try:
        _mqtt_client.connect(broker_host, broker_port, keepalive=60)
    except Exception as exc:  # Catch timeout, socket errors, etc.
        print(f"[MQTT] Connection failed to {broker_host}:{broker_port} {exc}")
        print("[MQTT] Running without broker MQTT dependent features will be disabled.")
        _is_connected = False
        return

    _mqtt_client.loop_start()
    _is_connected = True
    print("[MQTT] Client started")
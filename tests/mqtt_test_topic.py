import paho.mqtt.client as mqttClient
from paho import mqtt
HOST = "33ea71e0e0034036b86bee133525b810.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "SmartGreenHouse"
PASSWORD = "SmartGreenHouse2025"

def on_connect(client, userdata, flags, rc, protperties=None):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, message):
    try:
        topic = message.topic
        payload = message.payload.decode("utf-8")
        print(f"Received message '{payload}' on topic '{topic}'")
    except Exception as e:
        print(f"Error processing message: {e} for topic: {message.topic}")


try:
    mqtt_client = mqttClient.Client(client_id="", protocol=mqttClient.MQTTv5)
    mqtt_client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    mqtt_client.username_pw_set(USERNAME, PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(HOST, PORT)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Error connecting to MQTT broker: {e}")
    exit(1)


# Subscribe to a topic
mqtt_client.subscribe("test/plant_growth", qos=1)

# import json
# json_str = json.dumps({
#     "size_compare": {
#         "current_day_px": 11550,
#         "growth": 5
#     },
#     "deasese_class": {
#         "id": 100,
#         "name": "Powdery mildew",
#     }
# })

# mqtt_client.publish("test/plant_growth", json_str, qos=1, retain=True)

while True:
    try:
        pass
    except KeyboardInterrupt:
        print("Exiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        break
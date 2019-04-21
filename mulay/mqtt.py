# import context
import paho.mqtt.client as mqtt

TOPIC='topic'
USER = 'user'
PASSWORD = 'password'
HOST = 'host'
PORT = 'port'

DEFAULT_PORT = 1883
DEFAULT_TOPIC = 'mulay'

class MQTTConfig(object):
    def __init__(self, config_dict):
        self.host = config_dict[HOST]
        self.port = config_dict.get(PORT) or DEFAULT_PORT
        self.topic = config_dict.get(TOPIC) or DEFAULT_TOPIC
        self.username = config_dict.get(USER) or ''
        self.password = config_dict.get(PASSWORD) or ''

class Relay(mqtt.Client):
    def __init__(self, config_dict, sender):
        super(Relay, self).__init__()
        self.config = MQTTConfig(config_dict)
        self.sender = sender
        self.connected = False
        self.subscribed = False
        if self.config.password is not None:
            self.username_pw_set(username=self.config.username,password=self.config.password)

    def on_connect(self, mqttc, obj, flags, rc):
        self.connected = True
        print(f"Connected: {str(rc)}")

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.subscribed = True
        print(f"Subscribed to: {str(mid)}")

    def on_log(self, mqttc, obj, level, string):
        print(f"MQTT:[{level}] {string}")

    def on_message(self, mqttc, obj, msg):
        # print(f"Message: {msg}")
        for line in msg.payload.splitlines():
            self.sender.send_raw(line)

    def start(self):
        print(f"Starting relay on: {self.config.host}:{self.config.port}")
        self.connect(self.config.host, self.config.port, 60)

        print(f"Subscribing to: {self.config.topic}")
        self.subscribe(self.config.topic, 0)
        self.loop_forever()

    def stop(self):
        if self.subscribed is True:
            self.unsubscribe(self.config.topic)

        if self.connected is True:
            self.disconnect()

class Sender(mqtt.Client):
    def __init__(self, config_dict):
        super(Sender, self).__init__()
        self.config = MQTTConfig(config_dict)
        self.connected = False
        if self.config.password is not None:
            self.username_pw_set(username=self.config.username,password=self.config.password)

    def __del__(self):
        super().__del__()

    def on_connect(self, mqttc, obj, flags, rc):
        self.connected = True
        print(f"Connected: {str(rc)}")

    def on_publish(self, mqttc, obj, mid):
        print(f"Published: {str(mid)}")

    def on_log(self, mqttc, obj, level, string):
        print(f"MQTT:[{level}] {string}")

    def start(self):
        self.connect(self.config.host, self.config.port, 60)
        self.loop_start()

    def stop(self):
        if self.connected is True:
            self.loop_stop()
            self.disconnect()

    def send_raw(self, text):
        message_info = self.publish(self.config.topic, text, qos=0)
        message_info.wait_for_publish()


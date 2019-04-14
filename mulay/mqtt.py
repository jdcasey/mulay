import context
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
		self.user = config_dict.get(USER) or ''
		self.password = config_dict.get(PASSWORD)

class Relay(mqtt.Client):
	def __init__(self, config_dict, sender):
		self.config = MQTTConfig(config_dict)
		self.sender = sender
		self.client = mqtt.Client()
		self.connected = False
		self.subscribed = False
		if self.password is not None:
			self.client.username_pw_set(username=self.config.username,password=self.config.password)

	def on_connect(self, mqttc, obj, flags, rc):
		self.connected = True
		print(f"Connected: {str(rc)}")

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		self.subscribed = True
		print(f"Subscribed to: {str(mid)}")

	def on_log(self, mqttc, obj, level, string):
		print(f"MQTT:[{level}] {string}")

	def on_message(self, mqttc, obj, msg):
		for line in msg.payload.splitlines():
			self.sender.send_raw(line)

	def start(self):
		self.client.connect(self.config.host, self.config.port, 60)

		self.client.subscribe(self.config.topic, 0)
		self.client.loop_forever()

	def stop(self):
		if self.subscribed is True:
			self.client.unsubscribe(self.config.topic)

		if self.connected is True:
			self.client.disconnect()

class Sender(mqtt.Client):
	def __init__(self, config_dict, sender):
		self.config = MQTTConfig(config_dict)
		self.sender = sender
		self.client = mqtt.Client()
		self.connected = False
		if self.password is not None:
			self.client.username_pw_set(username=self.config.username,password=self.config.password)

	def on_connect(self, mqttc, obj, flags, rc):
		self.connected = True
		print(f"Connected: {str(rc)}")

	def on_publish(self, mqttc, obj, mid):
		print(f"Published: {str(mid)}")

	def on_log(self, mqttc, obj, level, string):
		print(f"MQTT:[{level}] {string}")

	def start(self):
		self.client.connect(self.config.host, self.config.port, 60)
		self.client.loop_start()

	def stop(self):
		if self.connected is True:
			self.client.loop_stop()
			self.client.disconnect()

	def send_raw(self, text):
		self.client.publish(self.config.topic, text, qos=0)


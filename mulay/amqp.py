import pika
import time

URL = 'url'
QUEUE = 'queue'

DEFAULT_QUEUE = 'mulay'

class AMQPConfig(object):
    def __init__(self, config_dict):
        self.url = config_dict[URL]
        self.queue = config.get(QUEUE) or DEFAULT_QUEUE

class Relay(object):
    def __init__(self, config_dict, sender):
        self.config = AMQPConfig(config_dict)
        self.sender = sender

    def on_message(self, body):
        for line in body.splitlines():
            self.sender.send_raw(line)

    def start(self):
        params = pika.URLParameters(self.config.url)
        self.conn = pika.BlockingConnection(params)
        self.chan = self.conn.channel()

        self.chan.queue_declare(queue=self.config.queue)
        self.chan.basic_consume(self.config.queue, lambda _c, _m, _p, body: self.on_message(body), auto_ack=True)
        self.chan.start_consuming()

    def stop(self):
        self.chan.stop_consuming()
        self.conn.close()

class Sender(object):
    def __init__(self, config):
        self.config = AMQPConfig(config_dict)

    def start(self):
        params = pika.URLParameters(self.config.url)
        self.conn = pika.BlockingConnection(params)
        self.chan = self.conn.channel()

    def stop(self):
        self.conn.close()

    def send_raw(self, body):
        self.chan.basic_publish(exchange='', routing_key=self.config.queue, body=body)


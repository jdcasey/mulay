import socket

HOST='host'
PORT='port'

DEFAULT_PORT=2023

class CarbonConfig(object):
    def __init__(self, config_dict):
        self.host = config_dict[HOST]
        self.port = config_dict.get(PORT) or DEFAULT_PORT

class Sender(object):
    def __init__(self, config_dict):
        """Initialize a new Carbon sender that will use the plaintext protocol for sending metrics"""
        self.config = CarbonConfig(config_dict)

    def start(self):
        self.sock = socket.socket()
        conn_info = (self.config.host, self.config.port)
        try:
            print("Connecting to: %s:%d" % conn_info)
            self.sock.connect(conn_info)
        except socket.error:
            raise SystemExit("Couldn't connect to %s:%d, is carbon-cache.py running?" % conn_info)

    def stop(self):
        """If a socket is open for sending data at the time when the user kills this script, try to close it 
        gracefully.
        """
        if self.sock is not None:
            print("Attempting to close socket.")
            self.sock.close()
            self.sock = None

    def send_metrics(self, metrics):
        """Serialize the metrics dict (of the form k:v without timestamps) along with a generated timestamp into a
        multi-line payload. Then, send it over a new socket to the Carbon daemon.
        """
        for line in metrics:
            print("Sending:\n%s\n" % line)
            send_raw(line)

    def send_raw(self, line):
        try:
            self.sock.send((line + "\n").encode())
        except socket.error:
            self.stop()
            self.start()


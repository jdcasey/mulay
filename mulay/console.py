class Sender(object):
    def __init__(self, config_dict):
        print("Console Sender Initialized")

    def start(self):
        print("Console Sender Started")

    def stop(self):
        print("Console Sender Stopped")

    def send_raw(self, text):
        print(text)

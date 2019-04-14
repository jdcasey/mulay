import slackclient as client
import time

def find_channel_id(slack, name):
    """Allow a user to configure this system using a user-friendly channel name.
    The network handlers will use this method to map that to a channel ID.
    """
    result = slack.api_call("channels.list", exclude_members=True)
    for channel in result['channels']:
        if channel['name'] == name:
            return channel['id']

        prev_names = channel.get('previous_names')
        if prev_names is not None and name in prev_names:
            return channel['id']

    return None

class SlackConfig(object):
    def __init__(self, config_dict):
        self.token = config_dict[TOKEN]
        self.channel = config_dict[CHANNEL]

class Relay(object):
    def __init__(self, config_dict, sender, last_message=0):
        """Initialize the Relay using a config dict and an optional last-message timestamp (in unix seconds).
        """
        self.config = SlackConfig(config_dict)
        self.slack = client.SlackClient(self.config.token)
        self.sender = sender

        self.channel_id = find_channel_id(self.slack, self.config.channel)
        if self.channel_id is not None:
            self.slack.api_call('channels.join', channel=self.channel_id)

        self.last_message = last_message

    def stop(self):
        print("Stopped Slack relay")

    def _get_messages(self):
        """Receive any available messages on the Slack channel, and update the last-message timestamp
        appropriately before returning the array of message objects.
        """
        result = self.slack.api_call('channels.history', channel=self.channel_id, oldest=self.last_message)
        self.last_message=int(time.time())

        messages = result.get('messages') or []
        messages = messages[::-1]

        return messages

    def _ack_messages(self, messages_ts):
        """Acknowledge that processing is complete for an array of messages (given by their 'ts' values in messages_ts).
        This acknowledgement happens by way of deleting the messages out of the channel to prevent duplicate processing.
        """
        if messages_ts is not None:
            for ts in messages_ts:
                self.slack.api_call('chat.delete', channel=self.channel_id, ts=ts)

    def start(self):
        """Receive any available messages from the Slack channel and assume they are metrics triplets (key, value, tstamp).
        Messages can be multi-line, with a triplet per line. For each message that we can parse in this way,
        add the message 'ts' value to an acks array, which will be used to delete those messages from the 
        Slack channel to reduce the possibility of duplicate processing.

        For each triplet we can parse, send a new metric data point over a socket that we open to the Carbon
        daemon for this purpose, using newline-delimited plaintext.
        """
        while True:
            messages = self._get_messages()
            if len(messages) > 0:
                acks = []
                metrics = []
                for m in messages:
                    lines = [l.rstrip() for l in m['text'].splitlines()]
                    for line in lines:
                        parts = line.split(' ')
                        if len(parts) < 3:
                            continue

                        metrics.append("%s %s %s\n" % (parts[0], parts[1], parts[2]))
                    acks.append(m['ts'])

                if len(acks) > 0:
                    for m in metrics:
                        self.sender.send_raw(m)
                    self._ack_messages(acks)

            time.sleep(10)


class Explorer(object):
    def __init__(self, config_dict, last_message=0):
        """Construct a new Slack channel message receiver using the given configuration dict and an
        optional last-message timestamp (unix seconds).
        """
        self.config = SlackConfig(config_dict)
        self.slack = client.SlackClient(self.config.token)

        self.channel_id = find_channel_id(self.slack, self.config.channel)
        if self.channel_id is not None:
            self.slack.api_call('channels.join', channel=self.channel_id)

    def list_channels(self):
        """List the available Slack channels."""
        result = self.slack.api_call("channels.list")
        return [channel for channel in result['channels']]

    def find_user(self, user_id):
        """Lookup the user information for the given user id. Things like username will be available this way.
        """
        result = self.slack.api_call('users.info', user=user_id, include_locale=False)
        return result.get('user')

class Sender(object):
    def __init__(self, config_dict):
        """Construct a new Slack channel message sender using the given configuration dict to specify a token and 
        channel name.
        """
        self.config = SlackConfig(config_dict)

    def start(self):
        self.slack = client.SlackClient(self.config.token)

        self.channel_id = find_channel_id(self.slack, self.config.channel)
        if self.channel_id is not None:
            self.slack.api_call('channels.join', channel=self.channel_id)

    def stop(self):
        print("Stopped Slack sender")

    def send_metrics(self, metrics):
        """Serialize the given metrics dict (assumed to be key:value pairs without timestamps) to triplets in a 
        multi-line message, using a timestamp generated in this method. Once the message is formatted, send it to 
        the configured Slack channel.
        """
        now = int(time.time())

        lines = []
        for k in metrics.keys():
            v = metrics[k]
            lines.append("%s %s %s" % (k, v, now))

        self.send_raw("\n".join(lines))

    def send_raw(self, message):
        """Send a simple string message to the configured Slack channel."""
        return self.slack.api_call('chat.postMessage', channel=self.channel_id, text=message)

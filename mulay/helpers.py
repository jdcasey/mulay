import time

def send_metrics(sender, metrics):
    """Serialize the given metrics dict (assumed to be key:value pairs without timestamps) to triplets in a 
    multi-line message, using a timestamp generated in this method. Once the message is formatted, send it to 
    the configured Slack channel.
    """
    now = int(time.time())

    lines = []
    for k in metrics.keys():
        v = metrics[k]
        lines.append(f"{k} {v} {now}")

    sender.send_raw("\n".join(lines))

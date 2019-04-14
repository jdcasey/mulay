from ruamel.yaml import YAML

def load(config_path):
    """Load a Carbon-AMQP relay configuration from a YAML file (by default, use /etc/carbon-amqp.yml)"""
    data = {}

    with open(config_path) as f:
        data = YAML().load(f)

    return data



mu Relay (mulay) Library for Python
========================================

This library's main purpose is to establish a common framework for relaying messages from one bus to another, or to some message consumer (such as Carbon / GraphiteDB). It currently includes support for MQTT, AMQP, and for using a Slack channel as a poor man's message bus. 

Basic Architecture
------------------

You can configure this library pretty much any way you want. Each Sender or Relay class expects a configuration dict with relevant details for connecting. Relays also expect a Sender object, which allows you to pair any receiver type (implemented in the Relay) to any type of Sender. Since each class only expects a dict for configuration, it's possible to bridge two buses of the same protocol together using different configuration dicts, or subsections of the same larger configuration.

Example: Relay MQTT to Carbon (GraphiteDB)
------------------------------------------

We can use the MQTT Relay class with the Carbon Sender class to relay between a public MQTT server and a GraphiteDB server without exposing the GraphiteDB server to the internet. First, the configuration, which we could conveniently store in a YAML file::

	carbon:
		host: my.graphitedb.home.net
		port: 2023
	mqtt:
		host: m16.cloudmqtt.com
		port: 20996
		user: <some-user>
		password: <some-password>

Then, in our code we start a sender for Carbon, and a relay for MQTT with the sender as a parameter::

	from mulay.carbon import PlaintextSender
	from mulay.mqtt import Relay

	sender = PlaintextSender(config['carbon'])
	relay = Relay(config['mqtt'], sender)

    try:
		sender.start()

		# Relay will loop forever
		relay.start()
	except KeyboardInterrupt:
		relay.stop()
		sender.stop()

Example: Relay MQTT to Carbon (GraphiteDB)
------------------------------------------

Or, we could opt to use an AMQP service, by specifying the AMQP Relay class with the Carbon Sender class. Again, this will not expose the GraphiteDB server to the internet. First, the configuration, which we could conveniently store in a YAML file::

	carbon:
		host: my.graphitedb.home.net
		port: 2023
	amqp:
		url: amqp://<amqp-user>:<amqp-password>@wombat.rmq.cloudamqp.com/<amqp-instance>
		queue: my-metrics

Then, in our code we start a sender for Carbon, and a relay for MQTT with the sender as a parameter::

	from mulay.carbon import PlaintextSender
	from mulay.amqp import Relay

	sender = PlaintextSender(config['carbon'])
	relay = Relay(config['amqp'], sender)

    try:
		sender.start()

		# Relay will loop forever
		relay.start()
	except KeyboardInterrupt:
		relay.stop()
		sender.stop()

Example: Relay Slack to Carbon (GraphiteDB)
-------------------------------------------

We can even use Slack in much the same way as MQTT or AMQP, with the Carbon Sender class. First, the configuration, which we could conveniently store in a YAML file::

	carbon:
		host: my.graphitedb.home.net
		port: 2023
	slack:
		token: <your-token-here>
		channel: my-metrics

Then, in our code we start a sender for Carbon, and a relay for Slack with the sender as a parameter::

	from mulay.carbon import PlaintextSender
	from mulay.slack import Relay

	sender = PlaintextSender(config['carbon'])
	relay = Relay(config['slack'], sender)

    try:
		sender.start()

		# Relay will loop forever
		relay.start()
	except KeyboardInterrupt:
		relay.stop()
		sender.stop()

Example: Publishing to MQTT
---------------------------

As a convenience, and to make the relay functions truly flexible, mulay provides a Sender class with all of the protocol implementations. This is to allow bridging from any protocol to any other protocol that's supported by the library, but it's also useful for publishing into a public bus some data that will eventually get routed into your internal consumer server (such as GraphiteDB). This only requires configuration for the public bus, which makes it simpler than a relay configuration::

	host: m16.cloudmqtt.com
	port: 20996
	user: <some-user>
	password: <some-password>

Then, in our code, we setup a loop to take measurements and publish them::

	from mulay.mqtt import Sender
	import time
	import speedtest as st

	sender = Sender(config)
	sender.start()

    test = st.Speedtest()
    test.get_best_server()

    try:
	    while True:
		    test.download()
		    test.upload()

		    result = test.results.dict()

		    now = int(time.time())

		    sender.send_raw(f"my.speedtest.download {result['download']} {now}")
		    sender.send_raw(f"my.speedtest.upload {result['upload']} {now}")

		    time.sleep(30) # check this at most every 30 seconds
	except KeyboardInterrupt:
		sender.stop()

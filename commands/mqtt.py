import time
from paho.mqtt.client import Client, MQTT_ERR_SUCCESS


class Command(object):
    user_data = {
        "messages_received": 0,
        "data": {}
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.get_config(__name__)

    def on_message(self, client, userdata, message):
        userdata["messages_received"] += 1
        userdata["data"][message.topic] = message.payload

    def execute(self, chat_id, args):
        client = Client(userdata=self.user_data)

        connect_result = client.connect(self.config["mqtt_server"])
        if not connect_result == MQTT_ERR_SUCCESS:
            raise Exception("Client connection error {}".format(connect_result))

        topics = self.config["topics"].keys()

        for topic in topics:
            (subs_result, subs_id) = client.subscribe(topic)

        client.on_message = self.on_message
        if not subs_result == MQTT_ERR_SUCCESS:
            raise Exception("Subscription error {}".format(subs_result))

        time_start = time.time()
        while True:
            client.loop()

            if self.user_data["messages_received"] >= len(topics):
                break

            if time.time() - time_start > 10:
                break

        for topic in topics:
            if topic in self.user_data["data"]:
                topic_label = self.config["topics"][topic]
                topic_value = self.user_data["data"][topic]
                message = u"{}: {}".format(
                    topic_label, topic_value)
                self.bot.sendMessage(
                    chat_id,
                    message.encode("utf-8"))

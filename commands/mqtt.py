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

    def get_topic_list(self, root=None):
        topics = []
        root = root or self.config["data"]
        for key, value in root.items():
            if hasattr(value, "items"):
                sub_topics = self.get_topic_list(root=value)
                topics.extend(sub_topics)
            else:
                if type(value) == list:
                    topic = value[0]
                else:
                    topic = value
                topics.append(topic)
        return topics

    def format_output(self, root=None, level=0):
        output = ""
        root = root or self.config["data"]
        indent = " " * self.config["indent_size"]

        for label, item in root.items():
            if hasattr(item, "items"):
                output += "{}{}\n".format(indent*level, label)
                output += self.format_output(item, level+1)
            else:
                if type(item) == list:
                    topic, units = item
                else:
                    topic = item
                    units = ""

                value = self.user_data["data"].get(topic)
                output += "{}{}:{}{}{}\n".format(
                    indent*level, label, indent, value, units)
        return output

    def execute(self, chat_id, args):
        client = Client(userdata=self.user_data)

        connect_result = client.connect(self.config["server"])
        if not connect_result == MQTT_ERR_SUCCESS:
            raise Exception("Client connection error {}".format(connect_result))

        topics = self.get_topic_list()
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

        self.bot.sendMessage(
            chat_id,
            self.format_output())

# -*- coding: utf-8 -*-
import json
import re
import sys
import time

import telepot
from telepot.loop import MessageLoop

from paho.mqtt.client import Client, MQTT_ERR_SUCCESS

reload(sys)
sys.setdefaultencoding('utf-8')


class Butler(telepot.Bot):
    def __init__(self, *args, **kwargs):
        with open("config/main.json", "r") as config_file:
            self.config = json.load(config_file)

        return super(Butler, self).__init__(
            self.config["token"], *args, **kwargs)
        
    def parse_commands(self, msg):
        entities = msg.get("entities", [])

        commands = []
        msg_text = msg["text"]
        end = len(msg_text)
        prev_command = None

        for entity in entities:
            offset = entity.get("offset")
            length = entity.get("length")

            if prev_command:
                prev_command["args"] = msg_text[
                    prev_command["_args_start"]:offset]

            if entity["type"] == "bot_command":
                args_start = offset+length
                command = {
                    "_args_start": args_start,
                    "command": msg_text[offset:args_start].lstrip("/"),
                    "args": msg_text[offset+length:],
                }
                commands.append(command)
                prev_command = command
        
        return commands

    def handle_command(self, chat_id, command):
        cmd_name = command["command"]

        attr = getattr(self, "handle_cmd_{}".format(cmd_name), None)
        if callable(attr):
            attr(chat_id, command["args"])
        else:
            self.sendMessage(
                chat_id,
                u"unknown command `{command[command]}` with argument "
                "string `{command[args]}`".format(
                    command=command))

    def handle_cmd_temp(self, chat_id, args):
        with open("temperature_config.json", "r") as config_file:
            config = json.load(config_file)


        def on_message(client, userdata, message):
            userdata["messages_received"] += 1
            userdata["data"][message.topic] = message.payload

        user_data = {
            "messages_received": 0,
            "data": {}
        }
        client = Client(userdata=user_data)
        connect_result = client.connect(config["mqtt_server"])
        if not connect_result == MQTT_ERR_SUCCESS:
            raise Exception("Client connection error {}".format(connect_result))

        topics = config["topics"].keys()

        for topic in topics:
            (subs_result, subs_id) = client.subscribe(topic)

        client.on_message = on_message
        if not subs_result == MQTT_ERR_SUCCESS:
            raise Exception("Subscription error {}".format(subs_result))

        time_start = time.time()
        while True:
            client.loop()

            if user_data["messages_received"] >= len(topics):
                break

            if time.time() - time_start > 10:
                break

        for topic in topics:
            if topic in user_data["data"]:
                topic_label = config["topics"][topic]
                topic_value = user_data["data"][topic]
                message = u"{}: {}".format(
                    topic_label, topic_value)
                print message
                self.sendMessage(
                    chat_id,
                    message.encode("utf-8"))
        
        
    def handle(self, msg):
        flavor = telepot.flavor(msg)

        msg_type, chat_type, chat_id = telepot.glance(msg, flavor=flavor)
        print msg_type
        if msg_type == "text":
            commands = self.parse_commands(msg)
            if commands:
                for command in commands:
                    self.handle_command(chat_id, command)
            else:
                print json.dumps(msg)


bot = Butler()

MessageLoop(bot).run_as_thread()


print 'Listening ...'

# Keep the program running.
while 1:
    time.sleep(10)

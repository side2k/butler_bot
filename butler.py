# -*- coding: utf-8 -*-
from importlib import import_module
import json
import re
import sys
import time

import telepot
from telepot.loop import MessageLoop


reload(sys)
sys.setdefaultencoding('utf-8')


class Butler(telepot.Bot):
    def __init__(self, *args, **kwargs):
        self.config = self.get_config()

        return super(Butler, self).__init__(
            self.config["token"], *args, **kwargs)

    def get_config(self, config_name="main"):
        try:
            with open("config/{}.json".format(config_name), "r") as config_file:
                return json.load(config_file)
        except IOError:
            return None
        
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
        cmd_name = command["command"].strip(".")

        try:
            module = import_module(".{}".format(cmd_name), "commands")
        except ImportError:
            module = None

        if module:
            command = module.Command(self)
            command.execute(chat_id, command)
        else:
            self.sendMessage(
                chat_id,
                u"unknown command `{command[command]}` with argument "
                "string `{command[args]}`".format(
                    command=command))

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


# Keep the program running.
while 1:
    time.sleep(10)

#!/usr/bin/env python3
import os
import sys
import time
import random
import time
from dataclasses import dataclass
from paho.mqtt import client as paho
import json
import uuid
import argparse
import mqtt_util
from loguru import logger

logger.add(sys.stdout,
           format="{time} {message}",
           filter="client",
           level="DEBUG")

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

class MsgBuilder:

    def __init__(self, msg_tpl = ""):
        self._data = {}
        if msg_tpl:
            self._data = json.loads(msg_tpl)
        self._seq = 0

    def sender(self, sender):
        self._data["from"] = sender
        return self

    def receiver(self, receiver):
        self._data["to"] = receiver
        return self

    def command(self, cmd):
        self._data["command"] = cmd
        return self

    def seq(self, seqNum=0):
        if not seqNum:
            self._seq += 1
            self._data["seq"] = self._seq
        else:
            self._data["seq"] = seqNum
        return self

    def time(self, timestamp=0):
        if not timestamp:
            self._data["time"] = int(time.time() * 1000)
        else:
            self._data["time"] = timestamp
        return self

    def set_track_id(self, track_id):
        self._data[track_id] = track_id
        return self

    def set_field(self, field_name, field_value):
        self._data[field_name] = field_value
        return self
    
    def get_field(self, field_name):
        return self._data.get(field_name)
    
    def build(self):
        return json.dumps(self._data)

@dataclass
class MqttConfig:
    broker: str = 'localhost'
    port: int = 1883
    username: str = 'admin'
    password: str = 'public'

def read_mqtt_config(config_dict):
    cfg = MqttConfig()
    cfg.broker = config_dict.get("broker")
    cfg.port = config_dict.get("port")
    cfg.username = config_dict.get("username")
    cfg.password = config_dict.get("password")
    return cfg

class MqttClient:

    def __init__(self, mqttConfig):
        self._mqtt_config = mqttConfig
        # Generate a Client ID with the subscribe prefix.
        self._connected = False
        self._started = False
        self._client = None
        self._messages = []

    def connect(self):
        if self._connected:
            return
        self._client_id = f'client-{random.randint(0, 10000)}'
        self._client = paho.Client(self._client_id)
        self._client.username_pw_set(self._mqtt_config.username, self._mqtt_config.password)
        self._client.on_connect = self.on_connect
        self._client.connect(self._mqtt_config.broker, self._mqtt_config.port)
        self.start()
        print(f"connect {self._mqtt_config} ...")
        return self._client

    def disconnect(self):
        if not self._client:
            print("Error: have not connected broker")
            return
        self.stop()
        self._client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            if not self._connected:
                print(f"Connected to MQTT Broker: {str(self._mqtt_config)}")
                self._connected = True
        else:
            print("Failed to connect, return_code={}".format(rc))
            self._connected = False

    def is_connected(self):
        return self._connected
    
    def clear_message(self):
        self._messages.clear()

    def get_messages(self):
        return self._messages

    def message_count(self):
        return len(self._messages)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        self._messages.append(payload)
        logger.debug(f"Received `{payload}` from `{msg.topic}` topic, count={len(self._messages)}")
        
    def start(self):
        if not self._started:
            self._client.loop_start()
            self._started = True

    def stop(self):
        if self._started:
            self._client.loop_stop()
            self._started = False

    def publish(self, topic, msg, retry_count = 3):
        if not self._client:
            print("Error: have not connected broker")
            return
        
        self.start()
        msg_count = 1
        
        while True:
            result = self._client.publish(topic, msg, 1, True)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Sent `{msg}` to topic `{topic}`")
                break
            else:
                print(f"Failed to send message to topic {topic}")
                msg_count += 1
                if msg_count > retry_count:
                    break
        

    def subscribe(self, topic, timeout=0, msg_cb=None):
        if not self._client:
            print("Error: have not connected broker")
            return
        
        self.start()

        self._client.subscribe(topic)
        if msg_cb:
            self._client.on_message = msg_cb
        else:    
            self._client.on_message = self.on_message
            
def example():
    str = './mqtt_client.py -a <sub|pub> -b <broker_address>  [-p <port> -u <username> -s <password>] -t <topic> -m <message>\n'
    str += ('e.g. ./mqtt_client.py -b localhost -a pub -t "/waltertest/req" -m "hello"\n')
    str += ('     ./mqtt_client.py -b localhost -a sub -t "/waltertest/#"')
    return str

if __name__ == '__main__':

    parser = argparse.ArgumentParser(usage=example())
    parser.add_argument('--action','-a', required=True, action='store', dest='action', help='specify action: pub|sub|test')
    parser.add_argument('--broker','-b', action='store', dest='broker', help='specify the broker address')
    parser.add_argument('--port', '-p', type=int, action='store', dest='port', help='specify the broker port', default=1883)
    parser.add_argument('-u', action='store', dest='username', help='specify a username')
    parser.add_argument('-s', action='store', dest='password', help='specify a password')
    parser.add_argument('-m', action='store', dest='command', help='specify a command')
    parser.add_argument('-t', action='store', dest='topic', help='specify a topic', default="req")
    parser.add_argument('-n', type=int, action='store', dest='sequence', help='specify a sequence', default=1)
    args = parser.parse_args()

    mqtt_config = MqttConfig()
    if args.broker:
        mqtt_config.broker = args.broker
    if args.port:
        mqtt_config.port = args.port
    if args.username:
        mqtt_config.username = args.username
    if args.password:
        mqtt_config.password = args.password

    client = MqttClient(mqtt_config)

    default_cmd = {
        "from": "alice",
        "to": "bob"
    }
    builder = MsgBuilder(json.dumps(default_cmd)).time().seq(args.sequence).command(args.command)
    builder.set_field("track_id", str(uuid.uuid4()))
    default_msg = builder.build()

    client.connect()
    ret = mqtt_util.wait_until(lambda: client.is_connected(), 10)

    if  not ret:
        print("Error: connect to broker failed")
        exit(-1)
    if args.action == 'sub':
        client.subscribe(args.topic, 10)
        mqtt_util.wait_until(lambda: client.message_count() > 0, 10)
    elif args.action == "pub":
        msg = MsgBuilder(default_msg).time().seq(args.sequence).build()
        client.publish(args.topic, msg)
    else:
        print(example())
        

    client.disconnect()


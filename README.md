# MQTT Client

It is a mqtt client based python paho-mqtt library

## Usage
* setup environment

```sh
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

* usage: 

```sh
./mqtt_client.py -a <sub|pub> -b <broker_address>  [-p <port> -u <username> -s <password>] -t <topic> -m <message>
```

* example

```sh
./mqtt_client.py -b localhost -a pub -t "/waltertest/req" -m "hello"

./mqtt_client.py -b localhost -a sub -t "/waltertest/#"

```

such as:

```sh
% ./mqtt_client.py -b localhost -a pub -t "/waltertest/req" -m "hello"
connect MqttConfig(broker='localhost', port=1883, username='admin', password='public') ...
.Connected to MQTT Broker: MqttConfig(broker='localhost', port=1883, username='admin', password='public')
Sent `{"from": "alice", "to": "bob", "time": 1711119463945, "seq": 1, "command": "hello", "track_id": "aec893b5-8d12-4640-a336-59e107bbe4a8"}` to topic `/waltertest/req`

% ./mqtt_client.py -b localhost -a sub -t "/waltertest/#"
connect MqttConfig(broker='localhost', port=1883, username='admin', password='public') ...
.Connected to MQTT Broker: MqttConfig(broker='localhost', port=1883, username='admin', password='public')
.2024-03-22 22:57:51.428 | DEBUG    | __main__:on_message:139 - Received `{"from": "alice", "to": "bob", "time": 1711119463945, "seq": 1, "command": "hello", "track_id": "aec893b5-8d12-4640-a336-59e107bbe4a8"}` from `/waltertest/req` topic, count=1
```
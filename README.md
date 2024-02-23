# Beekeeper System

<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/1971/1971350.png" alt="canva-logo" height="64px"/>
</p>

The aim of the project is to integrate the modern Internet of Things technologies with beekeeping. In general, bee colonies are organized into hives. For the colony to be healthy, attention must be paid to the conditions inside the hive, such as **humidity**, **temperature** and the **ratio** of **carbon dioxide** to **oxygen**. So being aware of these data can be very useful for the beekeeper, who can possibly intervene to help the colony.

One of the events that the beekeeper must be careful about is swarming, which is the possibility that the colony may decide to leave the hive. For this purpose, **frequency** and **noise** within the hive are factors that can be exploited by the beekeeper to prevent such an event. 

Another interesting metric to monitor is the **number** of **bees leaving** and **entering** the hive. This value indicates the mortality rate of a colony, which can be influenced by the use of insecticides in the area or the presence of varrosis in the colony. 

Finally, knowing the **weight** of the hive provides insight into how much honey is imported daily and whether new frames need to be inserted. In addition, weight is an index to understand the space available in the hive. If this is too low, the queen may decide not to lay eggs and the bees may stop collecting honey.

Bees are autonomous, but it is possible to help them in their growth and honey production by acting on the levels of temperature, humidity and ratio of carbon dioxide to oxygen. To achieve this, a **heating system** is used to warm the hive while a **ventilation system** is used to lower the temperature, humidity and amount of carbon dioxide. The beekeeper must be able to decide how the values measured by the sensors are to be used to control the implementation systems independently, according to his or her preferences.

## How to Run

The project consists of
* `Remote control application`
* `Cloud application`
* `MQTT broker`
* `MQTT sensors`
* `CoAP actuators`
* `RPL border router`

The `remote control application` is used by the beekeepers to manage their apiaries. To run it: 
```[bash]
cd src/remote-control-application
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 remote_control_application.py
```

The main purpose of the `cloud application` is to collect data from the low power and lossy network. It acts as **MQTT client** and as **CoAP server**. To run it: 
```[bash]
cd src/cloud-application
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 cloud_application.py
```

In order to use the MQTT protocol in the network, a `broker` is needed. The chosen one is **Mosquitto**:
```[bash]
mosquitto -c /etc/mosquitto/mosquitto.conf
```

You need mosquitto to be enabled to use **IPv6**. To achieve this, the following lines must be added to the configuration file:
```
allow_anonymous true
listener 1883 fd00::1
```

The `MQTT sensor` is a node that periodically collects several values from the surrounding environment. These data are encapsulated in an **MQTT packet** and transmitted to the cloud application through the **broker**. To flash the code on the nRF52840 dongle:
```[bash]
cd src/mqtt-sensor/
make TARGET=nrf52840 BOARD=dongle DEFINES=[sensor_type] mqtt-sensor.dfu-upload PORT=/dev/[dongle_port]
```

The `CoAP actuator` is a node that executes commands received from the remote control application. These commands are sent through a **CoAP request**. To flash the code on the nRF52840 dongle:
```[bash]
cd src/coap-actuator/
make TARGET=nrf52840 BOARD=dongle DEFINES=[actuator_type] coap-actuator.dfu-upload PORT=/dev/[dongle_port]
```

Finally, in order to allow sensors and actuators from the low power and lossy network to communicate with the applications, an `RPL border router` is needed. To flash the code on the nRF52840 dongle:
```[bash]
cd src/rpl-border-router/
make TARGET=nrf52840 BOARD=dongle border-router.dfu-upload PORT=/dev/[dongle_port]
make TARGET=nrf52840 BOARD=dongle PORT=/dev/[dongle_port] connect-router
```

## Authors

* [Biagio Cornacchia](https://github.com/biagiocornacchia)
* [Matteo Abaterusso](https://github.com/MatteoAba)
#!/usr/bin/env python

import protocol
import mqttThread
import common

import datetime
import httplib2
import json
import logging
import serial
import sys
import time
import traceback


# create logger with 'spam_application'
logger = logging.getLogger('serial_gateway')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)




httplib2.debuglevel     = 0
http                    = httplib2.Http()
content_type_header     = "application/json"
headers = {'Content-type': 'application/json'}
baseUrl                 = common.Config.getRestServerAddress()+":"+str(common.Config.getRestServerPort())+"/sensorinos/"

gateway=None


class SerialGateway:

    linuxPossibleSerialPorts=['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2',
    '/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
    '/dev/ttyS0','/dev/ttyS1',
    '/dev/ttyS2','/dev/ttyS3'] # TODO : complete list

    windowsPossibleSerialPorts=['\\.\COM1', '\\.\COM2', '\\.\COM3', '\\.\COM4'] # TODO : complete list

    @staticmethod
    def on_subscribe(mosq, obj, mid, qos_list):
        logger.debug("Subscribe with mid "+str(mid)+" received.")

    @staticmethod
    def on_connect(mosq, obj, rc):
        if rc == 0:
            logger.debug("Connected successfully.")

    @staticmethod
    def on_mqtt_message(mqtt, obj, msg):
        print mqtt
        """main server sends message on mosquitto"""
        logger.debug("msg from mosquitto: "+str(msg))
        if("commands" == msg.topic):
            try:
                command=json.dumps(msg.payload)
                if("set" in command):
                    gateway.writeOnSerial(json.dumps(command))
                elif("request" in command):
                    gateway.writeOnSerial(json.dumps(command))
                else:
                    logger.warn("unhandled message from mqtt: "+json.dumps(command))
            except:
                logger.debug("failed to decode "+msg.payload)

        elif ("serialOut" == msg.topic):
            gateway.processMessage(msg.payload)
        else:
            logger.warn("unknown mqtt channel")


    def __init__(self, portFile=None):
        self.protocol=protocol.Protocol()
        self.mqtt=None
        self.portFile=portFile
        self.port=None


    def setSerialPort(self, port):
        self.port=port

    def writeOnSerial(self, msg):
        gateway.port.write(msg)
        self.mqtt.mqttc.publish("serialOut", msg)

    def startSerial(self):
        if self.port==None:
            if self.portFile==None:
                logger.debug("no portFile was specified, scan for a valid serial")
                for device in SerialGateway.linuxPossibleSerialPorts:
                    try:
                        self.port = serial.Serial(device, 115200)
                        logger.debug("opened serial port (hopefully it's the base): "+device)
                        logger.debug("you can specify port on command line next time")
                        break
                    except:
                        logger.debug("no serial/arduino on "+device)
            else:
                self.port = serial.Serial(port, 57600)


    def startMqtt(self):
        self.mqtt=mqttThread.MqttThread()
        self.mqtt.mqttc.on_connect = self.on_connect
        self.mqtt.mqttc.on_subscribe = self.on_subscribe
        self.mqtt.mqttc.on_message= self.on_mqtt_message
        self.mqtt.start()
        time.sleep(1)
        self.mqtt.mqttc.subscribe("commands", 0)
        self.mqtt.mqttc.subscribe("serialOut", 0)


    def start(self):
        self.startMqtt()
        self.startSerial()
        while True:
            msg=self.port.readline()
            self.mqtt.mqttc.publish("serialIn",  msg)
            self.processMessage(msg)


    def processMessage(self, msg):
        if self.protocol.treatMessage(msg):
            print "message ok: "+msg
        else:
            print "message ko: "+msg
       


class FakeSerial:
    
    currentMessage=0   
    messages=[

        ## publish

        #service list from sensorino with address 10
        { "from": 10, "to": 0, "type": "publish", "serviceId": [ 0, 1 ] },
        # service dataType / description from a service 1 on sensorino with address 10
        { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "dataType": "switch", "count": [ 0, 1 ] },
        # publish from a service 1 of type switch on sensorino with address 10
        { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "switch": False },

        ## request 

        # base ask service list to service manager service on sensorino with address 10        
        { "from": 0, "to": 10, "type": "request", "serviceId": 0 },
        # base ask service description of service 1 on sensorino with address 10
        { "from": 0, "to": 10, "type": "request", "serviceId": 1, "dataType": "dataType" },
        # base ask service 1 on sensorino with address 10 to publish
        { "from": 0, "to": 10, "type": "request", "serviceId": 1, "dataType": "switch" },

        ## set
        # base set service 1 on sensorino with address 10 switch state to True
        { "from": 0, "to": 10, "type": "set", "serviceId": 1, "switch": True }

    ]


    def __init__(self):
        pass

    def readline(self):
        FakeSerial.currentMessage=FakeSerial.currentMessage+1
        if FakeSerial.currentMessage==len(FakeSerial.messages)+1:
            sys.exit()
        print "read message :"+FakeSerial.messages[FakeSerial.currentMessage-1]
        return FakeSerial.messages[FakeSerial.currentMessage-1]
        



if __name__ == '__main__':

    port=None
    if len(sys.argv)==2:
        port=sys.argv[1]

    gateway=SerialGateway(port)

    if "debug"==port:
        gateway.setSerialPort(FakeSerial())        
    
    gateway.start()

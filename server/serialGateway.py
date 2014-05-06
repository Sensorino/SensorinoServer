import logging
import serial
import protocol
import httplib2
import json
import sys
import time
import datetime
import time
import common
import traceback
import mqttThread


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
baseUrl                 = common.Config.getRestServer()+"/sensorinos/"



class SerialGateway:

    linuxPossibleSerialPorts=['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2',
    '/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
    '/dev/ttyS0','/dev/ttyS1',
    '/dev/ttyS2','/dev/ttyS3'] # TODO : complete list

    windowsPossibleSerialPorts=['\\.\COM1', '\\.\COM2', '\\.\COM3', '\\.\COM4'] # TODO : complete list


    def on_mqtt_message(mqtt, obj, msg):
        """main server sends message on mosquitto"""
        logger.debug("msg from mosquitto: "+json.dumps(msg))
        if("commands" == msg.topic):
            command=msg.payload
            if("set" in command):
                self.port.write(json.dumps(command))
            elif("control" in command):
                self.port.write(json.dumps(command))
            else:
                logger.warn("unhandled message from mqtt: "+json.dumps(command))
        else:
            logger.warn("unknown mqtt channel")


    def on_publish(prot, address, serviceID, serviceInstanceID, data):
        """protocol has decoded a publish event on (serial port), we should talk to main server"""
        try:
#            response, content = http.request( baseUrl+"/address/"+str(serviceID)+"/"+str(serviceInstanceID), 'POST', json.dumps(data), headers=content_type_header)
            print("post to rest")
        except Exception, e:
            print(e)
            traceback.print_stack()


    def __init__(self, portFile=None):
        self.protocol=protocol.Protocol()
        self.protocol.on_publish=self.on_publish
        self.mqtt=thread=mqttThread.MqttThread()
        self.mqtt.on_message=self.on_mqtt_message
        self.portFile=portFile
        self.port=None


    def setSerialPort(self, port):
        self.port=port


    def startSerial(self):
        if self.port==None:
            if self.portFile==None:
                for device in SerialGateway.windowsPossibleSerialPorts:
                    try:
                        self.port = serial.Serial(device, 57600)
                        break
                    except:
                        logger.debug("arduino not on "+device)
            else:
                self.port = serial.Serial(port, 57600)


    def startMqtt(self):
        self.mqtt.mqttc.connect(common.Config.getMqttServer(), 1883, 60)
        self.mqtt.mqttc.subscribe("commands", 0)
        self.mqtt.start()
       

    def start(self):
        self.startSerial()
        self.startMqtt()
        while True:
            if self.protocol.treatMessage(self.port.readline()):
                print "message ok"
            else:
                print "message ko"



class FakeSerial:
    
    currentMessage=0   
    messages=[
        '{ "set":     { "address": [1,2,3,4], "serviceID": 2, "serviceInstanceID": 0, "state": { "value": "on" } } }',
        '{ "publish": "fuck"}',
        '{ "publish": { "address": [1,2,3,4], "serviceID": 2, "serviceInstanceID": 0, "data":  { "value": "14" } } }',
        '{ "request": { "address": [1,2,3,4], "serviceID": 2, "serviceInstanceID": 0 } }'
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

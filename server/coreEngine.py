#!/usr/bin/python3
import logging
import threading
import datetime
import ConfigParser
import sensorino
import common
import json
import mqttThread
from errors import *

# create logger with 'spam_application'
logger = logging.getLogger('sensorino_coreEngine')
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



class Core:
    def __init__(self):
        self.sensorinos=[]
        self.loadSensorinos()
        self.mqtt = None


    def getSensorinos(self):
        """return all the sensorinos that are registered"""
        return self.sensorinos

    def loadSensorinos(self):
        """load all sensorinos stored in db """
        for senso in sensorino.Sensorino.loadAllSensorinos():
            senso.loadServices()
            self.addSensorino(senso)
        

    def addSensorino(self, sensorino):
        """create and add a new sensorino unless there is an id/address conflict """
        if (sensorino in self.sensorinos):
            logger.debug("not adding sensorino, already present")
            return None
        for sens in self.sensorinos:
            if ( sens.address == sensorino.address):
                logger.warn("unable to add your sensorino, id or address duplication")
                return None
        self.sensorinos.append(sensorino)
        return True

    def delSensorino(self, saddress):
        """delete and remove a new sensorino"""
        s=None
        try:
            s=self.findSensorino(saddress=saddress)
        except SensorinoNotFoundError:
            logger.debug("not deleting sensorino as already missing")
            return True
        s.delete()
        self.sensorinos.remove(s)
        return True

    def findSensorino(self, saddress=None):
        """return sensorino with given address or id"""
        for sens in self.sensorinos:
            if (saddress!=None and sens.address==saddress):
                return sens
        raise SensorinoNotFoundError("missing")

    def getServicesBySensorino(self, saddress):
        """return all services registered in sensorino with given id"""
        s = self.findSensorino(saddress=saddress)
        if s == None:
            logger.debug("not returning services as unable to find sensorino")
            return None
        return s.services 

    def createDataService(self, saddress, name, dataType ):
        s = self.findSensorino(saddress=saddress)
        service=sensorino.DataService(name, dataType, s.address)
        if (False==s.registerService(service)):
            return False
        status=service.save()
        return True

    def deleteService(self, saddress, serviceId):
        s = self.findSensorino(saddress=saddress)
        service = s.getService(serviceId)
        if service == None:
            logger.debug("not deleting service as already missing")
            return True
        else:
            s.removeService(service)
            service.delete()
            return True


        
    # TODO generate exception on failures, this will allow rest server to translate them into http status
    
    def publish(self, saddress, serviceId, data):
        """publish some data on dataService with given id"""
        sens = None
        try:
            sens=self.findSensorino(saddress=saddress)
        except SensorinoNotFoundError:
            logger.warn("logging data from unknown sensorino is not allowed (yet)")
            self.mqtt.mqttc.publish("discover", json.dumps({ "sensorino": {"saddress": saddress, "address": None}}))
            return False
        service=None
        try:
            service=sens.getService(serviceId)
        except ServiceNotFoundError:
            logger.warn("logging data from unknown service is not allowed")
            payload=  { "service": {"saddress": saddress, "serviceId":serviceId}}
            logger.warn(self.mqtt.mqttc.publish("discover", json.dumps(payload) ))
            raise ServiceNotFoundError("unable to publish on unknown service, mqttt clients will receive some notice")
        return service.logData(data)

    def setState(self, saddress, serviceId, state):
        """to setState we should send command and wait for the publish back"""
        sens=self.findSensorino(saddress=saddress)
        if (sens==None):
            logger.warn("logging data from unknown sensorino is not allowed (yet)")
            return None
        service=sens.getService(serviceId)
        if (service==None):
            logger.warn("logging data from unknown sensorino is not allowed (yet)")
            return None
        
        self.mqtt.mqttc.publish("commands",  { "set" : {"saddress":sadress, "serviceID":serviceId, "state":state}})
        return True

    
    def request(self, saddress, serviceId):
        """will launch a request to service"""
        sens=self.findSensorino(saddress=saddress)
        if (sens==None):
            logger.warn("logging data from unknown sensorino is not allowed (yet)")
            return None
        service=sens.getService(serviceId)
        if (service==None):
            logger.warn("logging data from unknown sensorino is not allowed (yet)")
            return None
        self.mqtt.mqttc.publish("commands",  json.dumps({ "request": { "saddress":sens.address, "serviceID":service.serviceId, "serviceInstanceID":service.sid}}))
        return True


    def _createMqttClient(self):
        """confire mqtt client and create thread for it"""
        def mqtt_on_connect(mosq, obj, rc):
            mosq.subscribe("sensorino", 0)
            print("rc: "+str(rc))

        def mqtt_on_message(mosq, obj, msg):
            print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

        def mqtt_on_publish(mosq, obj, mid):
            print("mid: "+str(mid))

        def mqtt_on_subscribe(mosq, obj, mid, granted_qos):
            print("Subscribed: "+str(mid)+" "+str(granted_qos))

        def mqtt_on_log(mosq, obj, level, string):
            print(string)

        mqtt=mqttThread.MqttThread()

        mqtt.mqttc.on_message = mqtt_on_message
        mqtt.mqttc.on_connect = mqtt_on_connect
        mqtt.mqttc.on_publish = mqtt_on_publish
        mqtt.mqttc.on_subscribe = mqtt_on_subscribe
        # Uncomment to enable debug messages
        #mqtt.mqttc.on_log = on_log
        
        self.mqtt = mqtt
        return mqtt


    def start(self):
        self.loadSensorinos()
        self._createMqttClient().start()



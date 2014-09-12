#!/usr/bin/python3
import logging
import threading
from threading import Timer
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
        self._sensorinosLoaded=False
        self.sensorinos=[]
        self.loadSensorinos()
        self.mqtt = None


    def getSensorinos(self):
        """return all the sensorinos that are registered"""
        return self.sensorinos

    def loadSensorinos(self, forceReload=False):
        """load all sensorinos stored in db """
        if (self._sensorinosLoaded and not forceReload):
            logger.debug("core started already, won't reload sensorinos")
            return
        self.sensorinos=[]
        for senso in sensorino.Sensorino.loadAllSensorinos():
            senso.loadServices()
            self.addSensorino(senso)
        self._sensorinosLoaded=True
    
    def createSensorino(self, name, address, description, location=None):
        sens=sensorino.Sensorino( name,  address, description) 
        self.addSensorino(sens)
        try:
            sens.save()
        except FailToSaveSensorinoError:
            raise FailToAddSensorinoError("failed to save senso")
        return sens


    def addSensorino(self, sensorino):
        """create and add a new sensorino unless there is an id/address conflict """
        if (sensorino in self.sensorinos):
            raise FailToAddSensorinoError("not adding sensorino, already exists")
        for sens in self.sensorinos:
            if ( sens.address == sensorino.address):
                raise FailToAddSensorinoError("not adding sensorino, address duplicated")
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

    def createService(self, saddress, name, instanceId ):
        s = self.findSensorino(saddress=saddress)
        service=sensorino.Service(name, s.address, instanceId)
        if (False==s.registerService(service)):
            raise FailToAddServiceError("register failed")
        status=service.save()
        return service

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
    
    def publish(self, saddress, instanceId, data, channelId=None):
        """publish some data on dataService with given id"""
        sens = None
        try:
            sens=self.findSensorino(saddress=saddress)
        except SensorinoNotFoundError:
            logger.warn("logging data from unknown sensorino is not allowed (yet)")
            payload = { "from": 0, "to": saddress, "type": "request", "serviceId": 0 }
            self.mqtt.mqttc.publish("request", json.dumps(payload))
            return False
        service=None
        try:
            service=sens.getService(instanceId)
        except ServiceNotFoundError:
            logger.warn("logging data from unknown service is not allowed")
            payload = { "from": 0, "to": saddress, "type": "request", "serviceId": 0 }
            self.mqtt.mqttc.publish("serialOut", json.dumps(payload))
            raise ServiceNotFoundError("unable to publish on unknown service, mqttt clients will receive some notice")

        return service.logData(data, channelId)

    def getLogs(self, saddress, instanceId, channelId):
        """publish some data on dataService with given id"""
        sens = None
        try:
            sens=self.findSensorino(saddress=saddress)
        except SensorinoNotFoundError:
            return False
        service=None
        try:
            service=sens.getService(instanceId)
        except ServiceNotFoundError:
            raise ServiceNotFoundError("unknown")

        return service.getLogs(channelId)


    def setState(self, saddress, serviceId, channelId, state):
        """to setState we should send command and wait for the publish back"""
        sens=self.findSensorino(saddress=saddress)
        if (sens==None):
            raise SensorinoNotFoundError("unable to set state: no sensorino found")
        service=sens.getService(serviceId)
        if (service==None):
            raise ServiceNotFoundError("unable to set state: no service found")
        chan=service.getChannel(channelId)
        
        
        self.mqtt.mqttc.publish("commands",  { "set" : {"saddress":saddress, "serviceID":serviceId, "state":state, "channelId":channelId}})
        timer=Timer(1,self.request, args=[saddress, serviceId]) # TODO cancel active timers if we receive a publish ?
        return True

    
    def request(self, saddress, serviceId):
        """will launch a request to service"""
        sens=self.findSensorino(saddress=saddress)
        if (sens==None):
            logger.warn("unknown sensorino")
            return None
        service=sens.getService(serviceId)
        if (service==None):
            logger.warn("unknown service")
            return None
        self.mqtt.mqttc.publish("commands",  json.dumps({ "request": { "saddress":sens.address, "serviceID":service.serviceId, "serviceInstanceID":service.sid}}))
        return True


    def _createMqttClient(self):
        """confire mqtt client and create thread for it"""
        def mqtt_on_connect(obj, rc):
            self.mqtt.mqttc.subscribe("sensorino", 0)

        def mqtt_on_message(obj, msg):
            print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

        def mqtt_on_publish(obj, mid):
            print("mid: "+str(mid))

        def mqtt_on_subscribe(obj, mid, granted_qos):
            print("Subscribed: "+str(mid)+" "+str(granted_qos))

        def mqtt_on_log(obj, level, string):
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



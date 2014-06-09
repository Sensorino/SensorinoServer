import logging
import threading
import sqlite3
import mosquitto
import datetime
import json
import common
from errors import *

# create logger with 'spam_application'
logger = logging.getLogger('sensorino_application')
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



class Sensorino:
    def __init__(self, name, address, description="yet another node", owner="default", location="unknown"):
        if (None==name):
            name="TBSL"
        self.name=name
        self.address=address
        self.description=description
        self.services=[]
        self.owner=owner
        self.location=location
        self._alive=None

    def loadServices(self):
        for service in Service.getServicesBySensorino(self.address):
            self.registerService(service) 
 

    def registerService(self, service):
        try:
            self.getService(service.serviceId)
        except ServiceNotFoundError:
            self.services.append(service)
            return True
        return False

    def removeService(self, service):
        self.services.remove(service)

    def getService(self, serviceId):
        for service in self.services:
            if service.serviceId==serviceId:
                return service
        raise ServiceNotFoundError("service not found/registered")

    def toData(self):
        return {
            'name': self.name,
            'address': self.address,
            'description': self.description,
            'owner': self.owner,
            'location': self.location
        }

    def save(self):
        logger.debug("insert/update sensorino in db")
        status=None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()
            status=c.execute("INSERT OR REPLACE INTO sensorinos  (name, description, owner, location, address) VALUES(?,?,?,?,?)", (self.name, self.description, self.owner, self.location, self.address))
            conn.commit()
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()
            raise FailToSaveSensorinoError("failed to save sensorino to db")
            
        return status

    def delete(self):
        status=None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()
            status=c.execute("DELETE FROM sensorinos WHERE address=? ",( self.address,))
            conn.commit()
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        return status

    @staticmethod
    def loadAllSensorinos(loadServices=False):

        sensorinos=[]

        conn = sqlite3.connect(common.Config.getDbFilename())
        conn.row_factory = common.dict_factory
        c = conn.cursor()

        c.execute("SELECT * from sensorinos")
        rows = c.fetchall()

        for row in rows:
            sens=Sensorino( row["name"], row["address"], row["description"], row["owner"], row["location"])
            sensorinos.append(sens)
            if(loadServices):
                sens.loadServices()

        return sensorinos
            



class Device:
    def __init__(self, name, location, did):
        self.name=name
        self.did=did
        self.location=location
        self.type=None

    def toData(self):
        return {
            'name': self.name,
            'did': self.did,
            'location': self.location.toData(),
            'type': self.type
        }


class DataDevice(Device):
    def __init__(self, name, dataType, location=None, did=None):
        Device.__init__( self, name, location, did)
        self.type="data"
        self.dataType=dataType

    def toData(self):
        data=super(Device, self).toData()
        data['dataType']=self.dataType
        return data

class ActuatorDevice(Device):
    def __init__(self, name, did, location, actuatorType):
        Device.__init__(self, name, location, did)
        self.type="action"
        self.actuatorType=actuatorType


class Location:
    def __init__(self, name, position="DEFAULT"):
        self.name=name
        self.position=position

    def toData(self):
        return {
            'name': self.name,
            #'position': self.position.toData(),
            'position': self.position,
        }

class Position:
    def __init__(self, name):
        self.name=name

    def toData(self):
        return {
            'name': self.name
        }


# Services can be linked to a sensor, an actuator or be a network protocol handler (Ping?)

class Service():
    def __init__(self, name, serviceId):
        self.name=name
        self.serviceId=serviceId
        self.saddress=None
        self.stype=None
        self.channels=[]

    def setSensorino(self, s):
        self.saddress=s.address

    def save(self):
        if (self.saddress==None):
            logger.critical("unable to save service without sensorino")
            return None

        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()
            status=None
            if (self.serviceId==None):
                logger.debug("INSERT service")
                status=c.execute("INSERT INTO services ( name, stype,  saddress)  VALUES (?,?,?)",
                    ( self.name, self.stype, self.saddress))
                self.serviceId=c.lastrowid
            else:
                logger.debug("UPDATE service")
                status=c.execute("UPDATE services SET stype=:stype WHERE saddress=:saddress AND serviceId=:serviceId LIMIT 1",
                     self.toData())
            conn.commit()
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        return status

    def delete(self):
        status=None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()
            logger.debug("DELETE service")
            status=c.execute("DELETE FROM services WHERE saddress=:saddress AND serviceId=:serviceId LIMIT 1", self.toData())
            conn.commit()
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()
        return status

    def toData(self):
        return {
            'name': self.name,
            'serviceId' : self.serviceId,
            'saddress': self.saddress,
            'stype' : self.stype,
            'channels': self.channels
        }


    @staticmethod
    def getServicesBySensorino(saddress):
        conn = sqlite3.connect(common.Config.getDbFilename())
        conn.row_factory = common.dict_factory
        c = conn.cursor()
        status=c.execute("SELECT * FROM services WHERE saddress=:saddress ",   {"saddress": saddress})

        rows = c.fetchall()
        conn.commit()

        services=[]
        for srow in rows:
            service=None
            if("DATA" == srow["stype"]):
                service=DataService(srow['name'], srow['dataType'], saddress, srow['serviceId'])
            elif("ACTUATOR" == srow["stype"]):
                service=ActuatorService(srow['name'], srow['dataType'], saddress, srow['serviceId'])
            if(None==service):
                logger.error("failed to load service for sensorino :"+srow)
            else:
                services.append(service)

        return services




class DataService(Service):
    def __init__(self, name,  saddress, serviceId=None):
        Service.__init__( self, name, serviceId)
        self.saddress=saddress
        self.stype="DATA"

        # need to load channels
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            conn.row_factory = common.dict_factory
            c = conn.cursor()

            c.execute("SELECT * FROM dataChannels WHERE serviceId=:serviceId", self.toData())
            channels = c.fetchall()
            for channel in channels:
                self.channels[channel["channelId"]]=channel["dataType"]
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        conn.close()


    def loadChannels(self):
        status = None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            conn.row_factory = common.dict_factory
            c = conn.cursor()
            logger.debug("Load channels for service "+str(self.serviceId))

            status = c.execute("SELECT * from dataChannels WHERE serviceId=? ORDER BY channelId", (str(self.serviceId),))
            self.channels = c.fetchall()

        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        return status


    def setChannels(self, dataTypes):
        status = None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()

            logger.debug("clear channels for service "+str(self.serviceId))
            c.execute("DELETE FROM dataChannels WHERE serviceId=?", (str(self.serviceId),))

            logger.debug("insert "+str(len(dataTypes))+" channels in service "+str(self.serviceId))
            for dataType in dataTypes:
                status=c.execute("INSERT INTO dataChannels (serviceId, dataType) VALUES (?,?)", ( self.serviceId, dataType))

            c.execute("SELECT * from dataChannels ")
            rows=c.fetchall()
            conn.commit()
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        conn.close()

        return self.loadChannels()


    def logData(self, channelId, value):

        logger.debug("log data on service:"+str(self.serviceId)+"/chan:"+str(channelId))

        if (len(self.channels)==0):
            logger.debug("unable to log on service without channel")
            return False

        status=None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()

            if (None==channelId):
                if (len(self.channels)==1):
                    channelId=self.channels[0]["channelId"]
                else:
                    logger.debug("unable to log on multiple channel service without channelId")
                    return False
            

            logger.debug("Log data on sensorino"+str(self.saddress)+" service: "+self.name+" chanID: "+str(channelId)+" data:"+str(value))

            status=c.execute("INSERT INTO dataServicesLog (saddress, serviceId, channelId, value, timestamp) VALUES (?,?,?,?,?) ",
                     (self.saddress, self.serviceId, channelId, value, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        conn.close()
        return status
           

    def getLogs(self, channelId):
        conn = sqlite3.connect(common.Config.getDbFilename())
        conn.row_factory = common.dict_factory
        c = conn.cursor()

        c.execute("SELECT value, timestamp FROM dataServicesLog WHERE serviceId=:serviceId AND channelId=:channelId", { 'serviceId': self.serviceId, 'channelId': channelId})
        rows = c.fetchall()
        conn.close()
        return rows



class ActuatorService(Service):

    def __init__(self, name, dataType, saddress, serviceId=None):
        Service.__init__( self, name, serviceId)
        self.dataType=dataType
        self.saddress=saddress
        self.stype="ACTUATOR"

    def setState(self, state):
        status=None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()
            status=c.execute("UPDATE sensorinos SET name=:name, address=:address, description=:description, owner=:owner, location=:location WHERE saddress=:saddress", self.toData())
            conn.commit()
            self.state=state
        except Exception as e:
            print(e)
            # Roll back any change if something goes wrong
            conn.rollback()

        conn.close()
        return status

 


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
            



# Location has a wider scope: typically a building or a room 
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

# Position is more precise: typically a room or relative position window/back/front
class Position:
    def __init__(self, name):
        self.name=name

    def toData(self):
        return {
            'name': self.name
        }


# Service are attached to a sensorino and handles various channels
class Service():
    def __init__(self, name, serviceId):
        self.name=name
        self.serviceId=serviceId
        self.saddress=None
        self.channels=[]
        self.loadChannels()

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
                status=c.execute("INSERT INTO services ( name,  saddress)  VALUES (?,?)",
                    ( self.name,  self.saddress))
                self.serviceId=c.lastrowid
            else:
                logger.debug("UPDATE service")
                status=c.execute("UPDATE services SET  WHERE saddress=:saddress AND serviceId=:serviceId LIMIT 1",
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
            service=Service(srow['name'],  saddress, srow['serviceId'])
            if(None==service):
                logger.error("failed to load service for sensorino :"+srow)
            else:
                services.append(service)

        return services




    def loadChannels(self):
        if (None == self.serviceId ): # brand new service
            return True
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

        return len(self.channels)


    def setChannels(self, chansInfos):
        status = None
        try:
            conn = sqlite3.connect(common.Config.getDbFilename())
            c = conn.cursor()

            logger.debug("clear channels for service "+str(self.serviceId))
            c.execute("DELETE FROM dataChannels WHERE serviceId=?", (str(self.serviceId),))

            logger.debug("insert "+str(len(chansInfos))+" channels in service "+str(self.serviceId))
             
            for infos in chansInfos:
                if not("dataType" in infos and "type" in infos):
                    raise FailToSetServiceChannelsError("incomplete or invalid channel info "+str(infos))

            for infos in chansInfos:
                status=c.execute("INSERT INTO dataChannels (serviceId, dataType, type) VALUES (?,?,?)", ( self.serviceId, infos['dataType'], infos['type']))

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




 


import common

import logging
import serial
import json
import traceback
import httplib2

# create logger with 'spam_application'
logger = logging.getLogger('protocol')
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









class Protocol:
    """
    on_publish(self, address, serviceID, serviceInstanceID, data)
    on_set(self, address, serviceID, serviceInstanceID, state)
    on_request(self, address, serviceID, serviceInstanceID)
    on_error(self, address, type, data)



    """

    def __init__(self):
        self.on_publish=None
        self.on_set=None
        self.on_request=None
        self.on_error=None

    @staticmethod
    def serializeAddress(address):
        return  ".".join(str(digit) for digit in address)


    def treatMessage(self, jsonString):
        try:
            message=json.loads(jsonString)
            if ("type" not in message):
                logger.error("invalid message "+message)
                return False

            if("publish" == message["type"]):
                # 3 cases : services list, service details, real publish
                
                #service list from sensorino with address 10
                # { "from": 10, "to": 0, "type": "publish", "serviceId": [ 0, 1 ] },
        # service dataType / description from a service 1 on sensorino with address 10
#        { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "dataType": "switch", "count": [ 0, 1 ] },
        # publish from a service 1 of type switch on sensorino with address 10
 #       { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "switch": False },

                if ( "serviceId" in message and message["serviceId"] is list):
                    print "now declare sensorino";
                    sens={address: message["from"]}
                    response, content = http.request( baseUrl+"/"+message["from"]+"services", 'POST', json.dumps(sens), headers=content_type_header)
                    /sensorinos
                    response, content = http.request( baseUrl+"/"+message["from"]+"services", 'GET', headers=content_type_header)
                    for serviceId in message["serviceId"]:
        
                        
                elif( "dataType" in message):
                    print "now declare service"
                else
                    print "data publish"

                return True



            elif("set" == message["type"]):
                if(self.on_set!=None):
                    self.on_set(Protocol.serializeAddress(msg["address"]), msg["serviceID"], msg['serviceInstanceID'], msg["state"])
                    return True
            elif("request" == message["type"]):
                if(self.on_request!=None):
                    self.on_request(Protocol.serializeAddress(msg["address"]), msg["serviceID"], msg['serviceInstanceID'])
                    return True
            elif ("error" == message["type"]):
                if (self.on_error!=None):
                    self.on_error(Protocol.serializeAddress(msg["address"]), msg["type"], msg["data"])
                    return True
            else:
                logger.error("unhandled message "+message)
                return False
                    
        except Exception, e:
              
            logger.error("fail to treat json message "+jsonString)
            logger.error(e)

            print repr(traceback.format_stack())

            return False



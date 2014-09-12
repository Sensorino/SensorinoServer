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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)



httplib2.debuglevel     = 0
http                    = httplib2.Http()
content_type_header     = "application/json"
headers                 = {'Content-type': 'application/json'}
baseUrl                 = "http://"+common.Config.getRestServerAddress()+":"+str(common.Config.getRestServerPort())




class Protocol:
    """
    on_publish(self, address, serviceID, serviceInstanceID, data)
    on_set(self, address, serviceID, serviceInstanceID, state)
    on_request(self, address, serviceID, serviceInstanceID)
    on_error(self, address, type, data)

    """


    @staticmethod
    def serializeAddress(address):
        return  ".".join(str(digit) for digit in address)


    def treatMessage(self, jsonString):

        logger.debug("treat message in proto: "+jsonString)

        try:
            message=json.loads(jsonString)
            if ("type" not in message):
                if("error" in message):
                #TODO who should receive this ?
                    logger.warn(json.dumps(message)) 
                    return False
                else:
                    logger.error("invalid message "+message)
                    return False

            if("publish" == message["type"]):
                # 3 cases : services list, service details, real publish
                
                #service list from sensorino with address 10
                # { "from": 10, "to": 0, "type": "publish", "serviceId": [ 0, 1 ] },

                if ( "serviceId" in message and  isinstance(message["serviceId"], list)):
                    logger.debug("declare sensorino");
                    sens={
                        'address'   : message["from"],
                        'name'      : 'new sensorino',
                        'description' : 'new sensorino'
                    }
                    response, content = http.request( 
                        baseUrl+"/sensorinos",
                        'POST',
                        json.dumps(sens),
                        headers)

                    if ('200'!=response['status']):
                        raise Exception("failed to declare sensorino, server answer :"+str(response)+"/"+str(content))
        
                        
                elif("dataType" in message):
                    
                    service={
                        "name": "new service",
                        "instanceId":message['serviceId']
                    }
                    response, content = http.request(
                        baseUrl+"/sensorinos/"+str(message['from'])+"/services",
                        'POST',
                        json.dumps(service),
                        headers)


                    if ('200'!=response['status']):
                        raise Exception("failed to declare sensorino, server answer :"+str(response)+"/"+str(content))
                    
                    sens=content
                    channels=[]

                    if ( isinstance(message["dataType"], list)):
                        # { "dataType": [ "temperature", "temperature", "switch", "switch", ], "count": [ 2, 2 ] } 
                        position=0
                        publishers=message['count'][0]
                        settables=message['count'][1]
                        chanType="publisher"
                        for dataType in message["dataType"]:
                            if position>=publishers:
                                chanType="settable"
                            channels.append({                                
                                "position": position,
                                "dataType": dataType,
                                "type": chanType
                                })
                            position=position+1

                    else:
                        # { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "dataType": "switch", "count": [ 0, 1 ] },
                        chanType="publisher"
                        if message['count'][1]!=0:
                            chanType="settable"
                        channels.append({
                            "position": 0,
                            "dataType": message["dataType"],
                            "type": chanType
                        })

                    response, content = http.request(
                        baseUrl+"/sensorinos/"+str(message['from'])+"/services/"+str(message['serviceId'])+"/channels",
                        'POST',
                        json.dumps({'channels':channels}),
                        headers)

                    if ('200'!=response['status']):
                        raise Exception("failed to declare sensorino, server answer :"+str(response)+"/"+str(content))


                else:
                    # publish from a service 1 of type switch on sensorino with address 10
                    # { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "switch": False },

                    logger.debug("data publish")

                    url= baseUrl+"/sensorinos/"+str(message['from'])+"/services/"+str(message["serviceId"])+"/channels"
                    if 'from' in message: del message['from']
                    if 'to' in message: del message['to']
                    if 'type' in message: del message['type']
                    
                    response, content = http.request( 
                        url,
                        'PUT',
                        json.dumps({'data':message}),
                        headers)

                    if ('200'!=response['status']):
                        raise Exception("failed to declare sensorino, server answer :"+str(response)+"/"+str(content))

                return True


            elif("set" == message["type"]):
                logger.debug("set message from a sensorino, don't know what to do")
                return False
            elif("request" == message["type"]):
                logger.debug("request message from a sensorino, don't know what to do")
                return False
            else:
                logger.error("unhandled message "+message)
                raise Exception("unhandled message type : "+message["type"])
                    
        except Exception, e:
              
            logger.error("fail to treat json message "+str(jsonString))
            logger.error(e)

            logger.debug(repr(traceback.format_stack()))

            return False



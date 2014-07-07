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
headers                 = {'Content-type': 'application/json'}
baseUrl                 = "http://"+common.Config.getRestServerAddress()+":"+str(common.Config.getRestServerPort())









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

                print "serviceid: "+str(message["serviceId"])

                if ( "serviceId" in message and  isinstance(message["serviceId"], list)):
                    print "now declare sensorino";
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
                    print "response: "+str(response);
                    print "content: "+str(content);
        
                        
                elif( "dataType" in message):
                    
                    print "now declare service"

                    service={
                        "name": "new service",
                        "instanceId":message['serviceId']
                    }
                    response, content = http.request(
                        baseUrl+"/sensorinos/"+str(message['from'])+"/services",
                        'POST',
                        json.dumps(service),
                        headers)

                    print "response: "+str(response);
                    print "content: "+str(content);
                
                    if ('404'==response['status']):
                        print "not there"
                        return False
                    if ('200'==response['status']):
                        print "ok"
                    else:
                        print "some error ?"
                    
                    sens=content

                    channels=[]

                    if ( isinstance(message["dataType"], list)):
                        # { "dataType": [ "temperature", "temperature", "switch", "switch", ], "count": [ 2, 2 ] } 
                        print "this is multi channel service"
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
                        print "single channel service"
                        chanType="publisher"
                        if message['count'][1]!=0:
                            chanType="settable"
                        channels.append({
                            "position": 0,
                            "dataType": message["dataType"],
                            "type": chanType
                        })

                    response, content = http.request(
                        baseUrl+"/sensorinos/"+str(message['from'])+"/services/"+str(service['instanceId'])+"/channels",
                        'POST',
                        json.dumps({'channels':channels}),
                        headers)
                    print "response: "+str(response);
                    print "content: "+str(content);


                else:
                    # publish from a service 1 of type switch on sensorino with address 10
                    # { "from": 10, "to": 0, "type": "publish", "serviceId": 1, "switch": False },

                    print "data publish"

                    url= baseUrl+"/sensorinos/services/"+str(message["serviceId"])+"/channels"
                    if 'from' in message: del message['from']
                    if 'to' in message: del message['to']
                    if 'type' in message: del message['type']
                    
                    response, content = http.request( 
                        url,
                        'POST',
                        json.dumps({'data':message}),
                        headers)
                    print "response: "+str(response);
                    print "content: "+str(content);



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
              
            logger.error("fail to treat json message "+str(jsonString))
            logger.error(e)

            print repr(traceback.format_stack())

            return False



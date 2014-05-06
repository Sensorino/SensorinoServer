class MessageParser:


    def __init__(self):
       self.protocol="basic"  

    @staticmethod
    def serializeAddress(address):
        return  ".".join(str(digit) for digit in address)

    def processMessage(self, message):
        print("in pm:")
        print(message)

        if("PublishMessage" in message):
            msg=message["PublishMessage"]
            self.onPublish(MessageParser.serializeAddress(msg["address"]), msg["service"], msg["data"])
        elif("Ping" in message):
            msg=message["Ping"]
            self.onPing(MessageParser.serializeAddress(msg["address"]))
        elif("Pong" in message):
            msg=message["Pong"]
            self.onPong(MessageParser.serializeAddress(msg["address"]))
        elif("internals" in message):
            msg=message["internals"]
            self.onPublish(1, 1, msg["temp"])
        else:
            print "NOT SUPPORTED"

    def onPublish(self, sensoId, serviceId, data):
        print("should log "+str(data)+" on senso "+str(sensoId)+" /service:"+str(serviceId))

    def onPing(self, sensAddr):
        print("should pong:  "+sensAddr)

    def onPong(self, sensAddr):
        print("got pong response from  "+sensAddr)


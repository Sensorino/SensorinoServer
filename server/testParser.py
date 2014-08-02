#!/usr/bin/env python

#-------------------------------------------------------------------------------
# Purpose:
#
# Author:      Elektroid
#
#-------------------------------------------------------------------------------

import sys
sys.path.append("..")
import protocol
import json
import mqttThread
import time

mode = "mqtt"


def main():
    json_data = open(sys.argv[1])
    data=json_data.read()
    print "treat :"+data

    if "mqtt" == mode:
        mThread=mqttThread.MqttThread()
        mThread.start()
        time.sleep(1)
        mThread.mqttc.publish("serialOut", data)
    else:
        prot=protocol.Protocol()
        print prot.treatMessage(data)



if __name__ == '__main__':
    main()

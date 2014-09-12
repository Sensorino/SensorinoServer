#!/usr/bin/env python

import mqttThread
import logging
import ConfigParser
import common
import time
import json


def on_mqtt_message(mqtt, obj, msg):
    print str(msg)

def on_connect(obj, rc, x=None):
    if rc == 0:
        print("Connected successfully.")

def on_subscribe(obj, mid, qos_list):
    print("Subscribe with mid "+str(mid)+" received.")


if __name__ == '__main__':
    mThread=mqttThread.MqttThread()
    mThread.mqttc.on_message = on_mqtt_message
    mThread.mqttc.on_connect = on_connect
    mThread.mqttc.on_subscribe = on_subscribe
    mThread.start()
    time.sleep(1)
    mThread.mqttc.subscribe("serialIn", 0)
    mThread.mqttc.subscribe("serialOut", 0)


    while True:
        user_input = raw_input("Send json command: ")
        mThread.mqttc.publish("serialOut", user_input)
        


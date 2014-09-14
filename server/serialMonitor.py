#!/usr/bin/env python

import mqttThread
import logging
import ConfigParser
import common
import time
import json


def on_mqtt_message(mqtt, obj, msg):
    print str(msg)

def on_connect(mosq, obj, rc):
    if rc == 0:
        print("Connected successfully.")

def on_subscribe(mosq, obj, mid, qos_list):
    print("Subscribe with mid "+str(mid)+" received.")


mode="in"

if __name__ == '__main__':
    mThread=mqttThread.MqttThread()
    mThread.mqttc.on_message = on_mqtt_message
    mThread.mqttc.on_connect = on_connect
    mThread.mqttc.on_subscribe = on_subscribe
    mThread.start()
    time.sleep(1)
    mThread.mqttc.subscribe("serialIn", 0)
    mThread.mqttc.subscribe("serialOut", 0)

    print "enter 'in' to send json message to be treated by gateway as incoming message from sensorino network\n"
    print "enter 'out' to send json message to be treated by gateway as outgoing message to sensorino network\n" 
    print "or enter a json message\n"


    while True:
        prompt=""
        if "in" == mode:
            prompt="Send json command 'from' base: "
        else:
            prompt="Send json command to network"
        user_input = raw_input(prompt)

        if "in" == user_input:
            mode="in"
        elif "out" == user_input:
            mode="out"
        else:
            if "out" == mode:
                mThread.mqttc.publish("serialOut", user_input)
            else:
                mThread.mqttc.publish("serialInEmulator", user_input)
        


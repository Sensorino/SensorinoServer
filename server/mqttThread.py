import threading
import ConfigParser
import mosquitto
import common
import time
import logging
import traceback
import singleton




class MqttThread(threading.Thread):
    __metaclass__ = singleton.Singleton
    """
        will create a daemon thread with mosquitto.Mosquitto client
    """
    def __init__(self):



        threading.Thread.__init__(self)
        self.daemon = True
        self.mqttc=mosquitto.Mosquitto()

        # create logger with 'spam_application'
        self.logger = logging.getLogger('serial_gateway')
        self.logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(ch)

#        self.logger.debug(repr(traceback.format_stack()))

    def run (self):
        # TODO add a mecanism to handle reconnection
        while True:
            try:
                self.mqttc.connect(common.Config.getMqttServer(), 1883, 60)
                self.mqttc.loop_forever()
            except Exception as e:
                self.mqttc.disconnect()
                self.logger.warn("failure in mqtt loop, sleep for a while")                 
                time.sleep(5)



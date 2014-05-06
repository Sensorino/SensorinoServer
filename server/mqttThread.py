import threading
import ConfigParser
import mosquitto
import common

class MqttThread(threading.Thread):
    """
        will create a daemon thread with mosquitto.Mosquitto client
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.mqttc=mosquitto.Mosquitto()

    def run (self):
        # TODO add a mecanism to handle reconnection
        self.mqttc.connect(common.Config.getMqttServer(), 1883, 60)
        self.mqttc.loop_forever()



import ConfigParser
import errors


class Config:
    """
        This is some kind of wrapper around ConfigParser that handles default and autoloading
        It's shared accross all projects
    """
    config=None
    filename="sensorino.ini"

    @staticmethod
    def load():
        Config.config = ConfigParser.ConfigParser()
        if len(Config.config.read(Config.filename))==0:
           raise ConfigFileNotFoundError("unable to open "+filename) 

    @staticmethod
    def setConfigFile(filename):
        Config.filename=filename
        Config.load()

    @staticmethod
    def getDbFilename():
        if (Config.config==None):
            Config.load()
        return Config.config.get("Db", "Filename")

    @staticmethod
    def getMqttServer():
        if (Config.config==None):
            Config.load()
        return Config.config.get("Mqtt", "ServerAddress")
       
    @staticmethod
    def getRestServerAddress():
        if (Config.config==None):
            Config.load()
        return Config.config.get("RestServer", "ServerAddress")
    @staticmethod
    def getRestServerPort():
        if (Config.config==None):
            Config.load()
        return int(Config.config.get("RestServer", "ServerPort"))
     

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


 

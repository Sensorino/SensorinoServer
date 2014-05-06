import ConfigParser


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
        Config.config.read(Config.filename)

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
    def getRestServer():
        if (Config.config==None):
            Config.load()
        return Config.config.get("RestServer", "ServerAddress")
      

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


 

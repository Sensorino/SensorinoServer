class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ConfigFileNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class SensorinoNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class ServiceNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class FailToSaveSensorinoError(Error):
    def __init__(self, message):
        self.message = message

class FailToAddSensorinoError(Error):
    def __init__(self, message):
        self.message = message

class FailToSetServiceChannelsError(Error):
    def __init__(self, message):
        self.message = message
  
   

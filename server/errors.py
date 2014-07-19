class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ConfigFileNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class SensorinoNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class ChannelNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class FailToSaveSensorinoError(Error):
    def __init__(self, message):
        self.message = message

class FailToDeleteSensorinoError(Error):
    def __init__(self, message):
        self.message = message

class FailToAddSensorinoError(Error):
    def __init__(self, message):
        self.message = message

class FailToLoadSensorinosError(Error):
    def __init__(self, message):
        self.message = message

class ServiceNotFoundError(Error):
    def __init__(self, message):
        self.message = message

class FailToAddServiceError(Error):
    def __init__(self, message):
        self.message = message

class FailToSaveServiceError(Error):
    def __init__(self, message):
        self.message = message

class FailToDeleteService(Error):
     def __init__(self, message):
        self.message = message
   
class FailToSetServiceChannelsError(Error):
    def __init__(self, message):
        self.message = message

class FailToLogOnChannelError(Error):
    def __init__(self, message):
        self.message = message

class FailToLoadServicesError(Error):
    def __init__(self, message):
        self.message = message

class FailToLoadChannelLogsError(Error):
    def __init__(self, message):
        self.message = message

class FailToLoadChannelsError(Error):
    def __init__(self, message):
        self.message = message

class FailToLogDataError(Error):
    def __init__(self, message):
        self.message = message

  
   

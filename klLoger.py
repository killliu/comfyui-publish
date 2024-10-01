from enum import Enum

class LogLevel(Enum):
    Log = 1
    Worning = 2
    Error = 4

class klLoger:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(klLoger, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def enable(self, e:bool, l:LogLevel):
        self.enabled = e
        self.level = l

    def log(self, content):
        if self.enabled and (self.level & LogLevel.Log.value) == LogLevel.Log.value:
            print(content)
 
    def worning(self, content):
        if self.enabled and (self.level & LogLevel.Worning.value) == LogLevel.Worning.value:
            print(content)

    def error(self, content):
        if self.enabled and (self.level & LogLevel.Error.value) == LogLevel.Error.value:
            print(content)

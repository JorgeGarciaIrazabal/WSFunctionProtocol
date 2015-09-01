import inspect
from wshubsapi.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from wshubsapi.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from wshubsapi.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator

__author__ = 'Jorge'


class HubException(Exception):
    pass


class Hub(object):
    HUBs_DICT = {}
    __hubsConstructed = False

    @classmethod
    def initHubsInspection(cls, forceReconstruction=False):
        if not cls.__hubsConstructed or forceReconstruction:
            cls.HUBs_DICT.clear()
            for hub in Hub.__subclasses__():
                try:
                    hub()
                except TypeError as e:
                    if "__init__()" in str(e):
                        raise HubException(
                            "Hubs can not have a constructor with parameters. Check Hub: %s" % hub.__name__)
                    else:
                        raise e
            cls.__hubsConstructed = True

    @classmethod
    def constructJSFile(cls, path="."):  # todo: create client constructor
        cls.initHubsInspection()
        JSClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    @classmethod
    def constructJAVAFile(cls, package, path="."):  # todo: create client constructor
        cls.initHubsInspection()
        hubs = cls.HUBs_DICT.values()
        JAVAFileGenerator.createFile(path, package, hubs)
        JAVAFileGenerator.createClientTemplate(path, package, hubs)

    @classmethod
    def constructPythonFile(cls, path="."):  # todo: create client constructor
        cls.initHubsInspection()
        PythonClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    def __sender(self):
        """
        :rtype : CommHandler
        """
        frame = inspect.currentframe()
        while frame.f_back is not None:
            frame = frame.f_back
            if isinstance(frame.f_locals.get("self", None), CommHandler):
                return frame.f_locals["self"]
        return None

    sender = property(__sender)

    @property
    def connections(self):
        """
        :rtype : dict of int; CommHandler
        """
        return self.sender.connections

    @classmethod
    def getConnections(cls, commProtocol=None):
        """
        :type commProtocol: wshubsapi.CommProtocol.CommProtocol
        :rtype : dict of int; CommHandler
        """
        if commProtocol is None:
            return cls.sender.connections
        else:
            return commProtocol.connections

    @property
    def allClients(self):
        return ConnectionGroup(self.getConnections().values())

    @classmethod
    def getAllClients(cls, commProtocol = None):
        return ConnectionGroup(cls.getConnections(commProtocol).values())

    @property
    def otherClients(self):
        connection = self.sender
        return ConnectionGroup(filter(lambda x: x.ID != connection.ID, connection.connections.values()))

    @classmethod
    def getClients(cls, function, commProtocol):
        connections = cls.getConnections(commProtocol)
        return ConnectionGroup(filter(function, connections.values()))

    @classmethod
    def getClient(cls, id, commProtocol = None):
        return cls.getConnections(commProtocol).get(id, None)

    def __init__(self):
        hubName = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        if hubName in self.HUBs_DICT:
            raise HubException("Hub's name must be unique")
        if hubName.startswith("__"):
            raise HubException("Hub's name can not start with '__'")
        if hubName == "wsClient":
            raise HubException("Hub's name can not be 'wsClient', it is a  reserved name")
        setattr(self.__class__, "__HubName__", hubName)
        self.HUBs_DICT[hubName] = self


from wshubsapi.CommProtocol import ConnectionGroup, CommHandler

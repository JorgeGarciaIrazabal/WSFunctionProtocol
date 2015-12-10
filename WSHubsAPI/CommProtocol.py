import logging
import threading
from jsonpickle.pickler import Pickler
from WSHubsAPI.ConnectedClient import ConnectedClient
from WSHubsAPI.ConnectedClientsHolder import ConnectedClientsHolder
from WSHubsAPI.utils import WSMessagesReceivedQueue, setSerializerDateTimeHandler

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

_DEFAULT_PICKER = Pickler(max_depth=5, max_iter=80, make_refs=False)

setSerializerDateTimeHandler()


class CommProtocol(object):
    def __init__(self, unprovidedIdTemplate="UNPROVIDED__{}"):
        self.lock = threading.Lock()
        self.availableUnprovidedIds = list()
        self.unprovidedIdTemplate = unprovidedIdTemplate
        self.lastProvidedId = 0
        self.wsMessageReceivedQueue = WSMessagesReceivedQueue()
        self.wsMessageReceivedQueue.startThreads()
        self.allConnectedClients = ConnectedClientsHolder.allConnectedClients

    def constructConnectedClient(self, writeMessageFunction, closeFunction, serializationPickler=_DEFAULT_PICKER):
        return ConnectedClient(serializationPickler, self, writeMessageFunction, closeFunction)

    def getUnprovidedID(self):
        if len(self.availableUnprovidedIds) > 0:
            return self.availableUnprovidedIds.pop(0)
        while self.unprovidedIdTemplate.format(self.lastProvidedId) in self.allConnectedClients:
            self.lastProvidedId += 1
        return self.unprovidedIdTemplate.format(self.lastProvidedId)

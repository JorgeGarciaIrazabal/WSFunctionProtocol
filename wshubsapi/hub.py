__author__ = 'Jorge'


class UnsuccessfulReplay:
    def __init__(self, replay):
        self.replay = replay


class HubError(Exception):
    pass


class Hub(object):
    def __init__(self):
        hub_name = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        if hub_name in HubsInspector.HUBS_DICT:
            raise HubError("Hub's name must be unique, found duplicated name with: {}".format(hub_name))
        if hub_name.startswith("__"):
            raise HubError("Hub's name can not start with '__'")
        if hub_name == "wsClient":
            raise HubError("Hub's name can not be 'wsClient', it is a  reserved name")
        setattr(self.__class__, "__HubName__", hub_name)
        HubsInspector.HUBS_DICT[hub_name] = self

        self._client_functions = dict()
        self._define_client_functions()
        self._clients_holder = ConnectedClientsHolder(hub_name)
        self.__hub_subscribers = []

    def subscribe_to_hub(self, _sender):
        if _sender in self.__hub_subscribers:
            return False
        self.__hub_subscribers.append(_sender)
        return True

    def unsubscribe_from_hub(self, _sender):
        if _sender in self.__hub_subscribers:
            self.__hub_subscribers.remove(_sender)
            return True
        return False

    def get_subscribed_clients_to_hub(self):
        self.__hub_subscribers = list(filter(lambda c: not c.api_is_closed, self.__hub_subscribers))
        return map(lambda x: x.ID, self.__hub_subscribers)

    def _get_clients_holder(self):
        """
        :rtype: ConnectedClientsHolder
        """
        # _clients_holder is defined while inspecting hubs
        return self._clients_holder

    @property
    def clients(self):
        return self._get_clients_holder()

    @property
    def client_functions(self):
        return self._client_functions

    @client_functions.setter
    def client_functions(self, client_functions):
        assert isinstance(client_functions, dict)
        for function_name, function in client_functions.items():
            assert isinstance(function_name, basestring)
            assert hasattr(function, '__call__')
        self._client_functions = client_functions

    @staticmethod
    def _construct_unsuccessful_replay(replay):
        return UnsuccessfulReplay(replay)

    def _define_client_functions(self):
        pass


from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connected_clients_holder import ConnectedClientsHolder

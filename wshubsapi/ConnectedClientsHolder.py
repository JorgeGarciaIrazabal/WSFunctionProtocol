
class ConnectedClientsHolder:
    all_connected_clients = dict()

    def __init__(self, hub_name):
        self.hub_name = hub_name

    def get_all_clients(self):
        return ConnectedClientsGroup(list(self.all_connected_clients.values()), self.hub_name)

    def get_other_clients(self, sender):
        """
        :type sender: ConnectedClientsGroup
        """
        connected_clients = [c for c in self.all_connected_clients.values() if c.ID != sender.ID]
        return ConnectedClientsGroup(connected_clients, self.hub_name)

    def get_clients(self, filter_function):
        return ConnectedClientsGroup(filter(filter_function, self.all_connected_clients.values()), self.hub_name)

    def get_client(self, client_id):
        return ConnectedClientsGroup([self.all_connected_clients[client_id]], self.hub_name)[0]

    def get_subscribed_clients(self):
        subscribed_clients = HubsInspector.get_hub_instance(self.hub_name).get_subscribed_clients_to_hub()
        return ConnectedClientsGroup([self.all_connected_clients[ID] for ID in subscribed_clients], self.hub_name)

    @classmethod
    def append_client(cls, client):
        cls.all_connected_clients[client.ID] = client

    @classmethod
    def pop_client(cls, client_id):
        """
        :type client_id: str|int
        """
        return cls.all_connected_clients.pop(client_id, None)


from wshubsapi.ConnectedClientsGroup import ConnectedClientsGroup
from wshubsapi.HubsInspector import HubsInspector

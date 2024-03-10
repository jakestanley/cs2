from py.map import Map

from rcon.source import Client

class Controller:
    def __init__(self, host, port, password) -> None:
        self.host = host
        self.port = port
        self.password = password

    def restart(self):
        with Client(self.host, int(self.port), passwd=self.password) as client:
            response = client.run('mp_restartgame', '1')

        print(response)

    def change_map(self, map: Map, mode: str):
        with Client(self.host, int(self.port), passwd=self.password) as client:
            response = client.run('host_workshop_map', map.id)

        print(response)
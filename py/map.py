import csv
from typing import Set, List

class Map:
    def __init__(self, workshop: bool, id: str, name: str, modes: Set[str]) -> None:
        self.workshop = workshop
        self.id = id
        self.name = name
        self.modes = modes

def LoadMaps() -> List[Map]:
    maps = []
    with open("maps.csv") as csvf:
        for row in csv.DictReader(csvf):
            maps.append(Map(
                workshop=row['workshop'] == 'yes', 
                id=row['id'], 
                name=row['name'],
                modes=row['modes'].split("|")))
            
    return maps
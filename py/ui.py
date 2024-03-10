from typing import List

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, \
    QLabel, QWidget, QDialogButtonBox, QPushButton, QListWidget, \
    QListWidgetItem

from py.map import Map
from py.controller import Controller

def _ControlPanel() -> QVBoxLayout:
    layout = QVBoxLayout()


    return layout

class MapWidget(QWidget):
    def __init__(self, map: Map, controller: Controller) -> None:
        super().__init__()

        self.map = map

        self.label_name = QLabel(self.map.name)
        self.workshop_button = QPushButton("Workshop")
        self.workshop_button.setEnabled(self.map.workshop)
        self.workshop_button.clicked.connect(self.open_workshop)

        self.dm_button = QPushButton("Deathmatch")
        self.dm_button.setEnabled(True)
        self.dm_button.clicked.connect(lambda: controller.change_map(self.map, "deathmatch"))
        
        layout = QHBoxLayout()
        layout.addWidget(self.label_name)
        layout.addWidget(self.workshop_button)
        layout.addWidget(self.dm_button)
        

        self.setLayout(layout)

    def open_workshop(self):
        # Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=1234567890
        print(f"Opening workshop page for {self.map.name} ({self.map.id})")

class ManagerDialog(QDialog):
    def __init__(self, maps: List[Map], controller: Controller):
        super(ManagerDialog, self).__init__()
        self.setWindowTitle("CS2 Manager")

        layout: QVBoxLayout = QVBoxLayout(self)

        # build the game control panel
        cpanel: QHBoxLayout = self.control_panel(controller)
        
        # build the map list
        self.map_list_widget = QListWidget()
        for map in maps:
            map_widget = MapWidget(map, controller)
            list_item = QListWidgetItem(self.map_list_widget)
            list_item.setSizeHint(map_widget.sizeHint())
            self.map_list_widget.setItemWidget(list_item, map_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)

        # layout ordering
        layout.addLayout(cpanel)
        layout.addWidget(self.map_list_widget)
        layout.addWidget(button_box)

    def control_panel(self, controller: Controller):
        layout = QHBoxLayout()


        restart_button = QPushButton("Restart")
        restart_button.clicked.connect(controller.restart)

        layout.addWidget(QPushButton("Pause"))
        layout.addWidget(restart_button)
        layout.addWidget(QPushButton("Scramble"))
        return layout

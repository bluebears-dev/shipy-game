# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 23.12.16

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition

from app.multiplayer.client import Client
from styledbutton import StyledButton

Builder.load_file('app/screen/kv/multiplayerscreen.kv')
Builder.load_file('app/screen/kv/connection.kv')


class ConnectionScreen(Screen):
    pass


class MultiplayerScreen(Screen):
    address_field = ObjectProperty(None)
    port_field = ObjectProperty(None)
    error_message = ObjectProperty(None)


class ConnectionLabel(Label):
    pass


class ConnectButton(StyledButton):

    def on_release(self):
        game = App.get_running_app().game
        screen_manager = App.get_running_app().screen_manager
        address = screen_manager.current_screen.address_field.text, int(screen_manager.current_screen.port_field.text)

        try:
            client = Client(address)
            client.request('test')
            game.players[1].make_client(address)
        except ConnectionRefusedError:
            screen_manager.current_screen.error_message.text = 'Cannot connect to the specified server!'
            return 0
        screen_manager.current_screen.error_message.text = ''
        screen_manager.transition = SlideTransition()
        screen_manager.current = 'ship_selection'

# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 27.12.16

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import Screen

from styledbutton import StyledButton

Builder.load_file('app/screen/kv/gameendscreen.kv')


class GameEndScreen(Screen):
    text_field = ObjectProperty(None)
    moves_field = ObjectProperty(None)

    def __init__(self, name, moves, **kwargs):
        super(GameEndScreen, self).__init__(**kwargs)
        self.player = name
        self.moves = moves

    def change_text(self):
        self.text_field.text = '%s has won the game!' % self.player
        self.moves_field.text = 'Winner has finished in %d moves' % self.moves


class EndButton(StyledButton):

    def on_release(self):
        screen_manager = App.get_running_app().screen_manager
        screen_manager.transition = FadeTransition()
        screen_manager.current = 'main'

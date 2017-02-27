# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 23.12.16

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, FadeTransition
from kivy.uix.textinput import TextInput

from app.game import ShipyGame, Player, NetPlayer, AI, singleplayer_init, multiplayer_init, pvp_init
from app.screen.highscores import highscores_init
from app.screen.player import PlayerScreen
from styledbutton import StyledButton

Builder.load_file('app/screen/kv/menuscreen.kv')
first_time = True


def clear_previous_session(callback, text):
    global first_time
    screen_manager = App.get_running_app().screen_manager
    if App.get_running_app().game:
        del App.get_running_app().game

    screen = screen_manager.get_screen('ship_selection')
    screen.clear()

    screen.start_button.callback = callback
    screen.start_button.text = text

    screen = screen_manager.get_screen('player1')
    if screen:
        screen_manager.remove_widget(screen)
        screen_manager.add_widget(PlayerScreen(name = 'player1'))

    screen = screen_manager.get_screen('player2')
    if screen:
        screen_manager.remove_widget(screen)
        screen_manager.add_widget(PlayerScreen(name = 'player2'))

    App.get_running_app().game = ShipyGame()
    game = App.get_running_app().game
    return game, screen_manager


def prepare_game(player1: type, player2: type, session_init, text, screen, *args):
    game, screen_manager = clear_previous_session(session_init, text)

    game.make_player(player1, 'Computer')
    game.make_player(player2, 'Computer')

    screen_manager.transition = FadeTransition(duration = 0.3)
    screen_manager.current = screen


class MenuButtonAnimation(Animation):
    initial_pos = 0

    def on_start(self, widget):
        self.initial_pos = widget.pos[0]

    def on_complete(self, widget):
        if widget.player1 and widget.player2:
            prepare_game(widget.player1, widget.player2, widget.screen_init, widget.button_text, widget.screen)
        else:
            if widget.screen_init:
                widget.screen_init()
            screen_manager = App.get_running_app().screen_manager
            screen_manager.transition = FadeTransition(duration = 0.3)
            screen_manager.current = widget.screen

        widget.pos[0] = self.initial_pos
        Clock.schedule_once(widget.show, 1)


class MainMenuButton(StyledButton):
    player1 = None
    player2 = None
    screen_init = None
    screen = None
    animation_start = None

    def __init__(self, **kwargs):
        super(MainMenuButton, self).__init__(**kwargs)

    def on_release(self):
        if not self.animation_start:
            self.animation_start = MenuButtonAnimation(x = self.x + 100, opacity = 0, duration = 0.2)
        self.animation_start.start(self)

    def show(self, *args):
        self.opacity = 1


class SingleplayerButton(MainMenuButton):

    def __init__(self, **kwargs):
        super(SingleplayerButton, self).__init__(**kwargs)
        self.player1 = Player
        self.player2 = AI
        self.screen_init = singleplayer_init
        self.screen = 'ship_selection'
        self.button_text = 'Play'


class MultiplayerButton(MainMenuButton):

    def __init__(self, **kwargs):
        super(MultiplayerButton, self).__init__(**kwargs)
        self.player1 = Player
        self.player2 = NetPlayer
        self.screen_init = multiplayer_init
        self.screen = 'multiplayer'
        self.button_text = 'Play'


class HighscoresButton(MainMenuButton):
    def __init__(self, **kwargs):
        super(HighscoresButton, self).__init__(**kwargs)
        self.screen_init = highscores_init
        self.screen = 'highscores'


class PvPButton(MainMenuButton):

    def __init__(self, **kwargs):
        super(PvPButton, self).__init__(**kwargs)
        self.player1 = Player
        self.player2 = Player
        self.screen_init = pvp_init
        self.screen = 'ship_selection'
        self.button_text = 'Next'


class QuitButton(MainMenuButton):

    def __init__(self, **kwargs):
        super(QuitButton, self).__init__(**kwargs)
        self.screen_init = exit


class Test(MainMenuButton):

    def __init__(self, **kwargs):
        super(Test, self).__init__(**kwargs)
        self.player1 = AI
        self.player2 = AI
        self.screen_init = pvp_init
        self.screen = 'ship_selection'
        self.button_text = 'Next'


class MenuScreen(Screen):
    pass


class PlayerInput(TextInput):

    def center_text(self):
        text_width = self._get_text_width(
            self.text,
            self.tab_width,
            self._label_cached
        )

        self.padding_x = (self.width - text_width) / 2
        return self.padding_x

    def on_text(self, *args):
        self.center_text()

    def on_focus(self, *args):
        self.center_text()


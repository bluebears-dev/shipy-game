# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 23.12.16

from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, WipeTransition

from app.color import Color
from app.game import change_screen

Builder.load_file('app/screen/kv/playerscreen.kv')


class PlayerScreen(Screen):
    ship_grid = ObjectProperty(None)
    ship_counter = ObjectProperty(None)
    turn_indicator = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PlayerScreen, self).__init__(**kwargs)
        self.player = None

    def bind_player(self, player):
        self.player = player
        self.player.screen = self

    def change_counter(self, number):
        if number == 1:
            self.ship_counter.text = 'Only one ship left'
        else:
            self.ship_counter.text = '%d ships left' % number

    def change_move_counter(self, moves):
        self.turn_indicator.text = '%s has moved %d times' % (self.player.name, moves)


class Cell(Button):
    sid = 0
    cell_state = False

    def __init__(self, **kwargs):
        super(Cell, self).__init__(**kwargs)
        self.row = Cell.sid // 10
        self.col = Cell.sid % 10
        Cell.sid += 1
        Cell.sid %= 100
        self.background_color = Color.cell_color

    def assign_state(self, state):
        if state == 'miss':
            self.background_color = Color.miss_color
        elif state == 'hit':
            self.background_color = Color.hit_color

        self.disabled = True
        self.cell_state = True

    def surrounding_assign_state(self, state):
        grid = App.get_running_app().screen_manager.current_screen.ship_grid.virtual_grid

        def wrapper():
            if self.row + i < 0 or self.col + j < 0:
                return
            try:
                cell = grid[self.row + i][self.col + j]

                if (i != 0 or j != 0) and not cell.cell_state:
                    cell.assign_state(state)
            except IndexError:
                return
            except AttributeError:
                return
            return

        for i in range(-1, 2):
            for j in range(-1, 2):
                wrapper()
        return True

    def on_release(self):
        app = App.get_running_app()
        current_player = app.game.players[app.game.turn]
        next_player = app.game.players[(app.game.turn + 1) % 2]
        current_player.screen.ship_grid.lock()

        if app.game.has_ended():
            return

        ship = current_player.hit(self.row, self.col, next_player)
        if ship:
            self.assign_state('hit')
        else:
            self.assign_state('miss')
        app.game.next_turn()

        app.screen_manager.transition = WipeTransition()
        Clock.schedule_once(partial(change_screen, next_player.screen), current_player.wait_time)
        return ship


class PlayingGrid(GridLayout):

    def __init__(self, **kwargs):
        super(PlayingGrid, self).__init__(**kwargs)
        self.virtual_grid = [[None] * 10 for i in range(10)]
        for i in range(100):
            ship_cell = Cell()
            self.add_widget(ship_cell)
            self.virtual_grid[i // 10][i % 10] = ship_cell

    def clear(self):
        for i in range(100):
            del self.virtual_grid[i // 10][i % 10]
        for i in range(100):
            ship_cell = Cell()
            self.add_widget(ship_cell)
            self.virtual_grid[i // 10][i % 10] = ship_cell

    def lock(self):
        grid = self.virtual_grid

        for row in grid:
            for col in row:
                if not col.cell_state:
                    col.disabled = True

    def unlock(self):
        grid = self.virtual_grid

        for row in grid:
            for col in row:
                if not col.cell_state:
                    col.disabled = False

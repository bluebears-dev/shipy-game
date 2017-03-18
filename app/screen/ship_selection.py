# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 23.12.16

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from app.color import Color
from app.game import Ship, ShipElement, make_random_ships
from app.styledbutton import StyledButton

Builder.load_file('app/screen/kv/selectionscreen.kv')


class ShipSelectionScreen(Screen):
    ship_grid = ObjectProperty(None)
    top_pane = ObjectProperty(None)
    start_button = ObjectProperty(None)
    player_input = ObjectProperty(None)

    def enable_starting(self):
        self.start_button.disabled = (self.ship_grid.start_game != 10)

    def clear(self):
        self.ship_grid.clear()
        self.player_input.text = ''
        self.start_button.disabled = True


class LimitIndicator(Widget):
    pass


class RotatedImage(Image):
    angle = NumericProperty(0)
    pass


class ShipLimitIndicator(GridLayout):
    limit = 1

    def set_limit(self, limit):
        self.limit = limit

        for i in range(4):
            self.children[i].opacity = 0
        for i in range(self.limit):
            self.children[i].opacity = 1


class ShipCell(Button):
    sid = 0
    grid = None
    ship_id = None

    def __init__(self, **kwargs):
        super(ShipCell, self).__init__(**kwargs)

        self.next_cell = None
        self.prev_cell = None

        self.is_ship = False
        self.row = ShipCell.sid // 10
        self.col = ShipCell.sid % 10
        ShipCell.sid += 1
        ShipCell.sid %= 100

    def check(self):
        condition = (0 <= self.row <= 9 and 0 <= self.col <= 9 and
                     not self.grid.virtual_grid[self.row][self.col].is_ship) or \
                    (self.row < 0 or self.col < 0 or self.row > 9 or self.col > 9)

        return condition

    def on_release(self):
        if not ShipCell.grid:
            ShipCell.grid = App.get_running_app().screen_manager.current_screen.ship_grid

        if self.is_ship:
            ship = self.grid.remove(self.grid.find_ship(self.ship_id))
            self.grid.ships.pop(self.grid.ships.index(ship))
        else:
            if self.grid.size_button.disabled:
                return
            else:
                ship = self.grid.create(self.row, self.col)
                if ship:
                    self.grid.ships.append(ship)

        self.grid.toggle_button()

        limit_panel = App.get_running_app().screen_manager.current_screen.limit_indicator
        limit_panel.set_limit(self.grid.size_button.how_many)
        App.get_running_app().screen_manager.current_screen.enable_starting()


class ShipGrid(GridLayout):
    size_button = None
    direction_button = None
    ships = []
    start_game = 0

    def __init__(self, **kwargs):
        super(ShipGrid, self).__init__(**kwargs)
        self.virtual_grid = [[None] * 10 for i in range(10)]
        for i in range(100):
            ship_cell = ShipCell()
            self.add_widget(ship_cell)
            self.virtual_grid[i // 10][i % 10] = ship_cell

    def clear(self):
        if len(self.ships):
            for ship in self.ships:
                self.remove(ship)

        size_button = None
        screen = App.get_running_app().screen_manager.get_screen('ship_selection')
        for button in screen.top_pane.children:
            if hasattr(button, 'ship_size'):
                self.size_button = button
                button.unlock(5 - button.ship_size)
                if button.ship_size == 4:
                    size_button = button
                else:
                    self.size_button.background_color = Color.gray

        self.ships = []
        self.start_game = 0
        self.size_button = size_button

    def get_cell(self, ship_element):
        return self.virtual_grid[ship_element.row][ship_element.col]

    def sign_cell(self, ship_element, ship_id):
        cell = self.get_cell(ship_element)
        cell.background_color = Color.red
        cell.is_ship = True
        cell.ship_id = ship_id

    def unsign_cell(self, ship_element):
        cell = self.get_cell(ship_element)
        cell.background_color = Color.cell_color
        cell.is_ship = False
        cell.ship_id = None

    def check_surrouding(self, row, col):

        def wrapper(x, y):
            if x < 0 or y < 0:
                return True
            try:
                retval = self.virtual_grid[x][y].check()
            except IndexError:
                return True
            except AttributeError:
                return True

            return retval

        for i in range(-1, 2):
            for j in range(-1, 2):
                if not wrapper(row + i, col + j):
                    return False
        return True

    def put(self, ship):
        for element in ship.elements:
            self.sign_cell(element, ship.id)

        for button in App.get_running_app().screen_manager.get_screen('ship_selection').top_pane.children:
            if hasattr(button, 'ship_size') and ship.size == button.ship_size:
                if self.size_button:
                    self.size_button.background_color = Color.gray
                self.size_button = button
                break

        if self.size_button.how_many:
            self.size_button.how_many -= 1
        self.toggle_button()
        self.start_game += 1
        return ship

    def create(self, r, c):
        elements = []
        direction = self.direction_button.direction
        row, col = r, c

        for iterator in range(self.size_button.ship_size):
            if row > 9 or col > 9:
                return

            if not self.check_surrouding(row, col):
                return

            elements.append(ShipElement(row, col))
            row += direction[1]
            col += direction[0]

        self.size_button.how_many -= 1
        self.start_game += 1
        ship = Ship(elements)
        for element in elements:
            self.sign_cell(element, ship.id)
        return ship

    def remove(self, ship):
        for element in ship.elements:
            self.unsign_cell(element)

        if len(ship.elements) >= 2:
            direction = (abs(ship.elements[0].col - ship.elements[1].col),
                         abs(ship.elements[0].row - ship.elements[1].row))
        else:
            direction = (1, 0)

        self.direction_button.change_direction(direction)

        for button in App.get_running_app().screen_manager.get_screen('ship_selection').top_pane.children:
            if hasattr(button, 'ship_size') and ship.size == button.ship_size:
                if self.size_button:
                    self.size_button.background_color = Color.gray
                button.how_many += 1
                self.size_button = button
                break

        self.start_game -= 1
        return ship

    def toggle_button(self):
        button = self.size_button
        if button.how_many and button.disabled:
            button.unlock()
        elif not button.how_many and not button.disabled:
            button.lock()

    def find_ship(self, ship_id):
        for ship in self.ships:
            if ship.id == ship_id:
                return ship
        return None


class ShipSelectionPane(GridLayout):
    pass


class ShipOrientationButton(StyledButton):
    direction = (1, 0)
    image = ObjectProperty(None)

    def change_direction(self, vector):
        if vector == (1, 0):
            self.direction = vector
            self.image.angle = 0
        elif vector == (0, 1):
            self.direction = vector
            self.image.angle = 90

    def on_release(self):
        self.change_direction((self.direction[1], self.direction[0]))


class ShipSizeButton(StyledButton):
    ship_size = NumericProperty(0)
    how_many = NumericProperty(0)
    button_id = StringProperty('')

    def lock(self):
        self.disabled = True
        self.how_many = 0
        self.background_color = Color.gray

    def unlock(self, how_many = 1):
        self.how_many = how_many
        self.background_color = Color.green
        self.disabled = False

    def on_release(self):
        screen = App.get_running_app().screen_manager.current_screen

        screen.limit_indicator.set_limit(self.how_many)
        if screen.ship_grid.size_button:
            screen.ship_grid.size_button.background_color = Color.gray
        self.background_color = Color.green
        screen.ship_grid.size_button = self


class RandomGridButton(StyledButton):

    def on_release(self):
        ships = None
        for i in range(5):
            if ships:
                break
            ships = make_random_ships()

        app = App.get_running_app()
        grid = app.screen_manager.get_screen('ship_selection').ship_grid
        grid.clear()
        for ship in ships:
            app.screen_manager.current_screen.ship_grid.ships.append(grid.put(ship))

        limit_panel = app.screen_manager.current_screen.limit_indicator
        limit_panel.set_limit(grid.size_button.how_many)
        app.screen_manager.current_screen.enable_starting()


class StartButton(StyledButton):
    callback = None

    def on_release(self):
        self.callback()


class ClearButton(StyledButton):

    def on_release(self):
        App.get_running_app().screen_manager.current_screen.ship_grid.clear()


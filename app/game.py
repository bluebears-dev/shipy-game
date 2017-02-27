# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 23.12.16

import atexit
import random
import time

import jsonpickle
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import Screen

from app.color import Color
from app.multiplayer.client import Client
from app.screen.game_end import GameEndScreen


def send_clear_request():
    players = App.get_running_app().game.players
    if len(players) >= 2 and isinstance(players[1], NetPlayer):
        try:
            players[1].client.request('clear')
        except ConnectionRefusedError:
            return


def make_random_ships():
    def convert(x, y):
        return 10 * x + y

    def remove_slots():
        for e in elements:
            for i in range(-1, 2, 1):
                for j in range(-1, 2, 1):
                    cell_id = convert(e[0] + i, e[1] + j)
                    if cell_id in free_slots:
                        index = free_slots.index(cell_id)
                        free_slots.pop(index)

    def add_ship(x, y):
        ship_size = ship_sizes[0]
        for i in range(ship_size):
            elements.append((x, y))
            x += direction[1]
            y += direction[0]
            if not convert(x, y) in free_slots:
                break
            if x > 9 or y > 9:
                break
        else:
            remove_slots()

            for i in range(len(elements)):
                elements[i] = ShipElement(elements[i][0], elements[i][1])

            how_many[0] -= 1
            if not how_many[0]:
                how_many.pop(0)
                ship_sizes.pop(0)
            placed_ships.append(Ship(elements))

    how_many = [1, 2, 3, 4]
    ship_sizes = [4, 3, 2, 1]
    free_slots = [i for i in range(100)]
    placed_ships = []

    random.seed(time.clock())
    start_time, time_limit = time.time(), 0.25
    while how_many:
        # if it take longer than limit, stop it
        if time.time() - start_time > time_limit:
            return None
        spot = free_slots[random.randrange(0, len(free_slots), 1)]
        elements = []
        row, col = spot // 10, spot % 10

        if random.randrange(0, 2):
            direction = (0, 1)
        else:
            direction = (1, 0)

        add_ship(row, col)

    return placed_ships


def change_screen(screen, *args):

    def callback(dt):
        if not app.screen_manager.transition.is_active:
            Clock.unschedule(event)
            app.game.players[app.game.turn].start_turn()

    app = App.get_running_app()
    if isinstance(screen, str):
        app.screen_manager.current = screen
        current_screen = app.screen_manager.get_screen(screen)
        if hasattr(current_screen, 'ship_grid') and not isinstance(current_screen.player, AI):
            current_screen.ship_grid.unlock()
    elif isinstance(screen, Screen):
        app.screen_manager.current = screen.name
        current_screen = screen
        if hasattr(current_screen, 'ship_grid') and not isinstance(current_screen.player, AI):
            current_screen.ship_grid.unlock()

    event = Clock.schedule_interval(callback, 0.01)


def bind_players(screen_manager, players):
    player1 = screen_manager.get_screen('player1')
    player2 = screen_manager.get_screen('player2')

    player1.bind_player(players[0])
    player2.bind_player(players[1])

    player1.turn_indicator.text = '%s\'s first move' % players[0].name
    player2.turn_indicator.text = '%s\'s first move' % players[1].name
    player1.turn_indicator.color = Color.first_player_color
    player2.turn_indicator.color = Color.second_player_color


def singleplayer_init():
    players = App.get_running_app().game.players
    index = 1
    if isinstance(players[1], AI) and not isinstance(players[0], AI):
        index = 0
        players[1].set(make_random_ships(), 0)

    screen_manager = App.get_running_app().screen_manager

    name = screen_manager.current_screen.player_input.text
    players[index].name = name if name else 'anonymous'
    players[index].set(screen_manager.current_screen.ship_grid.ships, 0)

    bind_players(screen_manager, players)

    index = random.randrange(0, len(players))
    App.get_running_app().game.turn = index
    screen_manager.transition = FadeTransition()
    change_screen(players[index].screen)


def pvp_init():
    players = App.get_running_app().game.players

    screen_manager = App.get_running_app().screen_manager
    screen_manager.get_screen('ship_selection').start_button.text = 'Play'

    name = screen_manager.current_screen.player_input.text
    players[0].name = name if name else 'anonymous'
    players[0].set(screen_manager.current_screen.ship_grid.ships, 0)

    screen_manager.get_screen('ship_selection').clear()
    screen_manager.get_screen('ship_selection').start_button.callback = singleplayer_init


def multiplayer_init():
    def finish_init(dt = 0):
        bind_players(screen_manager, players)

        App.get_running_app().game.turn = players[1].name_index
        screen_manager.transition = FadeTransition()
        change_screen(players[players[1].name_index].screen)

    def get_playername(*args):
        nonlocal index, event
        try:
            name = client.request('get_player', str(players[1].name_index))
        except ConnectionRefusedError:
            return

        if name and name != 'None':
            players[1].name = name
            Clock.unschedule(event)
            json = jsonpickle.encode(players[0].ships)
            index = client.request('ships', json)
            event = Clock.schedule_interval(get_ships, 1)

    def get_ships(*args):
        try:
            ships = client.request('get_ships', str(index))
        except ConnectionRefusedError:
            return

        if ships != 'None':
            players[1].ships = jsonpickle.decode(ships)
            Clock.unschedule(event)
            finish_init()

    screen_manager = App.get_running_app().screen_manager
    name = screen_manager.current_screen.player_input.text
    players = App.get_running_app().game.players

    players[0].name = name if name else 'anonymous'
    players[1].name_index = int(players[1].client.request('player', str(players[0].name)))
    players[0].set(App.get_running_app().screen_manager.current_screen.ship_grid.ships, 0)

    screen_manager.transition = FadeTransition()
    screen_manager.current = 'connection'
    atexit.register(send_clear_request)

    client = players[1].client
    index = 0
    event = Clock.schedule_interval(get_playername, 5)


class ShipyGame:

    def __init__(self):
        self.players = []
        self.turn = 0
        self.name = 'self'

    def make_player(self, player_type: type, name: object):
        self.players.append(player_type(name))
        return self.players[-1]

    def next_turn(self):
        self.turn += 1
        self.turn %= 2
        return self.turn

    def has_ended(self):
        for player in self.players:
            if player.ships_destroyed == 10:
                screen_manager = App.get_running_app().screen_manager
                screen_manager.transition = FadeTransition()
                ending_screen = GameEndScreen(player.name, player.moves)
                ending_screen.change_text()
                screen_manager.switch_to(ending_screen)
                loser = self.players[(self.players.index(player) + 1) % 2]
                App.get_running_app().highscores.append([player.name, loser.name, str(player.moves) + '\n'])
                if isinstance(self.players[1], NetPlayer):
                    atexit.unregister(send_clear_request)
                return True
        return False


class Ship:
    id = 0

    def __init__(self, elements = list(), drowned = 0):
        self.size = len(elements)
        self.elements = elements
        self.drowned_elements = drowned
        self.id = Ship.id
        Ship.id += 1

    def is_drowned(self):
        return self.drowned_elements == self.size

    def hit(self, row, col):
        for element in self.elements:
            if element.row == row and element.col == col and not element.shot_down:
                element.shot_down = True
                self.drowned_elements += 1
                return self
        return None

    def add_element(self, ship_element):
        self.elements.append(ship_element)
        self.size += 1

    def destroy_ship(self):
        for element in self.elements:
            del element
        self.size = 0


class ShipElement:
    def __init__(self, row, col):
        self.row, self.col = row, col
        self.shot_down = False


class Player:
    def __init__(self, name):
        self.screen = None
        self.name = name
        self.ships_destroyed = 0
        self.ships = []
        self.wait_time = 0.5
        self.moves = 1

    def callback(self, row = 0, col = 0):
        pass

    def set(self, ships, ships_destroyed):
        self.add_ships(ships)
        self.ships_destroyed = ships_destroyed

    def find_ship(self, ship_id):
        for ship in self.ships:
            if ship.id == ship_id:
                return ship
        return None

    def add_ship(self, ship):
        self.ships.append(ship)

    def add_ships(self, ships):
        for ship in ships:
            self.add_ship(ship)

    def pop_ship(self, ship):
        if isinstance(ship, Ship):
            index = self.ships.index(ship)
            self.ships.pop(index)
            ship.destroy_ship()
            del ship
        elif isinstance(ship, int):
            fship = self.find_ship(ship)
            index = self.ships.index(fship)
            self.ships.pop(index)
            fship.destroy_ship()
            del fship

    def add_move(self):
        self.moves += 1
        self.screen.change_move_counter(self.moves)

    def hit(self, row, col, player):
        player.callback(row, col)
        Clock.schedule_once(lambda x: self.add_move(), self.wait_time + 0.5)

        for ship in player.ships:
            hit_ship = ship.hit(row, col)
            if hit_ship:
                if hit_ship.is_drowned():
                    for element in hit_ship.elements:
                        self.screen.ship_grid.virtual_grid[element.row][element.col].surrounding_assign_state('miss')

                    player.ships.pop(player.ships.index(hit_ship))
                    self.ships_destroyed += 1
                    self.screen.change_counter(10 - self.ships_destroyed)
                return hit_ship
        else:
            return False

    def start_turn(self):
        App.get_running_app().game.has_ended()


class AI(Player):
    def __init__(self, name):
        super(AI, self).__init__(name)
        self.next_targets = []
        self.direction = None
        self.prev_target = None
        self.viable_targets = [i for i in range(100)]
        self.wait_time = 0.5

    def remove_surrounding_targets(self, row, col):
        for i in range(-1, 2):
            for j in range(-1, 2):
                self.remove_target(row + i, col + j)
        return True

    def remove_target(self, row, col):
        cell_id = row * 10 + col
        if cell_id in self.viable_targets:
            index = self.viable_targets.index(cell_id)
            if index >= 0:
                self.viable_targets.pop(index)

    def hit(self, row, col, player):
        self.remove_target(row, col)
        player.callback(row, col)
        Clock.schedule_once(lambda x: self.add_move(), self.wait_time + 0.5)

        for ship in player.ships:
            hit_ship = ship.hit(row, col)
            if hit_ship:
                if hit_ship.is_drowned():
                    for element in hit_ship.elements:
                        self.screen.ship_grid.virtual_grid[element.row][element.col].surrounding_assign_state('miss')
                        self.remove_surrounding_targets(element.row, element.col)

                    player.ships.pop(player.ships.index(hit_ship))
                    self.ships_destroyed += 1
                    self.screen.change_counter(10 - self.ships_destroyed)
                return hit_ship
        else:
            return None

    def is_available(self, row, col):
        if col > 9 or row > 9:
            return False
        cell_id = 10 * row + col
        return cell_id in self.viable_targets

    def start_turn(self):
        if len(self.next_targets):
            row, col = self.next_targets[0][0], self.next_targets[0][1]
            self.next_targets.pop(0)
        else:
            random.seed(time.clock())
            index = random.randrange(0, len(self.viable_targets))
            cell_id = self.viable_targets[index]
            row, col = cell_id // 10, cell_id % 10

        ship = self.screen.ship_grid.virtual_grid[row][col].on_release()

        if ship:
            if ship.is_drowned():
                # if it's down, there's no need to check remaining cells
                self.prev_target = None
                self.next_targets = []
                self.direction = None
            else:
                if not self.prev_target:
                    # check surrounding area
                    if self.is_available(row + 1, col):
                        self.next_targets.append((row + 1, col))

                    if self.is_available(row, col + 1):
                        self.next_targets.append((row, col + 1))

                    if self.is_available(row - 1, col):
                        self.next_targets.append((row - 1, col))

                    if self.is_available(row, col - 1):
                        self.next_targets.append((row, col - 1))

                    self.direction = None
                    self.prev_target = (row, col)
                else:
                    if not self.direction:
                        self.next_targets = []
                        self.direction = (row - self.prev_target[0], col - self.prev_target[1])
                    # check before and after previous target in found direction
                    row, col = row + self.direction[0], col + self.direction[1]
                    if self.is_available(row, col):
                        self.next_targets.append((row, col))
        else:
            if self.prev_target and self.direction:
                self.direction = (-self.direction[0], -self.direction[1])

                row, col = self.prev_target[0] + self.direction[0], self.prev_target[1] + self.direction[1]
                if self.is_available(row, col):
                    self.next_targets.append((row, col))


class NetPlayer(Player):
    def __init__(self, name):
        super(NetPlayer, self).__init__(name)
        self.client = None
        self.name_index = 0
        self.wait_time = 1

    def callback(self, row = 0, col = 0):

        json = jsonpickle.encode((row, col))
        self.client.request('coords', json)

    def make_client(self, address):
        self.client = Client(address)
        return self.client

    def start_turn(self):

        def get_coords(*args):
            string = self.client.request('get_coords')
            if string and string != 'None':
                row, col = jsonpickle.decode(string)
                self.screen.ship_grid.virtual_grid[row][col].on_release()
                Clock.unschedule(event)

        self.screen.ship_grid.lock()
        if not App.get_running_app().game.has_ended():
            event = Clock.schedule_interval(get_coords, 0.5)
        else:
            self.client.request('clear')

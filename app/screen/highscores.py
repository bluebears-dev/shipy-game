# *-* coding: utf-8 *-*
# Author: pgorski42
# Date: 13.01.17

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

Builder.load_file('app/screen/kv/highscores.kv')


class Score(GridLayout):
    pass


class ScoreLabel(Label):
    pass


def highscores_init():
    highscores = App.get_running_app().highscores
    screen = App.get_running_app().screen_manager.get_screen('highscores')

    for i in range(screen.iterator, len(highscores.score_list)):
        score = Score()
        score.add_widget(ScoreLabel(text = highscores.score_list[i][0], font_name = 'Old', font_size = 24))
        score.add_widget(ScoreLabel(text = highscores.score_list[i][1], font_name = 'Old', font_size = 24))
        score.add_widget(ScoreLabel(text = highscores.score_list[i][2], font_name = 'Old', font_size = 24))
        screen.score_list.add_widget(score)


class HighscoresScreen(Screen):
    score_list = ObjectProperty(None)
    iterator = 0


class Highscores:

    def __init__(self):
        self.current_score = 0
        self.score_list = self.read_from_file()
        self.has_changed = False

    @staticmethod
    def read_from_file(filename = 'highscores'):
        score = []
        try:
            with open(filename) as file:
                data = file.readlines()
        except FileNotFoundError:
            return score

        if not data:
            return score

        for line in data:
            score.append(line.lstrip('\n').rsplit(sep = ';'))
        else:
            return score[::-1]

    def append(self, score):
        self.score_list.append(score)
        self.has_changed = True

    def write_to_file(self, filename = 'highscores'):
        if self.has_changed:
            data = ''
            with open(filename, 'w') as file:
                for score in self.score_list:
                    data += ';'.join(score)
                file.write(data)

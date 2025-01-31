from SubModule import SubWindow
from time import perf_counter
from pyglet import media, app
from json import load as js_load, JSONDecodeError
from threading import Event, Thread
from typing import TYPE_CHECKING
from os import path


WIDTH, HEIGHT = 960, 480
FONT = "华文行楷"
ROOT = "resources"
WEIGHT_FILE = path.join(ROOT, "Json", "weight.json")
SCORING_MECHANISM = path.join(ROOT, "Json", "scoring_mechanism.json")
COLLISION_DATA_PATH = path.join("resources", "json", "collision_basic.json")
BG_IMG_PATH = path.join(ROOT, "Image", "bg.png")
ICO_PATH = path.join(ROOT, "Image", "favicon.ico")
DB_PATH = path.join(ROOT, "Rank.db")
DEFAULT_NAME = "这个家伙很神秘..."


if TYPE_CHECKING:
    from main import MainControl


class Setting(object):
    # 设置变量是相对静止的变量
    # 这些是直接设置变量，可以在设置中直接修改的
    PLAY_SPEED = 30 // 2
    RANDOM_FISH_SPEED = 10
    LIFE_VAL = 3
    REFRESH_SPEED = 3
    VECTORY_SCORE = 6000
    FISH_UPPER_NUM = 9
    GOD_TIME = 3
    PLAYER_INITIAL_H = 20
    PLAYER_INITIAL_W = 40
    # 这些是文件设置变量，可以在文件中永久性修改，但一般不建议修改
    score_slice = (500, 1500, 2500, 3500, 5000, 7000)
    fish_size_slice = (0.5, 1, 2)
    weight = (
        (0.4, 0.4, 0.2),
        (0.2, 0.5, 0.3),
        (0.1, 0.5, 0.4),
        (0.1, 0.4, 0.5),
        (0.25, 0.3, 0.45),
        (0.35, 0.35, 0.3),
        (0.5, 0.3, 0.2)
    )

    @classmethod
    def setting_param(cls) -> tuple:
        return (
            cls.PLAY_SPEED,
            cls.RANDOM_FISH_SPEED,
            cls.LIFE_VAL,
            cls.REFRESH_SPEED,
            cls.VECTORY_SCORE,
            cls.FISH_UPPER_NUM
        )

    @classmethod
    def load_weight_setting(cls) -> None:
        try:
            file_setting_var = ("score_slice", "fish_size_slice", "fish_speed_slice", "weight")
            with open(WEIGHT_FILE) as json_file:
                data = js_load(json_file)
                if not data["On"]:
                    return
                for var in file_setting_var:
                    setattr(cls, var, data[var])
        except (JSONDecodeError, KeyError, OSError):
            return


class GameControl(object):
    def __init__(self, main_control:'MainControl'):
        self.main_control = main_control
        self.life_lose: int = 0
        self.score: int = 0
        self.fish_count: int = 0  # 场面上鱼的数量, 除去玩家本身
        self.god: bool = False  # 当前是否处于无敌时间
        self.playing: bool = True  # 是否正在游戏中; 只有在游戏失败或成功时会被设置为False
        self.event: Event = Event()
        self.__stop_draw_id: int = 0
        self.__current_level: int = 0
        self.__game_start_time: float = 0.0
        self.__game_spend_time: float = 0.0

    def update_level(self) -> None:
        if self.__current_level == len(Setting.score_slice):
            return
        if self.score > Setting.score_slice[self.__current_level]:
            self.__current_level += 1

    def frozen_window(self) -> None:
        if self.stop:
            return
        self.event.clear()
        MusicPlayer.stop_game_music()
        self.main_control.unbind_player_motion()
        self.__game_spend_time += (perf_counter() - self.__game_start_time)

    def unfrozen_window(self) -> None:
        if self.ensure_unfrozen:
            return
        self.event.set()
        MusicPlayer.start_game_music()
        self.main_control.basic_frame.delete(self.__stop_draw_id)
        self.main_control.bind_player_motion()
        self.__game_start_time = perf_counter()

    def stop_game(self, _) -> None:
        if self.event.is_set():
            MusicPlayer.make_sound(3)
            self.draw_stop_info()
            self.frozen_window()
        else:
            self.unfrozen_window()

    def filled_with_fish(self) -> bool:
        return self.fish_count > Setting.FISH_UPPER_NUM

    def monitor_dispose_god_time(self, current_time) -> None:
        def join():
            self.event.wait()
            self.monitor_dispose_god_time(current_time)
        if self.stop:
            return Thread(target=join, daemon=True).start()
        if self.game_spend_time - current_time < Setting.GOD_TIME:
            self.main_control.player.flicker()
            return self.main_control.basic_frame.after(200, self.monitor_dispose_god_time, current_time)
        self.god = False
        

    def draw_stop_info(self):
        self.__stop_draw_id = self.main_control.basic_frame.create_text(
            485, 240, text="空格键游戏继续...", font=(FONT, 35)
        )

    @property
    def ensure_unfrozen(self):
        return SubWindow.alive() or not self.playing

    @property
    def stop(self) -> bool:
        return not self.event.is_set()

    @property
    def current_level(self) -> int:
        return self.__current_level

    @property
    def game_spend_time(self) -> float:
        extra = 0 if self.stop else perf_counter() - self.__game_start_time
        return self.__game_spend_time + extra

    @staticmethod
    def speed_up(_) -> None:
        Setting.PLAY_SPEED *= 2

    @staticmethod
    def restore_original_speed(_) -> None:
        Setting.PLAY_SPEED //= 2


class MusicPlayer:
    ROOT_PATH = path.join("resources", "Sound")
    MUSIC_FILES = ("bg_music.mp3", "be_attacked.mp3", "eat.mp3", "pause.ogg", "vectory.mp3", "fail.mp3")
    music_list = list()
    short_music_player = None
    long_music_player = None

    @classmethod
    def initialize(cls):
        for file in cls.MUSIC_FILES:
            music = media.load(path.join(cls.ROOT_PATH, file), streaming=False)
            cls.music_list.append(music)
        cls.short_music_player = media.Player()
        cls.long_music_player = media.Player()
        app.run()

    @classmethod
    def make_sound(cls, sound_id):
        if cls.short_music_player.playing:
            cls.short_music_player.next_source()
        cls.short_music_player.queue(cls.music_list[sound_id])
        cls.short_music_player.play()

    @classmethod
    def playback_loop(cls, music):
        while True:
            yield music

    @classmethod
    def start_game_music(cls):
        try:
            if cls.long_music_player.playing:
                cls.long_music_player.next_source()
            cls.long_music_player.queue(cls.playback_loop(cls.music_list[0]))
            cls.long_music_player.play()
        except AttributeError:
            from time import sleep
            sleep(0.2)
            cls.start_game_music()

    @classmethod
    def stop_game_music(cls):
        cls.long_music_player.pause()

    @classmethod
    def close(cls):
        app.exit()

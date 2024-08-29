from SubModule import SubWindow
from time import perf_counter
from pyglet import media, app
from json import load as js_load, JSONDecodeError


# 让我难过的是pyglet居然也是个GUI库，搞得一个GUI编程好不纯粹
class Setting(object):
    # 设置变量是相对静止的变量
    # 这些是直接设置变量，可以在设置中直接修改的
    PLAY_SPEED = 30 // 2
    RANDOM_FISH_SPEED = 10
    LIFE_VAL = 3
    REFRESH_SPEED = 3
    VECTORY_SCORE = 6000
    FISH_UPPER_NUM = 9
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
            # 小心，这里并没有去检查读取到字典后字典内部数据是否合法，不合法后续程序会直接崩溃
            file_setting_var = ("score_slice", "fish_size_slice", "fish_speed_slice", "weight")
            with open(r'resources/weight.json') as json_file:
                data = js_load(json_file)
                if not data["On"]:
                    return
                for var in file_setting_var:
                    setattr(cls, var, data[var])
        # 捕捉的错误包括: json文件语法不合法; json中找不到对应key; 更严重的是直接没有json文件
        except (JSONDecodeError, KeyError, OSError):
            return


class GameControl(object):
    # GameControl控制的是游戏中不断动态变化的变量
    # 由于要控制游戏，自然要与主游戏类BigEatSmall的实例做链接
    BigEatSmall_obj = None

    def __init__(self):
        self.life_lose = 0
        self.score = 0
        self.fish_count = 0  # 场面上鱼的数量, 除去玩家本身
        self.god = False  # 当前是否处于无敌时间
        self.playing = True  # 是否正在游戏中; 只有在游戏失败或成功时会被设置为False
        self.__stop = True
        self.__current_level = 0
        self.__game_start_time = 0    # 这也可以是暂停后游戏重新启动时的时间
        self.__game_spend_time = 0

    def update_level(self) -> None:
        if self.__current_level == len(Setting.score_slice):
            return
        if self.score > Setting.score_slice[self.__current_level]:
            self.__current_level += 1

    def frozen_window(self) -> None:
        if self.__stop:
            return
        self.__stop = True
        GameControl.BigEatSmall_obj.unbind_player_motion()
        self.__game_spend_time += (perf_counter() - self.__game_start_time)

    def unfrozen_window(self) -> None:
        if SubWindow.alive() or not self.playing:
            return
        GameControl.BigEatSmall_obj.bind_game_event()
        self.__stop = False
        self.__game_start_time = perf_counter()

    def stop_game(self, _) -> None:
        if self.stop:
            self.unfrozen_window()
        else:
            self.frozen_window()

    def filled_with_fish(self) -> bool:
        return self.fish_count > Setting.FISH_UPPER_NUM

    def dispose_god_time(self) -> None:
        self.god = False

    @property
    def stop(self) -> bool:
        return self.__stop

    @property
    def current_level(self) -> int:
        return self.__current_level

    @property
    def game_spend_time(self) -> int:
        return self.__game_spend_time

    @staticmethod
    def read_revise_info() -> dict:
        with open(r'resources/ReviseFish.json') as json_file:
            data = js_load(json_file)
            return data

    @staticmethod
    def speed_up(_) -> None:
        Setting.PLAY_SPEED *= 2

    @staticmethod
    def restore_original_speed(_) -> None:
        Setting.PLAY_SPEED //= 2


class MusicPlayer:
    AUDIO_FILE = "resources/be_attacked.mp3"
    music = None
    player = None

    @classmethod
    def initialize(cls):
        cls.music = media.load(cls.AUDIO_FILE, streaming=False)
        cls.player = media.Player()
        app.run()

    @classmethod
    def play(cls):
        cls.player.queue(cls.music)
        cls.player.play()

    @classmethod
    def close(cls):
        app.exit()

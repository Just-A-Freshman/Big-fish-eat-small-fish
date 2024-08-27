from tkinter import Tk, IntVar, Label, Scale, Button, HORIZONTAL
from os import startfile
from SubWindow import SubWindow
import json


s_font = "华文新魏"


class Setting(object):
    player_speed = 15
    random_speed_level = 2
    life_val = 3
    refresh_speed = 3
    vectory_score = 6000
    fish_upper_count = 9

    @classmethod
    def all_setting_param(cls):
        return (cls.player_speed, cls.random_speed_level, cls.life_val,
                cls.refresh_speed, cls.vectory_score, cls.fish_upper_count)

    @classmethod
    def load_weight(cls):
        try:
            # 小心，这里并没有去检查读取到字典后字典内部数据是否合法，不合法后续程序会直接崩溃
            with open(r'resources/weight.json') as json_file:
                data = json.load(json_file)
                if not data["On"]:
                    return
                GameControl.fish_size_slice = data["fish_size_slice"]
                GameControl.weight = data["weight"]
                GameControl.fish_size_slice = data["fish_size_slice"]

        except (json.JSONDecodeError, KeyError):
            return

    @classmethod
    def show_setting_window(cls, parent, game_obj):
        if GameControl.show_setting or not SubWindow.exist(parent):
            return
        GameControl.frozen_window()
        window_obj = SubWindow(parent, title="设置")
        setting_text = (
            '玩家移动速度:', '随机鱼移动速度', '玩家初始生命值:',
            '最晚出鱼秒数:', '胜利条件得分:', '在场鱼数量上限:',
        )
        setting_vals = ((10, 50), (1, 5), (1, 5), (1, 3), (2000, 30000), (5, 15),)
        default_vals = list(cls.__dict__.values())[1:7]
        required_save = list()
        for ly, tip, values, default_val in zip(
                range(50, 500, 50), setting_text, setting_vals, default_vals):
            int_val = IntVar(value=default_val)
            required_save.append(int_val)
            label = Label(window_obj.sub_window, text=tip, font=(s_font, 16))
            label.place(x=30 + 50, y=ly, width=150, height=30)
            slider = Scale(window_obj.sub_window, from_=values[0], to=values[1], variable=int_val,
                           orient=HORIZONTAL, bd=0)
            slider.place(x=190 + 50, y=ly - 17, width=150, height=60)
        window_obj.load_window_accessory()
        window_obj.confirm_btn.config(command=lambda: save(), text="保存")
        Button(window_obj.sub_window, bg="#FFA500", text="更多配置", font=(s_font, 15), command=lambda:
               startfile(r'resources/weight.json'), bd=0).place(width=80, height=30, x=520, y=0)
        Button(window_obj.sub_window, bg='#E34930', text="取消", bd=0, font=(s_font, 12),
               command=lambda: close()).place(width=80, height=20, y=335, x=420)

        def close():
            GameControl.unfrozen_window()
            window_obj.sub_window.destroy()

        def save():
            reset = cls.life_val != required_save[2].get()
            variables = list(cls.__dict__.keys())[1:7]
            for variable, data in zip(variables, required_save):
                setattr(cls, variable, data.get())
            game_obj.play_again() if reset else close()


class GameControl(object):
    # 难度: 前期一般难度 -> 中期到后期越来越难 -> 最后慢慢容易
    # 划分不同区域小鱼，中鱼，大鱼的权重
    game_obj: Tk | None = None
    current_level = 0
    life_lose = 0
    score = 0
    fish_count = 0  # 场面上鱼的数量, 除去玩家本身
    god = False  # 当前是否处于无敌时间
    stop = False
    bind_event = False
    show_setting = False  # 是否显示了设置窗口
    score_slice = (500, 1500, 2500, 3500, 5000, 7000)
    fish_size_slice = (0.5, 1, 2)
    fish_speed_slice = (12000, 8000, 4000, 1000, 500)
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
    def read_revise_info(cls):
        with open(r'resources/ReviseFish.json') as json_file:
            data = json.load(json_file)
            return data

    @classmethod
    def reset(cls):
        cls.current_level = cls.life_lose = cls.score = cls.fish_count = 0
        cls.god = cls.stop = cls.bind_event = cls.show_setting = False

    @classmethod
    def update_level(cls):
        if cls.current_level == 6:
            return
        if cls.score > cls.score_slice[cls.current_level]:
            cls.current_level += 1

    @classmethod
    def dispose_god_time(cls) -> None:
        cls.god = False

    @classmethod
    def frozen_window(cls) -> None:
        cls.game_obj.unbind("<Key-space>")
        cls.stop = True
        cls.bind_event = False

    @classmethod
    def unfrozen_window(cls) -> None:
        cls.game_obj.bind('<Key-space>', GameControl.stop_game)
        cls.show_setting = False
        cls.stop = False
        cls.bind_event = True

    # 阻塞函数
    @classmethod
    def join(cls) -> bool:
        return cls.stop or not cls.bind_event

    @classmethod
    def stop_game(cls, _) -> None:
        cls.stop = not cls.stop

    @staticmethod
    def speed_up(_) -> None:
        Setting.player_speed *= 2

    @staticmethod
    def restore_original_speed(_) -> None:
        Setting.player_speed //= 2

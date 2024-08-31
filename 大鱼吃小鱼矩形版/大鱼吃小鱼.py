from tkinter import Tk, Frame, Label, Button, Scale, IntVar, TclError, HORIZONTAL, PhotoImage
from random import randint, uniform, choices
from os import startfile
from threading import Thread
import json


class Setting(object):
    player_speed = 20
    random_speed_level = 2
    life_val = 3
    fish_upper_size = 240
    vectory_score = 6000
    fish_upper_count = 9

    @classmethod
    def load_weight(cls):
        try:
            # 小心，这里并没有去检查读取到字典后字典内部数据是否合法，不合法后续程序会直接崩溃
            with open(r'resources\weight.json')as json_file:
                data = json.load(json_file)
                if not data["On"]:
                    return
                GameInfo.fish_size_slice = data["fish_size_slice"]
                GameInfo.weight = data["weight"]
                GameInfo.fish_size_slice = data["fish_size_slice"]

        except (json.JSONDecodeError, KeyError):
            return

    @classmethod
    def save(cls, required_save: list[int]):
        reset = True if cls.life_val != required_save[2] else False
        variables = list(cls.__dict__.keys())[1:7]
        for variable, data in zip(variables, required_save):
            setattr(cls, variable, data)
        return reset


class GameInfo(object):
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

    def __init__(self):
        # 难度: 前期一般难度 -> 中期到后期越来越难 -> 最后慢慢容易
        # 划分不同区域小鱼，中鱼，大鱼的权重
        self.current_level = 0
        self.initial_pw, self.initial_ph = 40, 20
        self.pw, self.ph, self.px, self.py = self.initial_pw, self.initial_ph, 455, 250
        self.pf = 15
        self.life_lose = 0
        self.score = 0
        self.fish_count = 0    # 场面上鱼的数量, 除去玩家本身
        self.god = False       # 当前是否处于无敌时间
        self.stop = False
        self.bind_event = False
        self.show_setting = False         # 是否显示了设置窗口

    def update_level(self):
        if self.current_level == 6:
            return
        if self.score > self.score_slice[self.current_level]:
            self.current_level += 1


class BigEatSmall:
    def __init__(self, parent):
        self.parent: Tk | Frame = parent
        self.player: Label | None = None
        self.game_info = GameInfo()
        Setting.load_weight()
        self.basic_frame = Frame(self.parent)
        self.basic_frame.place(x=0, y=40, width=960, height=480)
        self.set_menu_bar()
        self.baffle = Label(self.parent, bg='#2AD95D')
        self.baffle.place(height=40, x=725, width=40 * (6 - Setting.life_val))
        self.score_label = Label(self.parent, bd=0, bg="#2AD95D", text="得分: 0", font=(s_font, 20))
        self.score_label.place(width=200, height=30, y=5, x=450)
        self.start_game()

    def set_menu_bar(self):
        bg_img_label = Label(self.basic_frame, image=bg_img)
        menu_bar = Label(self.parent, bg='#2AD95D')
        exit_button = Button(self.parent, bd=0, bg='#FFA500', text='退出', font=(s_font, 15),
                             command=lambda: self.game_quit())
        reset_button = Button(self.parent, bd=0, bg='#FFA500', text='重置', font=(s_font, 15),
                              command=lambda: self.play_again())
        setting_button = Button(self.parent, bd=0, bg="#FFA500", text='设置', font=(s_font, 15),
                                command=lambda: self.show_setting_window())
        for i in range(5):
            life_bar = Label(menu_bar, bg='red')
            life_bar.place(width=30, height=30, y=5, x=925 - 40 * i)
        menu_bar.place(width=960, height=40)
        bg_img_label.pack(expand=True)
        exit_button.place(width=100, height=30, y=5, x=5)
        reset_button.place(width=100, height=30, y=5, x=110)
        setting_button.place(width=100, height=30, y=5, x=215)

    @staticmethod
    def exist(widget, widget_property='bg') -> bool | str:
        try:
            temp = widget.cget(widget_property)
            return temp
        except (TclError, AttributeError):
            return False

    # 阻塞函数
    def join(self) -> bool:
        return self.game_info.stop or not self.game_info.bind_event

    def stop_game(self, _) -> None:
        if not self.game_info.stop:
            self.game_info.stop = True
        else:
            self.game_info.stop = False

    @staticmethod
    def speed_up(_) -> None:
        Setting.player_speed *= 2

    @staticmethod
    def restore_original_speed(_) -> None:
        Setting.player_speed //= 2

    def game_quit(self) -> None:
        self.basic_frame.destroy()
        self.parent.destroy()

    def play_again(self) -> None:
        self.basic_frame.destroy()
        self.__init__(self.parent)  # 重置函数
        self.game_info.stop = True

    def dispose_god_time(self) -> None:
        self.game_info.god = False

    def _move_up(self) -> None:
        if self.game_info.py - Setting.player_speed < 0:
            self.game_info.py = 0
        else:
            self.game_info.py -= Setting.player_speed

    def _move_down(self) -> None:
        if self.game_info.py + self.game_info.ph + Setting.player_speed > 480:
            self.game_info.py = 480 - self.game_info.ph
        else:
            self.game_info.py += Setting.player_speed

    def _move_left(self, anchor: str) -> None:
        if self.game_info.px < 0 or anchor == "e":
            self.player.config(anchor="w")
        else:
            self.game_info.px -= Setting.player_speed

    def _move_right(self, anchor: str) -> None:
        if self.game_info.px > 955 - self.game_info.pw or anchor == "w":
            self.player.config(anchor="e")
        else:
            self.game_info.px += Setting.player_speed

    def play_move(self, way):  # 玩家移动
        if self.join():
            return
        anchor = self.exist(self.player, 'anchor')
        if not anchor:
            return
        match way:
            case 'w': self._move_up()
            case 's': self._move_down()
            case 'a': self._move_left(anchor)
            case 'd': self._move_right(anchor)
        self.player.place(x=self.game_info.px, y=self.game_info.py, )

    def start_game(self):
        game_help_window = Frame(self.basic_frame)
        game_help_window.place(width=600, height=360, y=60, x=180)
        title = Label(game_help_window, text='帮助', bg='grey', font=(s_font, 15))
        title.place(width=600, height=30)
        tip = (f"按'w'、's'、'a'和'd'进行移动,\n 鼠标左键加速!\n空格键暂停游戏。\n"
               f"{Setting.vectory_score}分胜利,\n祝你好运！")
        help_info = Label(game_help_window, bg='#DEDEDE', font=(s_font, 20), text=tip)
        help_info.place(width=600, height=300, y=30)
        Label(game_help_window, bg='grey').place(width=600, height=30, y=330)
        confirm_btn = Button(game_help_window, bg='#22E02A', text='确定', bd=0,
                             font=(s_font, 12), command=lambda: start())
        confirm_btn.place(width=80, height=20, y=335, x=510)

        def start():
            game_help_window.destroy()
            game.bind('<Any-KeyPress>', lambda event: self.play_move(event.char))  # 键盘关联
            game.bind('<Key-space>', self.stop_game)
            game.bind('<Button-1>', self.speed_up)
            game.bind('<ButtonRelease-1>', self.restore_original_speed)
            self.player = Label(self.basic_frame, bg='black', fg='white',
                                font=('consolas', self.game_info.pf), text='O', anchor='w')
            self.player.place(width=self.game_info.pw, height=self.game_info.ph,
                              y=self.game_info.py, x=self.game_info.px)
            self.game_info.stop = False
            self.game_info.bind_event = True
            self.random_fish()

    def show_setting_window(self):
        if self.game_info.show_setting or not self.exist(self.basic_frame):
            return
        self.game_info.stop = self.game_info.show_setting = True
        self.game_info.bind_event = False
        setting_window = Frame(self.basic_frame)
        setting_window.place(width=600, height=360, y=60, x=180)
        title = Label(setting_window, text='设置', bg='grey', font=(s_font, 15))
        title.place(width=600, height=30)
        setting_text = (
            '玩家移动速度:', '随机鱼移动速度', '玩家初始生命值:',
            '随机鱼最大尺寸:', '胜利条件得分:', '在场鱼数量上限:',
        )
        setting_vals = ((10, 50), (1, 5), (1, 5), (80, 450), (2000, 30000), (5, 15),)
        default_vals = list(Setting.__dict__.values())[1:7]
        temp = list()
        for ly, tip, values, default_val in zip(
                range(50, 500, 50), setting_text, setting_vals, default_vals):
            int_val = IntVar(value=default_val)
            temp.append(int_val)
            from_, to = values
            label = Label(setting_window, text=tip, font=(s_font, 16))
            slider = Scale(setting_window, from_=from_, to=to, variable=int_val, orient=HORIZONTAL, bd=0)
            label.place(x=30+50, y=ly, width=150, height=30)
            slider.place(x=190+50, y=ly - 17, width=150, height=60)
        open_init_file_btn = Button(setting_window, bg="#FFA500", text="更多配置", font=(s_font, 15),
                                    command=lambda: startfile(r'resources\weight.json'), bd=0)
        cancel_btn = Button(setting_window, bg='#E34930', text="取消", bd=0,
                            font=(s_font, 12), command=lambda: close())
        confirm_btn = Button(setting_window, bg='#22E02A', text='保存', bd=0,
                             font=(s_font, 12), command=lambda: save())
        open_init_file_btn.place(width=80, height=30, x=520, y=0)
        cancel_btn.place(width=80, height=20, y=335, x=420)
        confirm_btn.place(width=80, height=20, y=335, x=510)

        def close():
            self.game_info.show_setting = self.game_info.stop = False
            self.game_info.bind_event = True
            setting_window.destroy()

        def save():
            reset = Setting.save([i.get() for i in temp])
            self.play_again() if reset else close()

    def victory(self):  # 胜利设定
        if self.game_info.score < Setting.vectory_score:
            return
        self.basic_frame.destroy()
        game.unbind('<All>')
        victory_window = Label(
            self.parent,
            bg='#FFFE91',
            font=(s_font, 100),
            text='- Victory -',
            fg='#FFA500'
        )
        victory_window.place(width=960, height=440, y=40)

    def death(self):  # 死亡设定
        self.game_info.life_lose += 1
        self.game_info.god = True
        self.basic_frame.after(3000, self.dispose_god_time)
        if self.game_info.life_lose < Setting.life_val:
            baffle_width = self.baffle.winfo_width() + 40
            self.baffle.place(height=40, x=725, width=baffle_width)
        else:
            self.baffle.place(height=40, x=725, width=235)
            game.unbind('<All>')
            dead_tip = Label(self.parent, bg='#FFFE91', font=(s_font, 100),
                             text='- You Dead -', fg='#FFA500')
            dead_tip.place(width=960, height=480, y=40)
            self.basic_frame.destroy()
            self.game_info.stop = True

    def eat_fish(self, fish, rw, rh, ry, rx):
        touch = False if (
                (self.game_info.px + self.game_info.pw < rx)
                or (rx + rw < self.game_info.px)
                or (self.game_info.py + self.game_info.ph < ry)
                or (ry + rh < self.game_info.py)
        ) else True

        if not touch:
            return
        if self.game_info.pw * self.game_info.ph > rw * rh:
            fish.destroy()
            self.game_info.fish_count -= 1
            self.game_info.score += rw + rh
            self.game_info.update_level()
            self.score_label.config(text=f'得分: {self.game_info.score}')
            self.game_info.pw = self.game_info.score // 40 + self.game_info.initial_pw
            self.game_info.ph = self.game_info.score // 80 + self.game_info.initial_ph
            self.game_info.pf = self.game_info.score // 100 + 15
            self.player.config(font=('consolas', self.game_info.pf))
            self.player.place(width=self.game_info.pw, height=self.game_info.ph)
            self.victory()
        elif not self.game_info.god:
            self.death()

    def fish_move(self, fish, speed, random_way, rw, rh, ry, rx):  # 鱼的移动
        if self.join():
            self.basic_frame.after(500, self.fish_move, fish, speed, random_way, rw, rh, ry, rx)
            return
        elif not self.exist(fish):
            return
        rx += speed if random_way == 'e' else -1 * speed
        fish.place(width=rw, height=rh, y=ry, x=rx)
        self.eat_fish(fish, rw, rh, ry, rx)

        if rx > 960 or rx + rw < 0:
            self.game_info.fish_count -= 1
            fish.destroy()
        else:
            self.basic_frame.after(10, self.fish_move, fish, speed, random_way, rw, rh, ry, rx)

    def slice_level_random_size(self):
        probabilities = self.game_info.weight[self.game_info.current_level]
        fish_size = choices((0, 1, 2), weights=probabilities, k=1)[0]
        rate1, rate2, rate3 = self.game_info.fish_size_slice
        match fish_size:
            case 0: return randint(10, int(self.game_info.ph * rate1))
            case 1: return randint(int(self.game_info.ph * rate1), int(self.game_info.ph * rate2))
            case 2: return randint(int(self.game_info.ph * rate2), int(self.game_info.ph * rate3))

    def random_fish(self):  # 随机刷新鱼
        if self.join() or self.game_info.fish_count > Setting.fish_upper_count - 1:
            # 鱼的刷新不敏感，但鱼动很敏感
            self.basic_frame.after(2000, self.random_fish)
            return
        elif not self.exist(self.basic_frame):
            return
        r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
        light = 0.3 * r + 0.59 * g + 0.11 * b
        fish_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
        eye_color = "#000000" if light > 127.5 else "#FFFFFF"
        speed_upper = (1.5 + self.game_info.score /
                       self.game_info.fish_speed_slice[Setting.random_speed_level-1])
        speed = uniform(0.3,  speed_upper)
        random_direction = ('w', 'e',)[randint(0, 1)]
        rh = min(self.slice_level_random_size(), Setting.fish_upper_size)
        rw = int(rh * uniform(1.2, 4))
        rx = -1 * rw if random_direction == 'e' else 960
        ry = randint(40, 480 - rh)
        rf = rh // 2
        fish = Label(self.basic_frame, bg=fish_color, font=('consolas', rf), fg=eye_color,
                     text='O', anchor=random_direction)
        fish.place(width=rw, height=rh, y=ry, x=rx)
        self.game_info.fish_count += 1
        Thread(target=self.fish_move, args=(fish, speed, random_direction, rw, rh, ry, rx)).start()
        self.basic_frame.after(randint(1000, 3000), self.random_fish)


if __name__ == "__main__":
    game = Tk()
    s_font = "华文新魏"
    bg_img = PhotoImage(file="resources//bg.png")
    Thread(target=lambda: game.iconbitmap("Resources/favicon.ico")).start()
    width, height = 960, 520
    screenwidth = game.winfo_screenwidth()
    screenheight = game.winfo_screenheight()
    geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    game.geometry(geometry)
    game.title('大鱼吃小鱼')
    game.resizable(False, False)
    BigEatSmall(game)
    game.mainloop()

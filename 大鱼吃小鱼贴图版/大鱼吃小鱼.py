from tkinter import Tk, Frame, Canvas, Label, Button, Scale, IntVar, TclError, HORIZONTAL, PhotoImage
from random import randint, uniform, choices, choice
from PIL import Image, ImageTk
from os import startfile, scandir, path
from threading import Thread
import json


class Setting(object):
    player_speed = 15
    random_speed_level = 2
    life_val = 3
    refresh_speed = 3
    vectory_score = 6000
    fish_upper_count = 9

    @classmethod
    def load_weight(cls):
        try:
            # 小心，这里并没有去检查读取到字典后字典内部数据是否合法，不合法后续程序会直接崩溃
            with open(r'resources\weight.json') as json_file:
                data = json.load(json_file)
                if not data["On"]:
                    return
                GameControl.fish_size_slice = data["fish_size_slice"]
                GameControl.weight = data["weight"]
                GameControl.fish_size_slice = data["fish_size_slice"]

        except (json.JSONDecodeError, KeyError):
            return

    @classmethod
    def save(cls, required_save: list[int]):
        reset = cls.life_val != required_save[2]
        variables = list(cls.__dict__.keys())[1:7]
        for variable, data in zip(variables, required_save):
            setattr(cls, variable, data)
        return reset


class GameControl(object):
    # 难度: 前期一般难度 -> 中期到后期越来越难 -> 最后慢慢容易
    # 划分不同区域小鱼，中鱼，大鱼的权重
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
        with open(r'resources\reviseFish.json') as json_file:
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

    @classmethod
    def bind_game_event(cls):
        game.bind('<Key-space>', cls.stop_game)
        game.bind('<Button-1>', cls.speed_up)
        game.bind('<ButtonRelease-1>', cls.restore_original_speed)


class Fish(object):
    basic_canvas: Canvas | None = None

    def __init__(self):
        self.image_id = 0
        self.anchor = 0  # 0代表左, 1代表右
        self.x0, self.y0, self.w0, self.h0 = 0, 0, 0, 0
        self.width: int = 0
        self.height: int = 0
        self.x: int = 0
        self.y: int = 0

    def load_revise_info(self, x0, y0, w0, h0):
        self.x0 = x0
        self.y0 = y0
        self.w0 = w0
        self.h0 = h0

    @property
    def revise_x(self):
        if self.anchor:
            return self.x + (1 - self.x0 - self.w0) * self.width
        else:
            return self.x + self.x0 * self.width

    @property
    def revise_y(self):
        return self.y + self.y0 * self.height

    @property
    def revise_w(self):
        return self.w0 * self.width

    @property
    def revise_h(self):
        return self.h0 * self.height

    def move(self):
        Fish.basic_canvas.move(
            self.image_id,
            self.x - Fish.basic_canvas.coords(self.image_id)[0],
            self.y - Fish.basic_canvas.coords(self.image_id)[1]
        )


class Player(Fish):
    initial_pw, initial_ph = 40, 20
    x0, y0, w0, h0 = GameControl.read_revise_info()["Player"]

    def __init__(self):
        super().__init__()
        self.x, self.y = 455, 250
        self.width, self.height = Player.initial_pw, Player.initial_ph
        self.load_revise_info(Player.x0, Player.y0, Player.w0, Player.h0)
        self.original_left_fish = Image.open(r"Resources/player_left.png")
        self.original_right_fish = Image.open(r"Resources/player_right.png")
        self.left_fish: PhotoImage | None = None
        self.right_fish: PhotoImage | None = None
        self.update_fish_img()

    def update_fish_img(self):
        left_fish = self.original_left_fish.resize((self.width, self.height))
        right_fish = self.original_right_fish.resize((self.width, self.height))
        self.left_fish = ImageTk.PhotoImage(left_fish)
        self.right_fish = ImageTk.PhotoImage(right_fish)
        self.image_id = super().basic_canvas.create_image(
            self.x, self.y,
            image=self.right_fish if self.anchor else self.left_fish,
            anchor="nw"
        )

    def bind_movement(self):
        game.bind('<Key-a>', self._move_left)
        game.bind('<Key-d>', self._move_right)
        game.bind('<Key-w>', self._move_up)
        game.bind('<Key-s>', self._move_down)

    def _move_up(self, _) -> None:
        if GameControl.stop:
            return
        elif self.y - Setting.player_speed < 0:
            self.y = 0
        else:
            self.y -= Setting.player_speed
        self.move()

    def _move_down(self, _) -> None:
        if GameControl.stop:
            return
        elif self.y + self.height + Setting.player_speed > 480:
            self.y = 480 - self.height
        else:
            self.y += Setting.player_speed
        self.move()

    def _move_left(self, _) -> None:
        if self.x < 0 or GameControl.stop:
            return
        if self.anchor:
            self.reversal()
        else:
            self.x -= Setting.player_speed
            self.move()

    def _move_right(self, _) -> None:
        if self.x - self.width > 955 or GameControl.stop:
            return
        if not self.anchor:
            self.reversal()
        else:
            self.x += Setting.player_speed
            self.move()

    def reversal(self):
        image = self.left_fish if self.anchor else self.right_fish
        self.anchor = not self.anchor
        super().basic_canvas.delete(self.image_id)
        self.image_id = super().basic_canvas.create_image(
            self.x, self.y, image=image, anchor="nw"
        )


class RandomFish(Fish):
    upper_size = 140
    small_upper, medium_upper, huge_upper = GameControl.fish_size_slice
    resource_dir = ("SmallFish", "MediumFish", "HugeFish")
    basic_player: Player | None = None
    # game: BigEatSmall | None = None
    game = None

    def __init__(self):
        super().__init__()
        # 生成的随机鱼是基于该玩家的大小的
        self.fish_img = None
        self.proportion = 1.2
        rough_size = RandomFish.random_rough_size()
        self.speed = RandomFish.random_speed()
        self.height = self.random_height(rough_size)
        self.width = self.random_width(rough_size)
        self.x = self.random_x()
        self.y = self.random_y()
        # 0 往左游; 1 往右游
        self.anchor = 1 if self.x < 0 else 0
        self.image_id = self.random_type(rough_size)

    def constant_move(self) -> None:
        if GameControl.join():
            super().basic_canvas.after(500, self.constant_move)
            return
        # 如果往右边游:
        if self.anchor:
            self.x += self.speed
            delete = self.x > 960
        else:
            self.x -= self.speed
            delete = self.x + self.width < 0
        if delete:
            GameControl.fish_count -= 1
            RandomFish.basic_canvas.delete(self.image_id)
            return
        else:
            self.eat_fish()
            try:
                self.move()
                super().basic_canvas.after(10, self.constant_move)
            except IndexError:
                return

    @classmethod
    def random_rough_size(cls) -> int:
        # 随机得出该鱼属于小型鱼，中型鱼还是大型鱼。0 - 1 - 2依次增大
        probabilities = GameControl.weight[GameControl.current_level]
        rough_fish_size = choices((0, 1, 2), weights=probabilities, k=1)[0]
        return rough_fish_size

    def random_type(self, size_id: int) -> int:
        dir_name = RandomFish.resource_dir[size_id]
        file_name = f"Resources/{dir_name}/{self.proportion}_{self.anchor}.png"
        if not path.exists(file_name):
            del self
            return 0
        img_obj = Image.open(file_name).resize((self.width, self.height))
        self.fish_img = ImageTk.PhotoImage(img_obj)
        # 生产出一条鱼
        image_id = super().basic_canvas.create_image(
            self.x, self.y,
            image=self.fish_img,
            anchor="nw"
        )
        return image_id

    @classmethod
    def random_speed(cls) -> float:
        temp = GameControl.fish_speed_slice[Setting.random_speed_level - 1]
        speed_upper = 1.5 + GameControl.score / temp
        return uniform(0.3, speed_upper)

    def random_x(self) -> int:
        # 这即是x坐标也是鱼出现时的方向，一值两用!
        return choice((-self.width, 960))

    def random_y(self) -> int:
        return randint(40, 480 - self.height)

    @classmethod
    def random_height(cls, rough_size: int) -> int:
        match rough_size:
            case 0:
                small_upper_size = int(cls.basic_player.height * RandomFish.small_upper)
                return min(randint(10, small_upper_size), 40)
            case 1:
                medium_lower_size = int(cls.basic_player.height * RandomFish.small_upper)
                medium_upper_size = int(cls.basic_player.height * RandomFish.medium_upper)
                return min(randint(medium_lower_size, medium_upper_size), 80)
            case 2:
                huge_lower_size = int(cls.basic_player.height * RandomFish.medium_upper)
                huge_upper_size = int(cls.basic_player.height * RandomFish.huge_upper)
                return min(randint(huge_lower_size, huge_upper_size), 120)

    def random_width(self, rough_size_id):
        rough_size = RandomFish.resource_dir[rough_size_id]
        target_folder = f"resources/{rough_size}"
        proportions = [float(i.name[:-6]) for i in scandir(target_folder)]
        self.proportion = choice(proportions)
        x0, y0, w0, h0 = GameControl.read_revise_info()[rough_size][str(self.proportion)]
        self.load_revise_info(x0, y0, w0, h0)
        fish_width = int(self.height * self.proportion)
        return fish_width

    def no_touch(self, surface=True):
        # surface=True -> 判断两个图层的外接矩形是否相交
        if surface:
            px, py = RandomFish.basic_player.x, RandomFish.basic_player.y
            pw, ph = RandomFish.basic_player.width, RandomFish.basic_player.height
            rx, ry, rw, rh = self.x, self.y, self.width, self.height
        else:
            px, py = RandomFish.basic_player.revise_x, RandomFish.basic_player.revise_y
            pw, ph = RandomFish.basic_player.revise_w, RandomFish.basic_player.revise_w
            rx, ry, rw, rh = self.revise_x, self.revise_y, self.revise_w, self.revise_h
        without_touch = px + pw < rx or rx + rw < px or py + ph < ry or ry + rh < py
        return without_touch

    def eat_fish(self):
        # 外接矩形未触碰，及时返回
        if self.no_touch():
            return
        # 图层未触碰，返回
        if self.no_touch(surface=False):
            return
        if (RandomFish.basic_player.width * RandomFish.basic_player.height
                > self.width * self.height):
            # 先把自己的图像给删了
            RandomFish.basic_canvas.delete(self.image_id)
            GameControl.fish_count -= 1
            GameControl.score += self.width + self.height
            GameControl.update_level()
            RandomFish.game.score_label.config(text=f'得分: {GameControl.score}')
            RandomFish.basic_player.width = GameControl.score // 40 + Player.initial_pw
            RandomFish.basic_player.height = GameControl.score // 80 + Player.initial_ph
            RandomFish.basic_player.update_fish_img()
            RandomFish.game.victory()
            # 最后把对自己的引用给删了
            del self
        elif not GameControl.god:
            RandomFish.game.death()


class BigEatSmall:
    def __init__(self, parent):
        self.parent: Tk | Frame = parent
        self.player: Player | None = None
        Setting.load_weight()
        self.basic_frame = Canvas(self.parent, borderwidth=0, highlightthickness=0)
        self.basic_frame.place(x=0, y=40, width=960, height=480)
        self.set_menu_bar()
        self.baffle = Label(self.parent, bg='#2AD95D')
        self.baffle.place(height=40, x=725, width=40 * (6 - Setting.life_val))
        self.score_label = Label(self.parent, bd=0, bg="#2AD95D", text="得分: 0", font=(s_font, 20))
        self.score_label.place(width=200, height=30, y=5, x=450)
        self.start_game()

    def set_menu_bar(self):
        self.basic_frame.create_image(0, 0, image=bg, anchor="nw")
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

    def game_quit(self) -> None:
        self.basic_frame.destroy()
        self.parent.destroy()

    def play_again(self) -> None:
        self.basic_frame.destroy()
        self.__init__(self.parent)  # 重置函数
        GameControl.reset()

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
            GameControl.read_revise_info()
            GameControl.bind_game_event()
            Fish.basic_canvas = self.basic_frame
            self.player = Player()
            self.player.bind_movement()
            GameControl.stop = False
            GameControl.bind_event = True
            RandomFish.basic_player = self.player
            RandomFish.game = self
            self.random_fish()

    def show_setting_window(self):
        if GameControl.show_setting or not self.exist(self.basic_frame):
            return
        GameControl.stop = GameControl.show_setting = True
        GameControl.bind_event = False
        setting_window = Frame(self.basic_frame)
        setting_window.place(width=600, height=360, y=60, x=180)
        title = Label(setting_window, text='设置', bg='grey', font=(s_font, 15))
        title.place(width=600, height=30)
        setting_text = (
            '玩家移动速度:', '随机鱼移动速度', '玩家初始生命值:',
            '最晚出鱼秒数:', '胜利条件得分:', '在场鱼数量上限:',
        )
        setting_vals = ((10, 50), (1, 5), (1, 5), (1, 3), (2000, 30000), (5, 15),)
        default_vals = list(Setting.__dict__.values())[1:7]
        print(default_vals)
        temp = list()
        for ly, tip, values, default_val in zip(
                range(50, 500, 50), setting_text, setting_vals, default_vals):
            int_val = IntVar(value=default_val)
            temp.append(int_val)
            from_, to = values
            label = Label(setting_window, text=tip, font=(s_font, 16))
            slider = Scale(setting_window, from_=from_, to=to, variable=int_val, orient=HORIZONTAL, bd=0)
            label.place(x=30 + 50, y=ly, width=150, height=30)
            slider.place(x=190 + 50, y=ly - 17, width=150, height=60)
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
            GameControl.show_setting = GameControl.stop = False
            GameControl.bind_event = True
            setting_window.destroy()

        def save():
            reset = Setting.save([i.get() for i in temp])
            self.play_again() if reset else close()

    def victory(self):  # 胜利设定
        if GameControl.score < Setting.vectory_score:
            return
        delattr(self, 'player')
        self.basic_frame.destroy()
        game.unbind('<All>')
        victory_window = Label(
            self.parent,
            bg='#FFFFD3',
            font=(s_font, 100),
            text='- Victory -',
            fg='#FFA500'
        )
        victory_window.place(width=960, height=440, y=40)

    def death(self):  # 死亡设定
        GameControl.life_lose += 1
        GameControl.god = True
        self.basic_frame.after(3000, GameControl.dispose_god_time)
        if GameControl.life_lose < Setting.life_val:
            baffle_width = self.baffle.winfo_width() + 40
            self.baffle.place(height=40, x=725, width=baffle_width)
        else:
            self.baffle.place(height=40, x=725, width=235)
            game.unbind('<All>')
            dead_tip = Label(
                self.parent,
                bg='#FFFFD3',
                font=(s_font, 100),
                text='- You Dead -',
                fg='#FFA500'
            )
            dead_tip.place(width=960, height=480, y=40)
            self.basic_frame.destroy()
            GameControl.stop = True

    def random_fish(self):  # 随机刷新鱼
        if GameControl.join() or GameControl.fish_count > Setting.fish_upper_count - 1:
            # 鱼的刷新不敏感，但鱼动很敏感
            self.basic_frame.after(2000, self.random_fish)
            return
        elif not self.exist(self.basic_frame):
            return
        fish = RandomFish()
        fish.constant_move()
        self.basic_frame.after(randint(0, Setting.refresh_speed * 1000), self.random_fish)


if __name__ == "__main__":
    game = Tk()
    s_font = "华文新魏"
    bg_img = Image.open(r"resources/bg.png")
    bg = ImageTk.PhotoImage(bg_img)
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

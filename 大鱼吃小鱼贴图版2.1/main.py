from tkinter import Tk, Frame, Canvas, Label, Button
from random import randint
from time import perf_counter
from threading import Thread
from PIL import Image, ImageTk
from Setting import Setting, GameControl
from FishControl import Fish, Player, RandomFish
from Rank import RankWindow
from SubWindow import SubWindow


class BigEatSmall:
    def __init__(self, parent):
        self.parent: Tk | Frame = parent
        self.player: Player | None = None
        self.start_time = 0
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
        reset_btn = Button(self.parent, bd=0, bg='#FFA500', text='重置', font=(s_font, 15),
                           command=lambda: self.play_again())
        setting_btn = Button(self.parent, bd=0, bg="#FFA500", text='设置', font=(s_font, 15),
                             command=lambda: Setting.show_setting_window(self.basic_frame, self))
        show_rank_btn = Button(self.parent, bd=0, bg='#FFA500', text='排行榜', font=(s_font, 15),
                               command=lambda: RankWindow.show_rank_window(self.basic_frame))
        for i in range(5):
            life_bar = Label(menu_bar, bg='red')
            life_bar.place(width=30, height=30, y=5, x=925 - 40 * i)
        menu_bar.place(width=960, height=40)
        reset_btn.place(width=100, height=30, y=5, x=5)
        setting_btn.place(width=100, height=30, y=5, x=110)
        show_rank_btn.place(width=100, height=30, y=5, x=215)

    def play_again(self) -> None:
        self.basic_frame.destroy()
        self.__init__(self.parent)    # 重置函数
        GameControl.reset()

    def start_game(self):
        window_obj = SubWindow(self.basic_frame, "帮助")
        window_obj.load_window_accessory()
        window_obj.confirm_btn.config(command=lambda: start())
        tip = (f"按'w'、's'、'a'和'd'进行移动,\n 鼠标左键加速!\n空格键暂停游戏。\n"
               f"{Setting.vectory_score}分胜利,\n祝你好运！")
        help_info = Label(window_obj.sub_window, bg='#DEDEDE', font=(s_font, 20), text=tip)
        help_info.place(width=600, height=300, y=30)

        def start():
            window_obj.sub_window.destroy()
            GameControl.read_revise_info()
            Fish.basic_canvas = self.basic_frame
            self.player = Player()
            self.bind_game_event()
            GameControl.stop = GameControl.show_setting = False
            GameControl.bind_event = True
            RandomFish.basic_player = self.player
            RandomFish.game = self
            self.start_time = perf_counter()
            self.random_fish()

    def victory(self):  # 胜利设定
        if GameControl.score < Setting.vectory_score:
            return
        using_time = perf_counter() - self.start_time
        GameControl.frozen_window()
        RankWindow.export(using_time)
        win_tip = Label(self.basic_frame, font=(s_font, 100), text=" - 胜 利 -",
                        bg="#D90021", fg="#FFC900")
        win_tip.place(x=0, y=40, height=160, width=960)

    def death(self):  # 死亡设定
        GameControl.life_lose += 1
        GameControl.god = True
        self.basic_frame.after(3000, GameControl.dispose_god_time)
        baffle_width = self.baffle.winfo_width() + 40
        self.baffle.place(height=40, x=725, width=baffle_width)
        if GameControl.life_lose >= Setting.life_val:
            GameControl.frozen_window()
            dead_tip = Label(self.basic_frame, bg="#ABABAB", font=(s_font, 100),
                             text='- 失 败 -', fg="#1F0302")
            dead_tip.place(x=0, y=40, height=160, width=960)

    def bind_game_event(self):
        game.bind('<Key-space>', GameControl.stop_game)
        game.bind('<Button-1>', GameControl.speed_up)
        game.bind('<ButtonRelease-1>', GameControl.restore_original_speed)
        game.bind('<Key-a>', self.player.move_left)
        game.bind('<Key-d>', self.player.move_right)
        game.bind('<Key-w>', self.player.move_up)
        game.bind('<Key-s>', self.player.move_down)

    def random_fish(self):  # 随机刷新鱼
        if GameControl.join() or GameControl.fish_count > Setting.fish_upper_count - 1:
            # 鱼的刷新不敏感，但鱼动很敏感
            self.basic_frame.after(2000, self.random_fish)
            return
        elif not SubWindow.exist(self.basic_frame):
            return
        fish = RandomFish()
        fish.constant_move()
        self.basic_frame.after(randint(0, Setting.refresh_speed * 1000), self.random_fish)


if __name__ == "__main__":
    game = Tk()
    s_font = "华文新魏"
    bg_img = Image.open(r"resources/image/bg.png")
    bg = ImageTk.PhotoImage(bg_img)
    Thread(target=lambda: game.iconbitmap("resources/image/favicon.ico")).start()
    GameControl.game_obj = game
    width, height = 960, 520
    screenwidth = game.winfo_screenwidth()
    screenheight = game.winfo_screenheight()
    geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    game.geometry(geometry)
    game.title('大鱼吃小鱼')
    game.resizable(False, False)
    BigEatSmall(game)
    game.mainloop()

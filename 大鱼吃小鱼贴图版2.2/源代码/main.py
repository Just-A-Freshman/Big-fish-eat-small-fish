from tkinter import Tk, Canvas
from tkinter.ttk import Entry
from random import randint
from threading import Thread
from PIL import Image, ImageTk
from Setting import Setting, GameControl, MusicPlayer
from FishControl import Fish, Player, RandomFish
from SubModule import *


BE_ATTACKED_SOUND = "resources/be_attacked.mp3"
BG_IMG_PATH = "resources/image/bg.png"
ICO_PATH = "resources/image/favicon.ico"


class BigEatSmall(object):
    def __init__(self, parent):
        self.parent: Tk | Frame = parent
        self.player: Player | None = None
        self.game_control = GameControl()
        self.setting_init()
        self.basic_frame = Canvas(self.parent, borderwidth=0, highlightthickness=0)
        self.basic_frame.place(x=0, y=40, width=960, height=480)
        self.set_menu_bar()
        self.baffle = Label(self.parent, bg='#2AD95D')
        self.baffle.place(height=40, x=725, width=40 * (6 - Setting.LIFE_VAL))
        self.score_label = Label(self.parent, bd=0, bg="#2AD95D", text="得分: 0", font=(s_font, 20))
        self.score_label.place(width=200, height=30, y=5, x=450)
        self.start_game()

    def set_menu_bar(self):
        def bind_command():
            reset_btn.config(command=lambda: self.play_again())
            setting_btn.config(command=lambda: self.show_setting_window())
            show_rank_btn.config(command=lambda: self.show_rank_window())
        self.basic_frame.create_image(0, 0, image=bg, anchor="nw")
        menu_bar = Label(self.parent, bg='#2AD95D')
        reset_btn = Button(self.parent, bd=0, bg='#FFA500', text='重置', font=(s_font, 15))
        setting_btn = Button(self.parent, bd=0, bg="#FFA500", text='设置', font=(s_font, 15))
        show_rank_btn = Button(self.parent, bd=0, bg='#FFA500', text='排行榜', font=(s_font, 15))
        for i in range(5):
            life_bar = Label(menu_bar, bg='red')
            life_bar.place(width=30, height=30, y=5, x=925 - 40 * i)
        menu_bar.place(width=960, height=40)
        reset_btn.place(width=100, height=30, y=5, x=5)
        setting_btn.place(width=100, height=30, y=5, x=110)
        show_rank_btn.place(width=100, height=30, y=5, x=215)
        Thread(target=bind_command).start()

    def show_setting_window(self):
        setting_window = ShowSettingWindow(self.basic_frame, self, self.game_control)
        setting_window.show_setting_window()

    def show_rank_window(self):
        rank_window = ShowRankWindow(self.basic_frame, self.game_control)
        rank_window.show_rank_window()

    def setting_init(self):
        game.bind("<Button-1>", GameControl.speed_up)
        game.bind("<ButtonRelease-1>", GameControl.restore_original_speed)
        Setting.load_weight_setting()
        GameControl.BigEatSmall_obj = self
        ShowSettingWindow.setting_class = Setting
        ShowRankWindow.setting_class = Setting

    def play_again(self) -> None:
        SubWindow.clear()
        self.basic_frame.destroy()
        self.__init__(self.parent)    # 重置函数

    def start_game(self):
        # 先把之前游戏的各种绑定关系取消掉
        window_obj = SubWindow(self.basic_frame, "帮助", "help")
        window_obj.load_window_accessory()
        window_obj.confirm_btn.config(command=lambda: start())
        tip = (f"按'w'、's'、'a'和'd'进行移动,\n 鼠标左键加速!\n空格键暂停游戏。\n"
               f"{Setting.VECTORY_SCORE}分胜利,\n祝你好运！")
        help_info = Label(window_obj.sub_window, bg='#DEDEDE', font=(s_font, 20), text=tip)
        help_info.place(width=600, height=300, y=30)

        def start():
            window_obj.destroy()
            GameControl.read_revise_info()
            Fish.basic_canvas = self.basic_frame
            self.player = Player(self.game_control)
            self.game_control.bind_event = True
            Thread(target=self.bind_game_event).start()
            RandomFish.basic_player = self.player
            RandomFish.game_control = self.game_control
            RandomFish.big_eat_small = self
            self.game_control.unfrozen_window()
            self.random_fish()

    def victory(self):  # 胜利设定
        if self.game_control.score < Setting.VECTORY_SCORE:
            return
        self.game_control.frozen_window()
        self.game_control.playing = False
        win_tip = Label(self.basic_frame, font=(s_font, 100), text=" - 胜 利 -", bg="#D90021", fg="#FFC900")
        win_tip.place(y=40, height=160, width=960)
        self.basic_frame.create_text(435, 245, text="为你的胜利记录取个名吧!", font=(s_font, 20))
        vectory_record_entry = Entry(self.basic_frame, )
        vectory_record_entry.place(x=280, y=270, width=400, height=40)
        ensure_btn = Button(self.basic_frame, text="确认", bg="#22B14C", font=(s_font, 15))
        ensure_btn.place(x=680, y=270, height=40)
        ensure_btn.config(command=lambda: self.record_in_rank(vectory_record_entry.get()))

    def record_in_rank(self, record_name):
        record_name = record_name.strip()
        if len(record_name) == 0:
            ask_no = messagebox.askyesno("提示", "您确定不为您的记录命个名吗?")
            if not ask_no:
                return
            record_name = "无名的人"
        elif len(record_name) > 15:
            messagebox.showinfo("提示", "名字有点太长了哦，最长限制15个字~")
            return
        rank_window = ShowRankWindow(self.basic_frame, self.game_control)
        rank_window.export(record_name)
        messagebox.showinfo("提示", "您的成绩已被录入排行榜!")
        self.play_again()

    def death(self):  # 死亡设定
        MusicPlayer.play()
        self.game_control.life_lose += 1
        self.game_control.god = True
        self.basic_frame.after(3000, self.game_control.dispose_god_time)
        baffle_width = self.baffle.winfo_width() + 40
        self.baffle.place(height=40, x=725, width=baffle_width)
        if self.game_control.life_lose < Setting.LIFE_VAL:
            return
        self.game_control.frozen_window()
        self.game_control.playing = False
        dead_tip = Label(self.basic_frame, bg="#ABABAB", font=(s_font, 100), text='- 失 败 -', fg="#1F0302")
        dead_tip.place(y=40, height=160, width=960)

    def bind_game_event(self):
        game.bind('<Key-space>', self.game_control.stop_game)
        game.bind('<Key-a>', self.player.move_left)
        game.bind('<Key-d>', self.player.move_right)
        game.bind('<Key-w>', self.player.move_up)
        game.bind('<Key-s>', self.player.move_down)

    @staticmethod
    def unbind_player_motion():
        player_motion = ("<Key-a>", "<Key-d>", "<Key-w>", "<Key-s>")
        for motion in player_motion:
            game.unbind(motion)

    def random_fish(self):  # 随机刷新鱼
        if self.game_control.stop or self.game_control.filled_with_fish():
            # 鱼的刷新不敏感，但鱼动很敏感
            self.basic_frame.after(2000, self.random_fish)
            return
        fish = RandomFish()
        fish.constant_move()
        self.basic_frame.after(randint(0, Setting.REFRESH_SPEED * 1000), self.random_fish)


if __name__ == "__main__":
    game = Tk()
    bg_img = Image.open(BG_IMG_PATH)
    bg = ImageTk.PhotoImage(bg_img)
    Thread(target=lambda: game.iconbitmap(ICO_PATH)).start()
    Thread(target=MusicPlayer().initialize).start()
    width, height = 960, 520
    screenwidth = game.winfo_screenwidth()
    screenheight = game.winfo_screenheight()
    geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    game.geometry(geometry)
    game.title('大鱼吃小鱼')
    game.resizable(False, False)
    BigEatSmall(game)
    game.mainloop()
    MusicPlayer.close()

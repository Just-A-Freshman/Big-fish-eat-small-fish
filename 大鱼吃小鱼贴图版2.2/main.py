from tkinter import Tk, Canvas, TclError
from tkinter.ttk import Entry
from threading import Thread
from random import randint
from PIL import Image, ImageTk
from FishControl import *
from SubModule import *
import Setting as env



class MainGUI(Tk):
    def __init__(self):
        super().__init__()
        self.set_window()
        self.background = self.set_background()
        self.menu_bar = self.set_menu_bar()
        self.reset_btn = self.set_reset_btn()
        self.setting_btn = self.set_setting_btn()
        self.ranking_list_btn = self.set_ranking_list_btn()
        self.basic_frame = self.set_basic_frame()
        self.score_label = self.set_score_label()
        self.clock = self.set_clock()
        self.life_bars = self.set_life_bar()
        Thread(target=lambda: self.iconbitmap(env.ICO_PATH)).start()

    def set_window(self):
        screenwidth, screenheight = self.winfo_screenwidth(), self.winfo_screenheight()
        geometry = f'{env.WIDTH}x{env.HEIGHT+40}+{(screenwidth-env.WIDTH)//2}+{(screenheight-env.HEIGHT)//2}'
        self.geometry(geometry)
        self.title('大鱼吃小鱼')
        self.resizable(False, False)

    def set_background(self) -> ImageTk.PhotoImage:
        bg_img = Image.open(env.BG_IMG_PATH)
        return ImageTk.PhotoImage(bg_img)

    def set_basic_frame(self) -> Canvas:
        basic_frame = Canvas(self, borderwidth=0, highlightthickness=0)
        basic_frame.create_image(0, 0, image=self.background, anchor="nw")
        basic_frame.place(x=0, y=40, width=env.WIDTH, height=env.HEIGHT)
        return basic_frame

    def set_menu_bar(self) -> Label:
        menu_bar = Label(self, bg='#2AD95D')
        menu_bar.place(height=40, x=0, width=env.WIDTH)
        return menu_bar

    def set_reset_btn(self) -> Button:
        reset_btn = Button(self.menu_bar, bd=0, bg='#FFA500', text='重置', font=(env.FONT, 16))
        reset_btn.place(width=100, height=30, y=5, x=5)
        return reset_btn

    def set_setting_btn(self) -> Button:
        setting_btn = Button(self.menu_bar, bd=0, bg="#FFA500", text='设置', font=(env.FONT, 16))
        setting_btn.place(width=100, height=30, y=5, x=110)
        return setting_btn

    def set_ranking_list_btn(self) -> Button:
        ranking_list_btn = Button(self.menu_bar, bd=0, bg='#FFA500', text='排行榜', font=(env.FONT, 16))
        ranking_list_btn.place(width=100, height=30, y=5, x=215)
        return ranking_list_btn

    def set_score_label(self) -> Label:
        score_label = Label(self.menu_bar, bd=0, bg="#2AD95D", text="得分: 0", font=(env.FONT, 20))
        score_label.place(width=180, height=30, y=5, x=360)
        return score_label

    def set_clock(self) -> Label:
        clock = Label(self.menu_bar, bd=0, bg="#2AD95D", text="用时: 0", font=(env.FONT, 20))
        clock.place(width=180, height=30, y=5, x=540)
        return clock

    def set_life_bar(self) -> list[Label]:
        life_bars: list[Label] = []
        special_font = ("Segoe UI Emoji", 22)
        for i in range(5):
            life_bar = Label(self.menu_bar, text="♥", bg='#2AD95D', font=special_font, fg="#2AD95D")
            life_bar.place(width=30, height=35, y=0, x=910 - 40 * i)
            life_bars.append(life_bar)
        for i in range(env.Setting.LIFE_VAL):
            life_bars[i].config(fg="#ED1C24")
        return life_bars

    def set_vectory_window(self) -> tuple[Label, Entry, Button]:
        win_tip = Label(self.basic_frame, font=(env.FONT, 100), text=" - 胜 利 -", bg="#D90021", fg="#FFC900")
        win_tip.place(y=40, height=160, width=960)
        self.basic_frame.create_text(435, 245, text="为你的胜利记录取个名吧!", font=(env.FONT, 20))
        vectory_record_entry = Entry(self.basic_frame)
        vectory_record_entry.place(x=280, y=270, width=400, height=40)
        ensure_btn = Button(self.basic_frame, text="确认", bg="#22B14C", font=(env.FONT, 15))
        ensure_btn.place(x=680, y=270, height=40)
        return win_tip, vectory_record_entry, ensure_btn

    def set_fail_window(self) -> tuple[Label, Button]:
        fail_tip = Label(self.basic_frame, bg="#ABABAB", font=(env.FONT, 100), text='- 失 败 -', fg="#1F0302")
        fail_tip.place(y=40, height=160, width=960)
        self.basic_frame.create_text(435, 245, text=f"想要获胜还需努力!", font=(env.FONT, 20))
        return fail_tip



class MainControl(MainGUI):
    def __init__(self):
        super().__init__()
        self.player: Player | None = None
        self.game_control: env.GameControl = env.GameControl(self)
        Thread(target=env.MusicPlayer().initialize).start()
        self.bind_command()
        self.bind_event()
        self.setting_init()
        self.show_help_window()

    def bind_command(self):
        self.reset_btn.config(command=lambda: self.play_again())
        self.setting_btn.config(command=lambda: self.show_setting_window())
        self.ranking_list_btn.config(command=lambda: self.show_rank_window())

    def bind_event(self):  
        self.bind("<Button-1>", self.game_control.speed_up)
        self.bind("<ButtonRelease-1>", self.game_control.restore_original_speed)
        self.bind('<Key-space>', self.game_control.stop_game)

    def bind_player_motion(self):
        self.bind('<Key-a>', self.player.move_left)
        self.bind('<Key-d>', self.player.move_right)
        self.bind('<Key-w>', self.player.move_up)
        self.bind('<Key-s>', self.player.move_down)

    def unbind_player_motion(self):
        player_motion = ("<Key-a>", "<Key-d>", "<Key-w>", "<Key-s>")
        for motion in player_motion:
            self.unbind(motion)

    def setting_init(self):
        env.Setting.load_weight_setting()
        SubWindow.game_control = self.game_control
        RandomFish.game_control = self.game_control
        CollisionDetection.main_control = self

    def show_help_window(self):
        help_window = ShowHelpWindow(self.basic_frame)
        help_window.show_help_window()
        help_window.window_obj.confirm_btn.config(command=lambda: self.start_game(help_window))

    def show_setting_window(self):
        setting_window = ShowSettingWindow(self.basic_frame, self)
        setting_window.show_setting_window()

    def show_rank_window(self):
        rank_window = ShowRankWindow(self.basic_frame)
        rank_window.show_rank_window()

    def refresh_clock(self):
        self.clock.config(text=f"用时: {int(self.game_control.game_spend_time)}")
        self.after(1000, self.refresh_clock)

    def reset_life_bar(self):
        for life_bar in self.life_bars[:env.Setting.LIFE_VAL]:
            life_bar.config(fg="#ED1C24")
        for life_bar in self.life_bars[env.Setting.LIFE_VAL:]:
            life_bar.config(fg="#2AD95D")

    def play_again(self) -> None:
        self.game_control.event.set()
        env.MusicPlayer.stop_game_music()
        SubWindow.clear()
        self.basic_frame.destroy()
        self.basic_frame = self.set_basic_frame()
        self.game_control.__init__(self)
        self.clock.config(text="用时: 0")
        self.score_label.config(text="得分: 0")
        self.reset_life_bar()
        self.show_help_window()

    def start_game(self, help_window: ShowHelpWindow):
        Fish.basic_canvas = self.basic_frame
        self.player = Player()
        self.bind_player_motion()
        help_window.window_obj.destroy(space_stop=False)
        env.MusicPlayer.start_game_music()
        self.refresh_clock()
        self.random_fish()

    def record_in_rank(self, record_name: str) -> None:
        record_name = record_name.strip()
        record_name_length = len(record_name)
        if record_name_length == 0:
            if not messagebox.askyesno("提示", "您确定不为您的记录命个名吗?"):
                return
            record_name = env.DEFAULT_NAME
        elif record_name_length > 15:
            return messagebox.showinfo("提示", "名字有点太长了哦，最长限制15个字~")
        rank_window = ShowRankWindow(self.basic_frame)
        rank_window.export(record_name)
        messagebox.showinfo("提示", "您的成绩已被录入排行榜!")
        self.play_again()

    def random_fish(self):
        if self.game_control.stop or self.game_control.filled_with_fish():
            return self.basic_frame.after(2000, self.random_fish)
        try:
            fish = RandomFish()
            fish.constant_move()
            self.game_control.fish_count += 1
            refresh_time = 500 if self.game_control.fish_count < 4 else randint(0, env.Setting.REFRESH_SPEED * 1000)
            self.basic_frame.after(refresh_time, self.random_fish)
        except TclError:
            return
        
    def victory(self):
        env.MusicPlayer.make_sound(2)
        if self.game_control.score < env.Setting.VECTORY_SCORE:
            return
        self.game_control.frozen_window()
        env.MusicPlayer.make_sound(4)
        self.game_control.playing = False
        _, record_entry, ensure_btn = self.set_vectory_window()
        ensure_btn.config(command=lambda: self.record_in_rank(record_entry.get()))
        
    def death(self):
        env.MusicPlayer.make_sound(1)
        self.game_control.life_lose += 1
        self.game_control.god = True
        self.game_control.monitor_dispose_god_time(self.game_control.game_spend_time)
        rest_life_val = env.Setting.LIFE_VAL - self.game_control.life_lose
        self.life_bars[rest_life_val].config(fg="#7F7F7F")
        if rest_life_val > 0:
            return
        self.game_control.frozen_window()
        env.MusicPlayer.make_sound(5)
        self.game_control.playing = False
        self.set_fail_window()


if __name__ == "__main__":
    game = MainControl()
    game.mainloop()
    env.MusicPlayer.close()

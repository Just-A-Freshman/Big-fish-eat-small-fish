"""
该模块是用于对接[设置窗口]、[排行榜窗口]等子窗口的出现
"""
import sqlite3
from json import load
from tkinter import Button, Frame, Label, IntVar, Scale, HORIZONTAL, Menu, messagebox
from tkinter.ttk import Treeview
from os import startfile, path
from math import log
from typing import Optional, Dict
import Setting as env




class SubWindow(object):
    game_control: 'env.GameControl' = None
    __instance_pool = dict()
    __redraw_opp = 5

    def __new__(cls, *args):
        flag = args[2]
        if flag in cls.__instance_pool:
            cls.__instance_pool[flag].sub_window.place(x=0.23*env.WIDTH, y=0.15*env.HEIGHT)
            return False
        else:
            obj = super().__new__(cls)
            cls.__instance_pool[flag] = obj
            return obj

    def __init__(self, parent, title, flag):
        # flag标识是为了避免不断创建的同一类型的窗口，当遇到同一个flag时就不会创建对应实例
        self.__flag = flag
        self.__push: bool = False
        self.__motion_times = 0
        self.__original_pos: tuple = tuple()
        self.parent = parent
        self.sub_window = self.__show_window(title)
        self.confirm_btn: Button | None = None

    @classmethod
    def alive(cls) -> bool:
        return len(cls.__instance_pool) != 0

    @classmethod
    def clear(cls) -> None:
        cls.__instance_pool.clear()

    def __show_window(self, title="") -> Frame:
        window = Frame(self.parent)
        title = Label(window, text=title, bg='grey', font=(env.FONT, 15))
        title.place(width=600, height=30)
        title.bind("<ButtonPress-1>", self.__start_move)
        title.bind("<ButtonRelease-1>", self.__end_move)
        title.bind("<Motion>", self.__move_window)
        window.place(width=600, height=360, x=0.23*env.WIDTH, y=0.15*env.HEIGHT)
        return window

    def load_window_accessory(self) -> None:
        sub_bar = Label(self.sub_window, bg='grey')
        sub_bar.place(width=600, height=30, y=330)
        self.confirm_btn = Button(self.sub_window, bg='#22E02A', text='确定', bd=0,
                                  font=(env.FONT, 12), command=self.destroy)
        self.confirm_btn.place(width=80, height=20, y=335, x=510)

    def destroy(self, space_stop=True) -> None:
        self.sub_window.destroy()
        SubWindow.__instance_pool.pop(self.__flag)
        SubWindow.game_control.unfrozen_window()
        if not self.alive() and space_stop:
            SubWindow.game_control.stop_game(0)

    def __start_move(self, event) -> None:
        self.__original_pos = (event.x_root, event.y_root)
        self.__push = True

    def __end_move(self, _) -> None:
        self.__push = False

    def __move_window(self, event) -> None:
        if not self.__push:
            return
        self.__motion_times += 1
        if self.__motion_times != SubWindow.__redraw_opp:
            return
        self.__motion_times = 0
        push_x, push_y = self.__original_pos
        self.__original_pos = (event.x_root, event.y_root)
        dx, dy = event.x_root - push_x, event.y_root - push_y
        new_x, new_y = self.sub_window.winfo_x() + dx, self.sub_window.winfo_y() + dy
        self.sub_window.place(x=new_x, y=new_y)


class ShowHelpWindow(object):
    def __init__(self, basic_frame):
        self.basic_frame = basic_frame
        self.window_obj: Optional[SubWindow] = None

    def show_help_window(self) -> None:
        self.window_obj = SubWindow(self.basic_frame, "帮助", "help")
        self.window_obj.load_window_accessory()
        tip = (f"按'w'、's'、'a'和'd'进行移动,\n 鼠标左键加速!\n空格键暂停游戏。\n"
               f"{env.Setting.VECTORY_SCORE}分胜利,\n祝你好运！")
        help_info = Label(self.window_obj.sub_window, bg='#DEDEDE', font=(env.FONT, 24), text=tip)
        help_info.place(width=600, height=300, y=30)


class ShowSettingWindow(object):
    setting_text = (
        '玩家移动速度:', '随机鱼移动速度', '玩家初始生命值:',
        '最晚出鱼秒数:', '胜利条件得分:', '在场鱼数量上限:',
    )
    setting_vals = ((10, 50), (7, 15), (1, 5), (1, 3), (2000, 30000), (5, 15),)

    def __init__(self, parent, big_eat_small_obj):
        self.parent = parent
        self.window_obj: Optional[SubWindow] = False
        self.big_eat_small_obj = big_eat_small_obj

    def show_setting_window(self) -> None:
        cls = ShowSettingWindow
        self.window_obj = SubWindow(self.parent, "设置", "setting")
        if not self.window_obj:
            return
        SubWindow.game_control.frozen_window()
        default_vals = list(env.Setting.__dict__.values())[1:7]
        scales: list[Scale] = []
        for ly, tip, values, default_val in zip(
                range(50, 500, 50), cls.setting_text, cls.setting_vals, default_vals
        ):
            int_val = IntVar(value=default_val)
            Label(self.window_obj.sub_window, text=tip, font=(env.FONT, 16)).place(
                x=30 + 50, y=ly, width=150, height=30)
            scale = Scale(self.window_obj.sub_window, from_=values[0], to=values[1],
                          variable=int_val, orient=HORIZONTAL, bd=0)
            scale.place(x=190 + 50, y=ly - 17, width=150, height=60)
            scales.append(scale)
        self.window_obj.load_window_accessory()
        self.window_obj.confirm_btn.config(command=lambda: self.check_save(scales), text="保存")
        Button(self.window_obj.sub_window, bg="#FFA500", text="更多配置", font=(env.FONT, 15), command=lambda:
               startfile(path.abspath(env.WEIGHT_FILE)), bd=0).place(width=80, height=30, x=520, y=0)
        Button(self.window_obj.sub_window, bg='#E34930', text="取消", bd=0, font=(env.FONT, 12),
               command=self.window_obj.destroy).place(width=80, height=20, y=335, x=420)

    def check_save(self, scales: list) -> None:
        def save(player_again: bool):
            variables = list(env.Setting.__dict__.keys())[1:7]
            for variable, data in zip(variables, scales):
                setattr(env.Setting, variable, data.get())
            self.big_eat_small_obj.play_again() if player_again else self.window_obj.destroy()

        life_val_unchanged = env.Setting.LIFE_VAL == scales[2].get()
        vectory_score_unchanged = env.Setting.VECTORY_SCORE == scales[4].get()
        if life_val_unchanged and vectory_score_unchanged:
            save(player_again=False)
            return
        message = "您在设置中修改了胜利条件得分或初始生命值, \n您确定要重新开始游戏吗?"
        reset = messagebox.askyesno("提示", message)
        if reset:
            save(player_again=True)
        else:
            scales[2].set(env.Setting.LIFE_VAL)
            scales[4].set(env.Setting.VECTORY_SCORE)


class ShowRankWindow(object):
    protectedTopN = 3
    columns = ("排名", "记录名", "加权得分", "用时/s", "消耗生命", "参数列表")
    column_width = (80, 140, 80, 80, 80, 140)

    def __init__(self, parent):
        self.parent = parent
        self.score_tree: Optional[Treeview] = None

    @staticmethod
    def load_compute_score_weight():
        with open(env.SCORING_MECHANISM) as json_file:
            data: dict = load(json_file)
        for value in data.values():
            yield value

    def show_rank_window(self) -> None:
        cls = ShowRankWindow
        SubWindow.game_control.frozen_window()
        window_obj = SubWindow(self.parent, "排行榜", "rank")
        if not window_obj:
            return
        window_obj.load_window_accessory()
        self.score_tree = Treeview(window_obj.sub_window)
        self.score_tree.bind("<Button-3>", self.create_menu)
        self.score_tree['columns'] = cls.columns
        for column, colwidth in zip(cls.columns, cls.column_width):
            self.score_tree.column(column, width=colwidth, anchor="center")
            self.score_tree.heading(column, text=column)
        self.score_tree.place(x=-200, y=30, height=300)
        for index, row_data in enumerate(cls.load_data()):
            self.score_tree.insert('', index, values=(index+1, *row_data))

    def create_menu(self, event) -> None:
        item = self.score_tree.identify_row(event.y)
        if len(item) == 0:
            return
        self.score_tree.selection_set(item)
        menu = Menu(self.score_tree, tearoff=0, font=(env.FONT, 14))
        menu.add_command(label="删除记录", command=lambda: self.delete_record(item))
        menu.post(event.x_root, event.y_root)

    def delete_record(self, item) -> None:
        rank, record_name, weighted_score, using_time, _, _ = self.score_tree.item(item)["values"]
        if rank <= ShowRankWindow.protectedTopN:
            messagebox.showinfo("提示", f"排行榜前{ShowRankWindow.protectedTopN}名荣耀加身，无法删除!")
            return
        if not messagebox.askyesno("提示", "您确定要删除这条记录吗?"):
            return
        try:
            connect = sqlite3.connect(env.DB_PATH)
            cursor = connect.cursor()
            condition = (f"weighted_score = {weighted_score} AND "
                         f"record_name = '{record_name}' AND using_time = {using_time}")
            delete_sql = f"DELETE FROM Rank WHERE {condition};"
            cursor.execute(delete_sql)
            connect.commit()
            self.score_tree.delete(item)
        except sqlite3.OperationalError:
            messagebox.showerror("错误", "删除失败，未能在数据库中找到该记录!")

    def weighted_score(self) -> float:
        # 加载json数据
        json_dict = self.load_compute_score_weight()
        ub, weights, life_weight, goal_score_weight = json_dict
        w1, w2, w3 = weights.values()
        life_weight_score = self.get_life_weight_score(life_weight)
        goal_weight_score = self.get_goal_weight_score(goal_score_weight)
        time_weight_score = self.get_time_weight_score()
        return (w1 * life_weight_score + w2 * goal_weight_score + w3 * time_weight_score) * ub

    @staticmethod
    def get_goal_weight_score(goal_score_weight: Dict[str, float]) -> float:
        goal = env.Setting.VECTORY_SCORE
        goal_slice_lst = list(map(int, goal_score_weight.keys()))
        goal_weight_lst = list(goal_score_weight.values())
        for index, score_span in enumerate(goal_slice_lst):
            if goal > score_span:
                continue
            if goal == score_span:
                current_goal_span = score_span
                next_goal_span = goal_slice_lst[index + 1]
                current_weight = goal_weight_lst[index]
                next_weight = goal_weight_lst[index + 1]
            else:
                current_goal_span = goal_slice_lst[index - 1]
                next_goal_span = score_span
                current_weight = goal_weight_lst[index - 1]
                next_weight = goal_weight_lst[index]
            exceed_proportion = (goal - current_goal_span) / (next_goal_span - current_goal_span)
            res = current_weight + exceed_proportion * (next_weight - current_weight)
            return res

    def get_life_weight_score(self, life_weight: Dict[str, float]) -> float:
        life_lose = SubWindow.game_control.life_lose
        life_lose_score = life_weight[str(life_lose)]
        return life_lose_score

    def get_time_weight_score(self) -> float:
        goal_score = env.Setting.VECTORY_SCORE
        real_using_time = SubWindow.game_control.game_spend_time
        fastest_using_time = self.fastest_cube(goal_score)
        if real_using_time <= fastest_using_time:
            exceed_time = fastest_using_time - real_using_time
            return 1 + 0.02 * exceed_time
        exceed_time = real_using_time - fastest_using_time
        exceed_proportion = exceed_time / fastest_using_time
        if exceed_proportion < 0.3:
            # < 0.3 至少拿70%的分数
            return 1 - exceed_proportion
        elif exceed_proportion < 1:
            # < 1 至少拿30%的分数
            exceed_proportion -= 0.3
            return 0.7 - 0.4 / 0.7 * exceed_proportion
        elif exceed_proportion < 2:
            exceed_proportion -= 1
            return 0.3 - 0.2 * exceed_proportion
        else:
            return 0.0

    @staticmethod
    def fastest_cube(x) -> int:
        # 最速曲线, 返回一个达到该目标分数(x)的最短用时(理论)
        if x < 10000:
            a, b, c = (-1.35694582e-06, 2.81099658e-02, 4.21697530e+00)
            return a * (x ** 2) + b * x + c
        else:
            a, b, c = (6.30983920e+01, 2.49623641e-02, -1.97593406e+02)
            return a * log(b * x) + c

    def export(self, record_name) -> None:
        # 简单的将排行榜中新的数据写入数据库文件
        ShowRankWindow.create_table()
        connect = sqlite3.connect(env.DB_PATH)
        cursor = connect.cursor()
        weighted_score = self.weighted_score()
        using_time = SubWindow.game_control.game_spend_time
        life_lose = SubWindow.game_control.life_lose
        # 第一次知道原来多行字符串不是str，而是tuple
        insert_sql = (f"INSERT INTO Rank VALUES ("
                      f"'{record_name}', {weighted_score:.2f}, {using_time:.2f}, {life_lose},"
                      f"'{env.Setting.setting_param()}');")
        cursor.execute(insert_sql)
        connect.commit()

    @classmethod
    def create_table(cls) -> None:
        connect = sqlite3.connect(env.DB_PATH)
        cursor = connect.cursor()
        create_table_sql = """CREATE TABLE IF NOT EXISTS "Rank"(record_name TEXT, weighted_score REAL,
                              using_time REAL, lose_life INTEGER, extra_param TEXT);""",
        create_index_sql = "CREATE INDEX IF NOT EXISTS rankIndex ON Rank (weighted_score);"
        cursor.execute(create_table_sql[0])
        cursor.execute(create_index_sql)
        connect.commit()

    @classmethod
    def load_data(cls) -> tuple:
        cls.create_table()
        connect = sqlite3.connect(env.DB_PATH)
        cursor = connect.cursor()
        select_sql = "SELECT * FROM RANK ORDER BY weighted_score DESC;"
        cursor.execute(select_sql)
        data = cursor.fetchall()
        connect.commit()
        return data
    

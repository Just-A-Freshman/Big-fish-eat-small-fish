"""
该模块是用于对接[设置窗口]、[排行榜窗口]等子窗口的出现
"""
import sqlite3
from tkinter import Button, Frame, Label, IntVar, Scale, HORIZONTAL, Menu, messagebox
from tkinter.ttk import Treeview
from os import startfile

s_font = "华文新魏"
DB_PATH = "resources/Rank.db"


class SubWindow(object):
    __instance_pool = dict()
    __redraw_opp = 4

    def __new__(cls, *args, **kwargs):
        flag = args[2]
        if flag in cls.__instance_pool:
            cls.__instance_pool[flag].sub_window.place(x=180, y=60)
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
    def alive(cls):
        return len(cls.__instance_pool) != 0

    @classmethod
    def clear(cls):
        cls.__instance_pool.clear()

    def __show_window(self, title=""):
        window = Frame(self.parent)
        title = Label(window, text=title, bg='grey', font=(s_font, 15))
        title.place(width=600, height=30)
        title.bind("<ButtonPress-1>", self.__start_move)
        title.bind("<ButtonRelease-1>", self.__end_move)
        title.bind("<Motion>", self.__move_window)
        window.place(width=600, height=360, y=60, x=180)
        return window

    def load_window_accessory(self):
        sub_bar = Label(self.sub_window, bg='grey')
        sub_bar.place(width=600, height=30, y=330)
        self.confirm_btn = Button(self.sub_window, bg='#22E02A', text='确定', bd=0, font=(s_font, 12),
                                  command=lambda: self.sub_window.destroy())
        self.confirm_btn.place(width=80, height=20, y=335, x=510)

    def destroy(self):
        self.sub_window.destroy()
        SubWindow.__instance_pool.pop(self.__flag)

    def __start_move(self, event):
        self.__original_pos = (event.x_root, event.y_root)
        self.__push = True

    def __end_move(self, _):
        self.__push = False

    def __move_window(self, event):
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


class ShowSettingWindow(object):
    # setting_class应为Setting.py下的Setting类
    setting_class = None
    setting_text = (
        '玩家移动速度:', '随机鱼移动速度', '玩家初始生命值:',
        '最晚出鱼秒数:', '胜利条件得分:', '在场鱼数量上限:',
    )
    setting_vals = ((10, 50), (7, 15), (1, 5), (1, 3), (2000, 30000), (5, 15),)

    def __init__(self, parent, big_eat_small_obj, game_control_obj):
        self.parent = parent
        self.window_obj: SubWindow | bool = False
        self.big_eat_small_obj = big_eat_small_obj
        self.game_control_obj = game_control_obj

    def show_setting_window(self):
        cls = ShowSettingWindow
        self.window_obj = SubWindow(self.parent, "设置", "setting")
        if not self.window_obj:
            return
        self.game_control_obj.frozen_window()
        default_vals = list(cls.setting_class.__dict__.values())[1:7]
        scales: list[Scale] = []
        for ly, tip, values, default_val in zip(
                range(50, 500, 50), cls.setting_text, cls.setting_vals, default_vals
        ):
            int_val = IntVar(value=default_val)
            Label(self.window_obj.sub_window, text=tip, font=(s_font, 16)).place(
                x=30 + 50, y=ly, width=150, height=30)
            scale = Scale(self.window_obj.sub_window, from_=values[0], to=values[1],
                          variable=int_val, orient=HORIZONTAL, bd=0)
            scale.place(x=190 + 50, y=ly - 17, width=150, height=60)
            scales.append(scale)
        self.window_obj.load_window_accessory()
        self.window_obj.confirm_btn.config(command=lambda: self.check_save(scales), text="保存")
        Button(self.window_obj.sub_window, bg="#FFA500", text="更多配置", font=(s_font, 15), command=lambda:
               startfile(r'resources/weight.json'), bd=0).place(width=80, height=30, x=520, y=0)
        Button(self.window_obj.sub_window, bg='#E34930', text="取消", bd=0, font=(s_font, 12),
               command=lambda: self.close_window()).place(width=80, height=20, y=335, x=420)

    def close_window(self):
        self.window_obj.destroy()
        self.game_control_obj.unfrozen_window()

    def check_save(self, scales: list):
        cls = ShowSettingWindow

        def save(player_again: bool):
            variables = list(cls.setting_class.__dict__.keys())[1:7]
            for variable, data in zip(variables, scales):
                setattr(cls.setting_class, variable, data.get())
            self.big_eat_small_obj.play_again() if player_again else self.close_window()
        life_val_unchanged = cls.setting_class.LIFE_VAL == scales[2].get()
        vectory_score_unchanged = cls.setting_class.VECTORY_SCORE == scales[4].get()
        if life_val_unchanged and vectory_score_unchanged:
            save(player_again=False)
            return
        message = "您在设置中修改了胜利条件得分或初始生命值, \n您确定要重新开始游戏吗?"
        reset = messagebox.askyesno("提示", message)
        if reset:
            save(player_again=True)
        else:
            scales[2].set(cls.setting_class.LIFE_VAL)
            scales[4].set(cls.setting_class.VECTORY_SCORE)


class ShowRankWindow(object):
    setting_class = None
    protectedTopN = 5
    columns = ("排名", "记录名", "加权得分", "用时/s", "消耗生命", "参数列表")
    column_width = (80, 140, 80, 80, 80, 140)

    def __init__(self, parent, game_control_obj):
        self.parent = parent
        self.game_control_obj = game_control_obj
        self.score_tree: Treeview | None = None

    def show_rank_window(self):
        cls = ShowRankWindow
        self.game_control_obj.frozen_window()
        window_obj = SubWindow(self.parent, "排行榜", "rank")
        if not window_obj:
            return
        window_obj.load_window_accessory()
        window_obj.confirm_btn.config(command=lambda: close_window())
        self.score_tree = Treeview(window_obj.sub_window)
        self.score_tree.bind("<Button-3>", self.create_menu)
        self.score_tree['columns'] = cls.columns
        for column, colwidth in zip(cls.columns, cls.column_width):
            self.score_tree.column(column, width=colwidth, anchor="center")
            self.score_tree.heading(column, text=column)
        self.score_tree.place(x=-200, y=30, height=300)
        for index, row_data in enumerate(cls.load_data()):
            self.score_tree.insert('', index, values=(index+1, *row_data))

        def close_window():
            self.score_tree.destroy()
            window_obj.destroy()
            self.game_control_obj.unfrozen_window()

    def create_menu(self, event):
        item = self.score_tree.identify_row(event.y)
        if len(item) == 0:
            return
        self.score_tree.selection_set(item)
        menu = Menu(self.score_tree, tearoff=0, font=(s_font, 14))
        menu.add_command(label="删除记录", command=lambda: self.delete_record(item))
        menu.post(event.x_root, event.y_root)

    def delete_record(self, item):
        rank, record_name, weighted_score, using_time, _, _ = self.score_tree.item(item)["values"]
        if rank <= ShowRankWindow.protectedTopN:
            messagebox.showinfo("提示", "排行榜前5名荣耀加身，无法删除!")
            return
        if not messagebox.askyesno("提示", "您确定要删除这条记录吗?"):
            return
        try:
            connect = sqlite3.connect(DB_PATH)
            cursor = connect.cursor()
            # 将加权分数, 记录名以及使用时间作为唯一标识, 极小概率会出现重合, 除非代码刻意构造
            condition = (f"weighted_score = {weighted_score} AND "
                         f"record_name = '{record_name}' AND using_time = {using_time}")
            delete_sql = f"DELETE FROM Rank WHERE {condition};"
            cursor.execute(delete_sql)
            connect.commit()
            self.score_tree.delete(item)
        except sqlite3.OperationalError:
            messagebox.showerror("错误", "删除失败，未能在数据库中找到该记录!")

    def weighted_score(self):
        using_time = self.game_control_obj.game_spend_time
        return (
                ShowRankWindow.setting_class.VECTORY_SCORE -
                self.game_control_obj.life_lose * 1000 -
                using_time - 18 * using_time
        )

    def export(self, record_name):
        # 简单的将排行榜中新的数据写入数据库文件
        ShowRankWindow.create_table()
        connect = sqlite3.connect(DB_PATH)
        cursor = connect.cursor()
        weighted_score = self.weighted_score()
        using_time = self.game_control_obj.game_spend_time
        life_lose = self.game_control_obj.life_lose
        # 第一次知道原来多行字符串不是str，而是tuple
        insert_sql = (f"INSERT INTO Rank VALUES ("
                      f"'{record_name}', {weighted_score:.2f}, {using_time:.2f}, {life_lose},"
                      f"'{ShowRankWindow.setting_class.setting_param()}');")
        cursor.execute(insert_sql)
        connect.commit()

    @classmethod
    def create_table(cls):
        connect = sqlite3.connect(DB_PATH)
        cursor = connect.cursor()
        create_table_sql = """CREATE TABLE IF NOT EXISTS "Rank"(record_name TEXT, weighted_score REAL,
                              using_time REAL, lose_life INTEGER, extra_param TEXT);""",
        create_index_sql = "CREATE INDEX IF NOT EXISTS rankIndex ON Rank (weighted_score);"
        cursor.execute(create_table_sql[0])
        cursor.execute(create_index_sql)
        connect.commit()

    @classmethod
    def load_data(cls):
        cls.create_table()
        connect = sqlite3.connect(DB_PATH)
        cursor = connect.cursor()
        select_sql = "SELECT * FROM RANK ORDER BY weighted_score DESC;"
        cursor.execute(select_sql)
        data = cursor.fetchall()
        connect.commit()
        return data

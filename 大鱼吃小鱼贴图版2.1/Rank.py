from tkinter.ttk import Treeview
from os import path
import sqlite3
from Setting import GameControl, Setting
from SubWindow import SubWindow


class RankWindow(object):
    show_window = False

    @classmethod
    def create_table(cls):
        connect = sqlite3.connect("resources/Rank.db")
        cursor = connect.cursor()
        create_table_sql = """CREATE TABLE IF NOT EXISTS "Rank"(
                                        weighted_score INTEGER,
                                        using_time INTEGER,
                                        goal_score INTEGER,
                                        lose_life INTEGER,
                                        extra_param TEXT
                                    );""",
        create_index_sql = "CREATE INDEX IF NOT EXISTS rankIndex ON Rank (weighted_score);"
        cursor.execute(create_table_sql[0])
        cursor.execute(create_index_sql)
        connect.commit()

    @classmethod
    def show_rank_window(cls, parent):
        if cls.show_window:
            return
        GameControl.frozen_window()
        GameControl.show_setting = True
        cls.show_window = True
        window_obj = SubWindow(parent, "排行榜")
        window_obj.load_window_accessory()
        window_obj.confirm_btn.config(command=lambda: cls.close_window(window_obj.sub_window))
        score_tree = Treeview(window_obj.sub_window)
        columns = ("排名", "加权得分", "用时", "消耗生命", "目标分数", "参数列表")
        column_width = (70, 100, 100, 70, 100, 160)
        score_tree['columns'] = columns
        for column, colwidth in zip(columns, column_width):
            score_tree.column(column, width=colwidth)
            score_tree.heading(column, text=column)
        score_tree.place(x=-200, y=30, height=300)
        for index, row_data in enumerate(cls.load_data()):
            score_tree.insert('', index, values=(index+1, *row_data))

    @classmethod
    def close_window(cls, window):
        GameControl.unfrozen_window()
        cls.show_window = False
        window.destroy()

    @classmethod
    def load_data(cls):
        # 这里就是简单的读取SQLite数据库，然后排序，最后将数据展示在树图中
        if not path.exists("resources/Rank.db"):
            return ()
        cls.create_table()
        connect = sqlite3.connect("resources/Rank.db")
        cursor = connect.cursor()
        select_sql = "SELECT * FROM RANK ORDER BY weighted_score DESC;"
        cursor.execute(select_sql)
        data = cursor.fetchall()
        connect.commit()
        return data

    @classmethod
    def export(cls, using_time):
        # 简单的将排行榜中新的数据写入数据库文件
        cls.create_table()
        connect = sqlite3.connect("resources/Rank.db")
        cursor = connect.cursor()
        # 这只是随便糊弄上去的一个公式，后期还会改进这个公式!
        weighted_score = cls.weighted_score(using_time)
        # 第一次知道原来多行字符串不是str，而是tuple
        insert_sql = (f"INSERT INTO Rank VALUES ("
                      f"{weighted_score:.2f}, {using_time:.2f}, {GameControl.life_lose},"
                      f"{Setting.vectory_score}, '{Setting.all_setting_param()}');")
        cursor.execute(insert_sql)
        connect.commit()

    @classmethod
    def weighted_score(cls, using_time):
        return Setting.vectory_score - GameControl.life_lose * 1000 - using_time - 18 * using_time

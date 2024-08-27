from tkinter import Button, Frame, Label, TclError


class SubWindow(object):
    def __init__(self, parent, title):
        self.__push: bool = False
        self.__original_pos: tuple = tuple()
        self.parent = parent
        self.sub_window = self.__show_window(title)
        self.confirm_btn: Button | None = None

    @staticmethod
    def exist(widget, widget_property='bg') -> bool | str:
        try:
            temp = widget.cget(widget_property)
            return temp
        except (TclError, AttributeError):
            return False

    def __refresh_push_state(self, event, value: bool):
        if value:
            self.__original_pos = (event.x_root, event.y_root)
        self.__push = value

    def move_window(self, event):
        if not self.__push:
            return
        push_x, push_y = self.__original_pos
        self.__original_pos = (event.x_root, event.y_root)
        dx, dy = event.x_root - push_x, event.y_root - push_y
        new_x, new_y = self.sub_window.winfo_x() + dx, self.sub_window.winfo_y() + dy
        self.sub_window.place(x=new_x, y=new_y)

    def __show_window(self, title=""):
        window = Frame(self.parent)
        title = Label(window, text=title, bg='grey', font=("华文新魏", 15))
        title.place(width=600, height=30)
        title.bind("<ButtonPress-1>", lambda event: self.__refresh_push_state(event, True))
        title.bind("<ButtonRelease-1>", lambda event: self.__refresh_push_state(event, False))
        title.bind("<Motion>", lambda event: self.move_window(event))
        window.place(width=600, height=360, y=60, x=180)
        return window

    def load_window_accessory(self):
        sub_bar = Label(self.sub_window, bg='grey')
        sub_bar.place(width=600, height=30, y=330)
        self.confirm_btn = Button(self.sub_window, bg='#22E02A', text='确定', bd=0, font=("华文新魏", 12),
                                  command=lambda: self.sub_window.destroy())
        self.confirm_btn.place(width=80, height=20, y=335, x=510)

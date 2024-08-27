from tkinter import Canvas, PhotoImage
from PIL import Image, ImageTk
from Setting import GameControl, Setting
from random import choices, choice, uniform, randint
from os import path, scandir


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
        self.original_left_fish = Image.open(r"resources/image/player_left.png")
        self.original_right_fish = Image.open(r"resources/image/player_right.png")
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

    def move_up(self, _) -> None:
        if GameControl.stop:
            return
        elif self.y - Setting.player_speed < 0:
            self.y = 0
        else:
            self.y -= Setting.player_speed
        self.move()

    def move_down(self, _) -> None:
        if GameControl.stop:
            return
        elif self.y + self.height + Setting.player_speed > 480:
            self.y = 480 - self.height
        else:
            self.y += Setting.player_speed
        self.move()

    def move_left(self, _) -> None:
        if self.x < 0 or GameControl.stop:
            return
        if self.anchor:
            self.reversal()
        else:
            self.x -= Setting.player_speed
            self.move()

    def move_right(self, _) -> None:
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

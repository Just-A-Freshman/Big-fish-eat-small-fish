from tkinter import Canvas, PhotoImage
from Setting import GameControl, Setting
from random import choices, choice, uniform, randint
from os import path, scandir
from PIL import Image, ImageTk


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

    def __init__(self, game_control):
        super().__init__()
        self.game_control = game_control
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
        if self.y - Setting.PLAY_SPEED < 0:
            self.y = 0
        else:
            self.y -= Setting.PLAY_SPEED
        self.move()

    def move_down(self, _) -> None:
        if self.y + self.height + Setting.PLAY_SPEED > 480:
            self.y = 480 - self.height
        else:
            self.y += Setting.PLAY_SPEED
        self.move()

    def move_left(self, _) -> None:
        if self.x < 0:
            return
        if self.anchor:
            self.reversal()
        else:
            self.x -= Setting.PLAY_SPEED
            self.move()

    def move_right(self, _) -> None:
        if self.x + self.width > 955:
            return
        if not self.anchor:
            self.reversal()
        else:
            self.x += Setting.PLAY_SPEED
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
    small_upper, medium_upper, huge_upper = Setting.fish_size_slice
    resource_dir = ("SmallFish", "MediumFish", "HugeFish")
    basic_player: Player | None = None
    # 因为要生产的鱼的实例太多了，不好一个个传入game_control实例对象，所以改用类变量来接受
    game_control: GameControl | None = None
    # game: BigEatSmall | None = None
    big_eat_small = None

    def __init__(self):
        super().__init__()
        # 生成的随机鱼是基于该玩家的大小的
        self.__fish_img = None
        self.__proportion = 1.2
        rough_size = RandomFish.__random_rough_size()
        self.speed = RandomFish.__random_speed()
        self.height = self.__random_height(rough_size)
        self.width = self.__random_width(rough_size)
        self.x = self.__random_x()
        self.y = self.__random_y()
        self.anchor = 0  # 0 往右游; 1 往左游
        self.__out_of_border = self.__move_left
        self.__initialize_anchor()
        self.image_id = self.__random_type(rough_size)

    def constant_move(self) -> None:
        if self.game_control.stop:
            super().basic_canvas.after(500, self.constant_move)
            return
        if self.__out_of_border():
            self.__destroy()
            return
        try:
            self.__eat_fish()
            self.move()
            super().basic_canvas.after(22-Setting.RANDOM_FISH_SPEED, self.constant_move)
        except IndexError:
            return

    def __initialize_anchor(self):
        if self.x < 0:
            self.anchor = 1
            self.__out_of_border = self.__move_right

    def __move_left(self) -> bool:
        # 返回是否越界
        self.x -= self.speed
        return self.x + self.width < 0

    def __move_right(self) -> bool:
        self.x += self.speed
        return self.x > 960

    def __destroy(self):
        RandomFish.game_control.fish_count -= 1
        RandomFish.basic_canvas.delete(self.image_id)

    @classmethod
    def __random_rough_size(cls) -> int:
        # 随机得出该鱼属于小型鱼，中型鱼还是大型鱼。0 - 1 - 2依次增大
        probabilities = Setting.weight[cls.game_control.current_level]
        rough_fish_size = choices((0, 1, 2), weights=probabilities, k=1)[0]
        return rough_fish_size

    def __random_type(self, size_id: int) -> int:
        dir_name = RandomFish.resource_dir[size_id]
        file_name = f"Resources/{dir_name}/{self.__proportion}.png"
        if not path.exists(file_name):
            return 0
        img_obj = Image.open(file_name).resize((self.width, self.height))
        if self.anchor:
            img_obj = img_obj.transpose(Image.FLIP_LEFT_RIGHT)
        self.__fish_img = ImageTk.PhotoImage(img_obj)
        # 生产出一条鱼
        image_id = super().basic_canvas.create_image(
            self.x, self.y,
            image=self.__fish_img,
            anchor="nw"
        )
        return image_id

    @classmethod
    def __random_speed(cls) -> float:
        speed_upper = 1.5 + cls.game_control.score / 7000
        return uniform(0.3, speed_upper)

    def __random_x(self) -> int:
        # 这即是x坐标也是鱼出现时的方向，一值两用!
        return choice((-self.width, 960))

    def __random_y(self) -> int:
        return randint(40, 480 - self.height)

    @classmethod
    def __random_height(cls, rough_size: int) -> int:
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

    def __random_width(self, rough_size_id):
        rough_size = RandomFish.resource_dir[rough_size_id]
        target_folder = f"resources/{rough_size}"
        proportions = [float(i.name[:3]) for i in scandir(target_folder)]
        self.__proportion = choice(proportions)
        x0, y0, w0, h0 = GameControl.read_revise_info()[rough_size][str(self.__proportion)]
        self.load_revise_info(x0, y0, w0, h0)
        fish_width = int(self.height * self.__proportion)
        return fish_width

    def __no_touch(self, surface=True):
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

    def __eat_fish(self):
        # 外接矩形未触碰，及时返回
        if self.__no_touch():
            return
        # 图层未触碰，返回
        if self.__no_touch(surface=False):
            return
        if (RandomFish.basic_player.width * RandomFish.basic_player.height
                > self.width * self.height):
            RandomFish.basic_canvas.delete(self.image_id)
            RandomFish.game_control.fish_count -= 1
            RandomFish.game_control.score += self.width + self.height
            RandomFish.game_control.update_level()
            RandomFish.big_eat_small.score_label.config(text=f'得分: {RandomFish.game_control.score}')
            RandomFish.basic_player.width = RandomFish.game_control.score // 40 + Player.initial_pw
            RandomFish.basic_player.height = RandomFish.game_control.score // 80 + Player.initial_ph
            RandomFish.basic_player.update_fish_img()
            RandomFish.big_eat_small.victory()
            # 最后把对自己的引用给删了
            del self
        elif not RandomFish.game_control.god:
            RandomFish.big_eat_small.death()

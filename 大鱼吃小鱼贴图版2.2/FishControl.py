from tkinter import Canvas, PhotoImage, TclError
from random import choices, choice, uniform, randint
from os import path, scandir
from PIL import Image, ImageTk
from typing import TYPE_CHECKING
import threading
import json
import Setting as env


if TYPE_CHECKING:
    from main import MainControl


class Fish(object):
    basic_canvas: Canvas | None = None

    def __init__(self):
        self.image_id = 0
        self.anchor = 0  # 0代表左, 1代表右
        self.width, self.height = env.Setting.PLAYER_INITIAL_W, env.Setting.PLAYER_INITIAL_H
        self.x, self.y = 0, 0
        self.life_val = 0

    def move(self) -> None:
        Fish.basic_canvas.move(
            self.image_id,
            self.x - Fish.basic_canvas.coords(self.image_id)[0],
            self.y - Fish.basic_canvas.coords(self.image_id)[1]
        )


class Player(Fish):
    def __init__(self):
        super().__init__()
        CollisionDetection.player = self
        self.x = self.basic_canvas.winfo_width() // 2 - env.Setting.PLAYER_INITIAL_W // 2
        self.y = self.basic_canvas.winfo_height() // 2 - env.Setting.PLAYER_INITIAL_H // 2
        self.original_left_fish: Image.Image = Image.open(r"resources/image/player_left.png")
        self.original_right_fish: Image.Image = Image.open(r"resources/image/player_right.png")
        self.left_fish: PhotoImage | None = None
        self.right_fish: PhotoImage | None = None
        self.update_fish_img()

    def update_fish_img(self) -> None:
        left_fish = self.original_left_fish.resize((self.width, self.height))
        right_fish = self.original_right_fish.resize((self.width, self.height))
        self.left_fish = ImageTk.PhotoImage(left_fish)
        self.right_fish = ImageTk.PhotoImage(right_fish)
        image = self.right_fish if self.anchor else self.left_fish,
        self.image_id = super().basic_canvas.create_image(self.x, self.y, image=image, anchor="nw")
        CollisionDetection.update_player_info()

    def move_up(self, _) -> None:
        if self.y - env.Setting.PLAY_SPEED < 0:
            self.y = 0
        else:
            self.y -= env.Setting.PLAY_SPEED
        self.move()

    def move_down(self, _) -> None:
        if self.y + self.height + env.Setting.PLAY_SPEED > self.basic_canvas.winfo_height():
            self.y = self.basic_canvas.winfo_height() - self.height
        else:
            self.y += env.Setting.PLAY_SPEED
        self.move()

    def move_left(self, _) -> None:
        if self.x < 0:
            return
        if self.anchor:
            self.reversal()
        else:
            self.x -= env.Setting.PLAY_SPEED
            self.move()

    def move_right(self, _) -> None:
        if self.x + self.width > self.basic_canvas.winfo_width():
            return
        if not self.anchor:
            self.reversal()
        else:
            self.x += env.Setting.PLAY_SPEED
            self.move()

    def reversal(self) -> None:
        image = self.left_fish if self.anchor else self.right_fish
        self.anchor = not self.anchor
        super().basic_canvas.delete(self.image_id)
        self.image_id = super().basic_canvas.create_image(self.x, self.y, image=image, anchor="nw")

    def flicker(self) -> None:
        self.basic_canvas.tag_lower(self.image_id)
        self.basic_canvas.after(100, self.basic_canvas.tag_raise, self.image_id)


class RandomFish(Fish):
    upper_size = 140
    small_upper, medium_upper, huge_upper = env.Setting.fish_size_slice
    resource_dir = ("SmallFish", "MediumFish", "HugeFish")
    game_control: env.GameControl | None = None

    def __init__(self):
        super().__init__()
        # self.fish是为了保证对鱼图像的引用，避免其被销毁
        self.fish: Image.Image | PhotoImage | None = None
        self.tagname = None
        self.speed = RandomFish.__random_speed()
        size_rank = RandomFish.__random_size_rank()
        self.height = self.__random_height(size_rank)
        self.width = self.__random_width(size_rank)
        self.x = self.__random_x()
        self.y = self.__random_y()
        self.anchor, self.__out_of_border = self.__initialize_anchor()
        self.image_id = self.generate_fish_image_id()
        self.collision_detector = CollisionDetection(self)
        self.poly_x, self.poly_y, life_val = self.collision_detector.load_collision_data(self.tagname)
        self.life_val = life_val * self.width * self.height

    def constant_move(self) -> None:
        def join():
            self.game_control.event.wait()
            self.constant_move()
        if not self.game_control.playing:
            return
        if self.game_control.stop:
            return threading.Thread(target=join, daemon=True).start()
        try:
            if self.__out_of_border():
                self.destroy()
            self.collision_detector.fish_collision()
            self.move()
            super().basic_canvas.after(22 - env.Setting.RANDOM_FISH_SPEED, self.constant_move)
        except (IndexError, TclError):
            return

    def __initialize_anchor(self) -> tuple[int, callable]:
        if self.x < 0:
            return 1, self.__move_right
        else:
            return 0, self.__move_left

    def __move_left(self) -> bool:
        self.x -= self.speed
        return self.x + self.width < 0

    def __move_right(self) -> bool:
        self.x += self.speed
        return self.x > self.basic_canvas.winfo_width()

    def destroy(self) -> None:
        self.fish = None
        RandomFish.game_control.fish_count -= 1
        RandomFish.basic_canvas.delete(self.image_id)

    @classmethod
    def __random_size_rank(cls) -> int:
        probabilities = env.Setting.weight[cls.game_control.current_level]
        size_rank = choices((0, 1, 2), weights=probabilities, k=1)[0]
        return size_rank

    @classmethod
    def __random_speed(cls) -> float:
        speed_upper = 1.5 + cls.game_control.score / 7000
        return uniform(0.3, speed_upper)

    def __random_x(self) -> int:
        return choice((-self.width, self.basic_canvas.winfo_width()))

    def __random_y(self) -> int:
        return randint(40, self.basic_canvas.winfo_height() - self.height)

    @classmethod
    def __random_height(cls, size_rank: int) -> int:
        player = CollisionDetection.player
        match size_rank:
            case 0:
                small_upper_size = int(player.height * cls.small_upper)
                return min(randint(10, small_upper_size), 40)
            case 1:
                medium_lower_size = int(player.height * cls.small_upper)
                medium_upper_size = int(player.height * RandomFish.medium_upper)
                return min(randint(medium_lower_size, medium_upper_size), 80)
            case 2:
                huge_lower_size = int(player.height * cls.medium_upper)
                huge_upper_size = int(player.height * cls.huge_upper)
                return min(randint(huge_lower_size, huge_upper_size), 120)
            
    def __random_width(self, size_rank: int) -> int:
        dir_name = RandomFish.resource_dir[size_rank]
        self.tagname = choice([file.name for file in scandir(path.join("Resources", dir_name))])
        file_path = path.join("Resources", dir_name, self.tagname)
        with Image.open(file_path) as fish:
            orig_w, orig_h = fish.size
            real_width = int(orig_w * self.height / orig_h)
            self.fish: Image.Image = fish.resize((real_width, self.height))
        return real_width
    
    def generate_fish_image_id(self) -> int:
        if self.anchor:
            self.fish = self.fish.transpose(Image.FLIP_LEFT_RIGHT)
        self.fish = ImageTk.PhotoImage(self.fish)
        image_id = super().basic_canvas.create_image(
            self.x, self.y,
            image=self.fish,
            anchor="nw"
        )
        return image_id



class CollisionDetection(object):
    with open(env.COLLISION_DATA_PATH, "r", encoding="utf-8") as f:
        COLLISION_DATA = json.load(f)
    player_info = COLLISION_DATA["Player"]
    player: Player | None = None
    main_control: 'MainControl' = None
    player_life_val = 0
    checkpoints = list()

    def __init__(self, fish: RandomFish):
        self.fish: RandomFish = fish

    @classmethod
    def update_player_info(cls) -> None:
        _, image_height = cls.player_info["Size"]
        poly_x, poly_y = cls.player_info["PolyX"], cls.player_info["PolyY"]
        scale = cls.player.height / image_height
        cls.checkpoints = [(x * scale, y * scale) for x, y in zip(poly_x, poly_y)]
        cls.player_life_val = cls.player.width * cls.player.height * cls.player_info["Life_val"]

    @classmethod
    def player_checkpoints(cls) -> list:
        if cls.player.anchor:
            tmp = cls.player.x + cls.player.width - 1
            return [(tmp - x, y + cls.player.y) for x, y in cls.checkpoints]
        else:
            return [(x + cls.player.x, y + cls.player.y) for x, y in cls.checkpoints]
        
    def load_collision_data(self, tagname: str) -> tuple[list, list, float]:
        poly_data = CollisionDetection.COLLISION_DATA[tagname]
        _, height = poly_data["Size"]
        life_val: float = poly_data["Life_val"]
        poly_x, poly_y = poly_data["PolyX"], poly_data["PolyY"]
        scale = self.fish.height / height
        poly_x = [x * scale for x in poly_x]
        poly_y = [y * scale for y in poly_y]
        if self.fish.anchor:
            poly_x = [self.fish.width - x for x in poly_x]
            poly_x.reverse()
            poly_y.reverse()
        return poly_x, poly_y, life_val

    def point_in_fish_polygon(self) -> bool:
        poly_x = [x + self.fish.x for x in self.fish.poly_x]
        poly_y = [y + self.fish.y for y in self.fish.poly_y]
        min_x, max_x = min(poly_x), max(poly_x)
        min_y, max_y = min(poly_y), max(poly_y)
        polySides = len(self.fish.poly_x)

        for point in self.player_checkpoints():
            x, y = point
            if x < min_x or x > max_x or y < min_y or y > max_y:
                continue
            oddNodes = False
            for i in range(polySides):
                j = (i + 1) % polySides
                if ((poly_y[i] < y and poly_y[j] >= y) or (poly_y[j] < y and poly_y[i] >= y)) and \
                (poly_x[i] + (y - poly_y[i]) * (poly_x[j] - poly_x[i]) / (poly_y[j] - poly_y[i]) < x):
                    oddNodes = not oddNodes
            if oddNodes:
                return True
        return False

    def no_rectangle_collision(self) -> bool:
        cls = CollisionDetection
        return cls.player.x + cls.player.width < self.fish.x or\
               self.fish.x + self.fish.width < cls.player.x or\
               cls.player.y + cls.player.height < self.fish.y or\
               self.fish.y + self.fish.height < cls.player.y
    
    def fish_collision(self) -> None:
        if self.no_rectangle_collision():
            return
        if self.point_in_fish_polygon():
            self.collision_update()
    
    def collision_update(self) -> None:
        cls = CollisionDetection
        game_control = RandomFish.game_control
        if cls.player_life_val > self.fish.life_val:
            self.fish.destroy()
            game_control.score += self.fish.width + self.fish.height
            game_control.update_level()
            cls.main_control.score_label.config(text=f'得分: {RandomFish.game_control.score}')
            cls.player.width = game_control.score // 40 + env.Setting.PLAYER_INITIAL_W
            cls.player.height = game_control.score // 80 + env.Setting.PLAYER_INITIAL_H
            cls.player.update_fish_img()
            cls.main_control.victory()
        elif not RandomFish.game_control.god:
            cls.main_control.death()


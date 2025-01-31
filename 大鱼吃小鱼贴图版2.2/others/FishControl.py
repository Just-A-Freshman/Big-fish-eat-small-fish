from tkinter import Canvas, PhotoImage, TclError
from Setting import GameControl, Setting
from random import choices, choice, uniform, randint
from os import path, scandir
from PIL import Image, ImageTk
from PixelReader import find_window, get_pixel_color
import threading
import json
import math


MENU_OFFSET = 40
PLAYER_INITIAL_H = 20
PLAYER_INITIAL_W = 40
COLLISION_DATA_PATH = path.join("resources", "json", "collison_basic.json")
SYN_EVENT = threading.Event()
SYN_EVENT.set()



class Fish(object):
    basic_canvas: Canvas | None = None

    def __init__(self):
        self.image_id = 0
        self.anchor = 0  # 0代表左, 1代表右
        self.width, self.height = PLAYER_INITIAL_W, PLAYER_INITIAL_H
        self.x, self.y = 0, 0
        self.life_val = 0

    def move(self):
        Fish.basic_canvas.move(
            self.image_id,
            self.x - Fish.basic_canvas.coords(self.image_id)[0],
            self.y - Fish.basic_canvas.coords(self.image_id)[1]
        )

    def tag_raise(self):
        Fish.basic_canvas.tag_raise(self.image_id)


class Player(Fish):
    def __init__(self):
        super().__init__()
        self.collison_detector = CollisonDetection(self)
        self.x, self.y = 455, 250
        self.original_left_fish: Image.Image = Image.open(r"resources/image/player_left.png")
        self.original_right_fish: Image.Image = Image.open(r"resources/image/player_right.png")
        self.left_fish: PhotoImage | None = None
        self.right_fish: PhotoImage | None = None
        self.update_fish_img()

    def update_fish_img(self):
        left_fish = self.original_left_fish.resize((self.width, self.height))
        right_fish = self.original_right_fish.resize((self.width, self.height))
        self.left_fish = ImageTk.PhotoImage(left_fish)
        self.right_fish = ImageTk.PhotoImage(right_fish)
        image = self.right_fish if self.anchor else self.left_fish,
        self.image_id = super().basic_canvas.create_image(self.x, self.y, image=image, anchor="nw")
        self.collison_detector.update_collison_data()

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
        self.image_id = super().basic_canvas.create_image(self.x, self.y, image=image, anchor="nw")


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
        # self.fish是为了保证对鱼图像的引用，避免其被销毁
        self.fish: Image.Image | PhotoImage | None = None
        self.speed = RandomFish.__random_speed()
        size_rank = RandomFish.__random_size_rank()
        self.height = self.__random_height(size_rank)
        self.width = self.__random_width(size_rank)
        self.x = self.__random_x()
        self.y = self.__random_y()
        self.anchor, self.__out_of_border = self.__initialize_anchor()
        self.image_id = self.generate_fish_image_id()
        self.collison_detector = RandomFish.basic_player.collison_detector

    def constant_move(self) -> None:
        def join():
            self.game_control.event.wait()
            self.constant_move()
        if not self.game_control.playing:
            return
        elif self.game_control.stop:
            return threading.Thread(target=join, daemon=True).start()
        elif self.__out_of_border():
            return self.__destroy()
        try:
            self.fish_collision()
            self.move()
            super().basic_canvas.after(22 - Setting.RANDOM_FISH_SPEED, self.constant_move)
        except (IndexError, TclError):
            return

    def __initialize_anchor(self):
        if self.x < 0:
            return 1, self.__move_right
        else:
            return 0, self.__move_left

    def __move_left(self) -> bool:
        self.x -= self.speed
        return self.x + self.width < 0

    def __move_right(self) -> bool:
        self.x += self.speed
        return self.x > 960

    def __destroy(self):
        self.fish = None
        RandomFish.game_control.fish_count -= 1
        RandomFish.basic_canvas.delete(self.image_id)

    @classmethod
    def __random_size_rank(cls) -> int:
        probabilities = Setting.weight[cls.game_control.current_level]
        size_rank = choices((0, 1, 2), weights=probabilities, k=1)[0]
        return size_rank

    @classmethod
    def __random_speed(cls) -> float:
        speed_upper = 1.5 + cls.game_control.score / 7000
        return uniform(0.3, speed_upper)

    def __random_x(self) -> int:
        return choice((-self.width, 960))

    def __random_y(self) -> int:
        return randint(40, 480 - self.height)

    @classmethod
    def __random_height(cls, size_rank: int) -> int:
        match size_rank:
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
            
    def __random_width(self, size_rank: int) -> tuple[int, Image.Image]:
        dir_name = RandomFish.resource_dir[size_rank]
        fish_img_file = choice([file.name for file in scandir(path.join("Resources", dir_name))])
        file_path = path.join("Resources", dir_name, fish_img_file)
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

    def fish_collision(self):
        no_contact = self.collison_detector.rough_rectangle_collison(self)
        if no_contact:
            return
        
        self.tag_raise()
        if self.collison_detector.distance_collison(self):
            self.__fish_collison()
        elif self.collison_detector.pixel_detection():
            touch = self.__fish_collison()
            if touch:
                res = [self.basic_canvas.find_closest(*i)[0] for i in self.collison_detector.screen_checkpoints()]
                if any(tag == self.image_id for tag in res):
                    self.__fish_collison()
            

        
    def __fish_collison(self):
        player_size = RandomFish.basic_player.width * RandomFish.basic_player.height
        if player_size > self.width * self.height:
            self.__destroy()
            RandomFish.game_control.score += self.width + self.height
            RandomFish.game_control.update_level()
            RandomFish.big_eat_small.score_label.config(text=f'得分: {RandomFish.game_control.score}')
            RandomFish.basic_player.width = RandomFish.game_control.score // 40 + PLAYER_INITIAL_W
            RandomFish.basic_player.height = RandomFish.game_control.score // 80 + PLAYER_INITIAL_H
            RandomFish.basic_player.update_fish_img()
            RandomFish.big_eat_small.victory()
        elif not RandomFish.game_control.god:
            print(self.collison_detector.tmp)
            RandomFish.game_control.god = True
            RandomFish.big_eat_small.after(3000, RandomFish.game_control.dispose_god_time)
            # RandomFish.big_eat_small.death()
            RandomFish.game_control.stop_game(0)


class CollisonDetection(object):
    
    def load_detection_data():
        with open(COLLISION_DATA_PATH, "r", encoding="utf-8") as f:
            res = json.load(f)
        angle_dist_rel: dict = res["angle_dist_rel"]
        angle_dist_rel = {float(key): value for key, value in angle_dist_rel.items()}
        check_point = res["check_point"]
        return angle_dist_rel, check_point
    
    PLAYER_IMAGE_HEIGHT = 240
    COLOR_THRESHOLD = 90
    ANGLE_DIST_REL, ST_CHECKPOINTS = load_detection_data()
    ANGLES = list(ANGLE_DIST_REL.keys())

    def __init__(self, player: Player):
        self.player: Player = player
        self.hwnd = find_window(window_name="大鱼吃小鱼")
        # 下面两个属性自动在玩家图像更新时更新
        self.image_checkpoints = None
        self.image_pixel_color = None
        self.tmp = None

    @staticmethod
    def __find_target_angle(target):
        angles = CollisonDetection.ANGLES
        left, right = 0, len(angles) - 1
        while left <= right:
            mid = (left + right) // 2
            mid_value = angles[mid]
            if mid_value < target:
                left = mid + 1
            elif mid_value > target:
                right = mid - 1
            else:
                return angles[mid], angles[mid + (mid + 1 < len(angles))]
        return angles[right], angles[left]
    
    @staticmethod
    def color_diff(color1, color2) -> float:
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)
    
    @staticmethod
    def get_around_point(x, y):
        points = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (i, j) != (0, 0):
                    points.append((x + i, y + j))
        return points
    
    def __transform_points(self):
        def transform(x):
            return int(round(x * scale, 0))
        scale = self.player.height / CollisonDetection.PLAYER_IMAGE_HEIGHT
        return [(transform(y), transform(x)) for x, y in CollisonDetection.ST_CHECKPOINTS]

    def update_collison_data(self) -> None:
        self.image_checkpoints = self.__transform_points()

    
    def screen_checkpoints(self) -> list:
        player_y = self.player.y + MENU_OFFSET
        if self.player.anchor:
            tmp = self.player.x + self.player.width - 1
            return [(tmp - x, y + player_y) for x, y in self.image_checkpoints]
        else:
            return [(x + self.player.x, y + player_y) for x, y in self.image_checkpoints]

    def rough_rectangle_collison(self, fish: RandomFish) -> bool:
        return self.player.x + self.player.width < fish.x or\
               fish.x + fish.width < self.player.x or\
               self.player.y + self.player.height < fish.y or\
               fish.y + fish.height < self.player.y

    def distance_collison(self, fish: RandomFish) -> bool:
        fx, fy = fish.x + fish.width / 2, fish.y + fish.height / 2
        px, py = self.player.x + self.player.width / 2, self.player.y + self.player.height / 2
        dx, dy = fx - px, fy - py
        distance = math.sqrt(dx ** 2 + dy ** 2)
        angle_degrees = math.degrees(math.atan2(dy, dx)) % 360
        if self.player.anchor == 0:
            angle_degrees = 540 - angle_degrees if angle_degrees > 180 else 180 - angle_degrees
        select_dist = CollisonDetection.ANGLE_DIST_REL
        left_angle, right_angle = self.__find_target_angle(angle_degrees)
        left_dist, right_dist = select_dist[left_angle], select_dist[right_angle]
        contact_distance = (angle_degrees - left_angle) / (right_angle - left_angle) * (right_dist - left_dist) + left_dist
        contact_distance *= (self.player.height / CollisonDetection.PLAYER_IMAGE_HEIGHT)
        return distance < contact_distance

    def pixel_detection(self) -> int:
        screen_checkpoints = self.screen_checkpoints()
        game_pixel_color = list(get_pixel_color(screen_checkpoints, self.hwnd))
        return any(i == (0, 0, 0) for i in game_pixel_color)
        


import pygame as p
import math
import random
from tile_for_game import*
from tools_for_game import*

side_right = p.transform.scale(p.image.load(os.path.join(images_path, "side.png")).convert_alpha(), (24, 48))
move_right1 = p.transform.scale(p.image.load(os.path.join(images_path, "finishstep.png")).convert_alpha(), (24, 48))
move_right2 = p.transform.scale(p.image.load(os.path.join(images_path, "bigstep.png")).convert_alpha(), (24, 48))
side_left = p.transform.scale(p.image.load(os.path.join(images_path, "side2.png")).convert_alpha(), (24, 48))
move_left1 = p.transform.scale(p.image.load(os.path.join(images_path, "finishstep2.png")).convert_alpha(), (24, 48))
move_left2 = p.transform.scale(p.image.load(os.path.join(images_path, "bigstep2.png")).convert_alpha(), (24, 48))

w, h = 800, 600
screen = p.display.set_mode((w, h))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 48
        self.vel_y = 0
        self.on_ground = False
        self.fly_mode = False
        self.direction = "right"
        self.walking = False
        self.animation_frames = {
            "right": [move_right1, move_right2],
            "left": [move_left1, move_left2]
        }
        self.animation_index = 0
        self.animation_counter = 0
        self.animation_speed = 10
        self.current_image = side_right

    def rect(self):
        return p.Rect(self.x, self.y, self.width, self.height)

    def update(self, world, keys):
        dx, dy = 0, 0
        if self.fly_mode:
            if keys[p.K_a]:
                dx = -5
            if keys[p.K_d]:
                dx = 5
            if keys[p.K_w]:
                dy = -5
            if keys[p.K_s]:
                dy = 5
            self.x += dx
            self.y += dy
        else:
            if keys[p.K_a]:
                dx = -5
                self.direction = "left"
            elif keys[p.K_d]:
                dx = 5
                self.direction = "right"
            self.x += dx

            # Horizontal collision (ignoring water)
            start_tx = math.floor(self.x / tile_size)
            end_tx = math.floor((self.x + self.width) / tile_size) + 1
            start_ty = math.floor(self.y / tile_size)
            end_ty = math.floor((self.y + self.height) / tile_size) + 1
            for tx in range(start_tx, end_tx):
                for ty in range(start_ty, end_ty):
                    tile = world.get_tile(tx, ty)
                    if tile is not None and tile.kind != "water":
                        tile_rect = p.Rect(tx * tile_size, ty * tile_size, tile_size, tile_size)
                        if self.rect().colliderect(tile_rect):
                            if dx > 0:
                                self.x = tile_rect.left - self.width
                            elif dx < 0:
                                self.x = tile_rect.right

            # Gravity
            self.vel_y += 0.5
            self.y += self.vel_y
            start_tx = math.floor(self.x / tile_size)
            end_tx = math.floor((self.x + self.width) / tile_size) + 1
            start_ty = math.floor(self.y / tile_size)
            end_ty = math.floor((self.y + self.height) / tile_size) + 1
            for tx in range(start_tx, end_tx):
                for ty in range(start_ty, end_ty):
                    tile = world.get_tile(tx, ty)
                    if tile is not None and tile.kind != "water":
                        tile_rect = p.Rect(tx * tile_size, ty * tile_size, tile_size, tile_size)
                        if self.rect().colliderect(tile_rect):
                            if self.vel_y > 0:
                                self.y = tile_rect.top - self.height
                                self.vel_y = 0
                                self.on_ground = True
                            elif self.vel_y < 0:
                                self.y = tile_rect.bottom
                                self.vel_y = 0

            # Check if in water
            in_water = False
            for tx in range(start_tx, end_tx):
                for ty in range(start_ty, end_ty):
                    tile = world.get_tile(tx, ty)
                    if tile is not None and tile.kind == "water":
                        in_water = True
                        break
                if in_water:
                    break
            if in_water:
                self.on_ground = False
                if keys[p.K_SPACE]:
                    self.vel_y = -1.5
                else:
                    self.vel_y = min(self.vel_y + 0.2, 1.5)
            if self.on_ground and keys[p.K_SPACE]:
                self.vel_y = -10
                self.on_ground = False

            # Update animation
            if dx != 0:
                self.walking = True
                self.animation_counter += 1
                if self.animation_counter >= self.animation_speed:
                    self.animation_counter = 0
                    self.animation_index = (self.animation_index + 1) % len(self.animation_frames[self.direction])
                    self.current_image = self.animation_frames[self.direction][self.animation_index]
            else:
                self.walking = False
                self.current_image = side_right if self.direction == "right" else side_left

    def draw(self, camera_x, camera_y):
        screen.blit(self.current_image, (self.x - camera_x, self.y - camera_y))

class Mountain:
    def __init__(self, image, image_id, x, y=GROUND_LEVEL, parallax=0.3):
        self.image = image
        self.image_id = image_id
        self.x = x
        self.y = y
        self.parallax = parallax

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x * self.parallax
        ground_screen_y = GROUND_LEVEL * tile_size - camera_y
        draw_y = ground_screen_y - self.image.get_height()
        screen.blit(self.image, (draw_x, draw_y))

class Cloud:
    def __init__(self, images):
        self.original_image = random.choice(images)
        self.scale = random.uniform(1.5, 2.5)
        self.image = p.transform.rotozoom(self.original_image, 0, self.scale)
        self.x = random.randint(0, w)
        self.y = random.randint(-300, 50)
        self.speed = random.uniform(0.2, 1.0)

    def update(self):
        self.x += self.speed
        if self.x > w:
            self.x = -self.image.get_width()
            self.y = random.randint(-300, 50)

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.x - camera_x, self.y - camera_y))
import pygame as p
import random

w, h = 800, 600

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
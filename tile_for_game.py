import pygame as p
from tools_for_game import load_texture

textures = {
    "grass": load_texture("grass.png"),      # expected texture: grass.png
    "dirt": load_texture("dirt.png"),          # expected texture: dirt.png
    "cave_stone": load_texture("cave_stone.png"),  # expected texture: cave_stone.png
    "water": load_texture("water.png"),        # expected texture: water.png
    "wood": load_texture("wood.png"),
    "leaves": load_texture("leaves.png"),
    "stone": load_texture("stone.png")
}

tile_size = 32

class Tile:
    def __init__(self, kind, level=None):
        self.kind = kind
        # For water, attach a level (1 to 8, where 8 means a full source)
        if self.kind == "water":
            self.level = 8 if level is None else level
        self.image = textures.get(kind, None)
        # Interactive tiles for collision (except water)
        self.can_interact = kind in ["grass", "dirt", "stone", "wood", "leaves", "cave_stone"]
        
    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, Tile):
            # For water, ignore level differences when comparing types.
            if self.kind == "water" and other.kind == "water":
                return True
            return self.kind == other.kind
        if isinstance(other, str):
            return self.kind == other
        return False
    
    def draw(self, screen, x, y, camera_x, camera_y):
        if self.image:
            screen.blit(self.image, (x - camera_x, y - camera_y))
        else:
            # Fallback colors if texture is missing.
            color_mapping = {
                "grass": (34, 139, 34),
                "dirt": (139, 69, 19),
                "cave_stone": (70, 70, 70),
                "stone": (128, 128, 128),
                "wood": (160, 82, 45),
                "leaves": (34, 139, 34),
                "water": (50, 100, 255)
            }
            color = color_mapping.get(self.kind, (200, 0, 200))
            p.draw.rect(screen, color, p.Rect(x - camera_x, y - camera_y, tile_size, tile_size))
import pygame as p
import math
from tile_for_game import Tile

tile_size = 32
GROUND_LEVEL = 10
w, h = 800, 600
screen = p.display.set_mode((w, h))

class World:
    """
    The interactive foreground world:
      - y < GROUND_LEVEL: sky (None).
      - y == GROUND_LEVEL: grass tile.
      - GROUND_LEVEL < y <= GROUND_LEVEL+6: a random blend of dirt and stone.
      - y > GROUND_LEVEL+6: stone.
    """
    def __init__(self, layer="foreground"):
        self.modifications = {}
        self.layer = layer
        
    def default_tile(self, x, y):
        if self.layer == "foreground":
            if y < GROUND_LEVEL:
                return None
            elif y == GROUND_LEVEL:
                return Tile("grass")
            elif GROUND_LEVEL < y <= GROUND_LEVEL + 6:
                noise = (math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0
                threshold = (y - (GROUND_LEVEL + 1)) / 5.0  # 0 at GROUND_LEVEL+1, 1 at GROUND_LEVEL+6
                if noise < threshold:
                    return Tile("stone")
                else:
                    return Tile("dirt")
            else:
                return Tile("stone")
        
    def get_tile(self, x, y):
        if (x, y) in self.modifications:
            return self.modifications[(x, y)]
        return self.default_tile(x, y)
    
    def set_tile(self, x, y, kind):
        default_tile_obj = self.default_tile(x, y)
        if kind is None:
            new_tile = None
        elif isinstance(kind, Tile):
            new_tile = kind
        else:
            new_tile = Tile(kind)
            
        if new_tile == default_tile_obj:
            if (x, y) in self.modifications:
                del self.modifications[(x, y)]
        else:
            self.modifications[(x, y)] = new_tile
            
    def add_tile(self, x, y, kind):
        self.set_tile(x, y, kind)
        
    def remove_tile(self, x, y):
        cur = self.get_tile(x, y)
        if cur is not None and cur.can_interact:
            self.set_tile(x, y, None)
            
    def draw(self, camera_x, camera_y):
        start_x = math.floor(camera_x / tile_size)
        end_x = math.floor((camera_x + w) / tile_size) + 1
        start_y = math.floor(camera_y / tile_size)
        end_y = math.floor((camera_y + h) / tile_size) + 1
        for tx in range(start_x, end_x):
            for ty in range(start_y, end_y):
                tile = self.get_tile(tx, ty)
                if tile is not None:
                    tile.draw(screen, tx * tile_size, ty * tile_size, camera_x, camera_y)
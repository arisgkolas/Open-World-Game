import pygame as p
import os
import random    

base_path = os.path.dirname(__file__)
images_path = os.path.join(base_path, 'images')
tile_size = 32
GROUND_LEVEL = 10

def load_texture(filename):
    path = os.path.join(images_path, filename)
    try:
        img = p.image.load(path).convert_alpha()
        # Scale to tile size
        return p.transform.scale(img, (tile_size, tile_size))
    except Exception as e:
        print(f"Failed to load image: {path}", e)
        return None

#--------------------------------------------------------------------------------------------------------------------
def load_bg_image(filename):
    path = os.path.join(images_path, filename)
    try:
        return p.image.load(path).convert_alpha()
    except Exception as e:
        print(f"Failed to load background image: {path}", e)
        return None
    
#--------------------------------------------------------------------------------------------------------------------
def update_water_flow(world):
    from tile_for_game import Tile
    """
    Simplified water physics:
    For every water tile, if the tile immediately below is empty (or contains water with a lower level),
    water flows downward by one tile.
    Source water blocks (level 8) remain after flowing.
    Horizontal flow is omitted so water simply drips downward.
    """
    water_positions = []
    for pos, tile in list(world.modifications.items()):
        if tile is not None and tile.kind == "water":
            water_positions.append((pos, tile.level))
    # Process water from bottom to top so gravity is respected.
    water_positions.sort(key=lambda pos_level: pos_level[0][1], reverse=True)
    for (x, y), level in water_positions:
        current_tile = world.get_tile(x, y)
        if current_tile is None or current_tile.kind != "water":
            continue
        L = current_tile.level
        below = world.get_tile(x, y + 1)
        if below is None or (below.kind == "water" and getattr(below, "level", 0) < L):
            world.set_tile(x, y + 1, Tile("water", level=L))
            if L < 8:  # Only non-source water is removed after flowing.
                world.set_tile(x, y, None)

#--------------------------------------------------------------------------------------------------------------------
def fill_surface_caves_with_water(world, x_min, x_max, y_top, y_bottom):
    """
    Scans row y_top for a contiguous empty gap.
    If the gap is 5 or more blocks wide, fills region y_top to y_bottom with source water.
    """
    x = x_min
    while x < x_max:
        if world.get_tile(x, y_top) is None:
            start = x
            while x < x_max and world.get_tile(x, y_top) is None:
                x += 1
            region_width = x - start
            if region_width >= 5:
                for i in range(start, x):
                    for y in range(y_top, y_bottom + 1):
                        world.set_tile(i, y, "water")
        else:
            x += 1

#--------------------------------------------------------------------------------------------------------------------
def generate_cave_blob(world, cx, cy, rx, ry, entrance_width, cave_type):
    """
    Carves out a blob-shaped cave.
    For the top entrance rows (entrance_height = 2):
      - For stone caves, removes tiles in a wider opening.
      - For dirt caves, removes only the central column to form a narrow, coal-mine style entrance.
    Below that, carving follows an elliptical equation.
    """
    entrance_height = 2
    top_y = cy - ry
    for y in range(top_y, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if y < top_y + entrance_height:
                if cave_type == "dirt":
                    if x == cx:
                        world.set_tile(x, y, None)
                else:
                    if abs(x - cx) <= entrance_width // 2:
                        world.set_tile(x, y, None)
            else:
                if ((x - cx) ** 2) / (rx ** 2) + ((y - cy) ** 2) / (ry ** 2) < 1:
                    world.set_tile(x, y, None)

#--------------------------------------------------------------------------------------------------------------------
def generate_caves_in_layer(world, start_x, end_x, start_y, end_y, cave_type):
    """
    Generates cave blobs in a given region.
    - For "dirt" caves (higher, shallower), use smaller parameters.
    - For "stone" caves (lower, deeper), use larger parameters.
    """
    width = end_x - start_x
    if cave_type == "dirt":
        num_blobs = max(8, width // 20)
        entrance_width = 1
    else:
        num_blobs = max(5, width // 30)
        entrance_width = 1
    for _ in range(num_blobs):
        cx = random.randint(start_x, end_x)
        cy = random.randint(start_y, end_y)
        if cave_type == "dirt":
            rx = random.randint(3, 6)
            ry = random.randint(2, 4)
        else:  # stone caves – generate bigger blobs
            rx = random.randint(8, 16)
            ry = random.randint(6, 12)
        generate_cave_blob(world, cx, cy, rx, ry, entrance_width, cave_type)
        # For stone caves, sometimes generate an interconnected upper blob.
        if cave_type == "stone" and random.random() < 0.2:
            upper_cy = cy - ry - random.randint(2, 4)
            upper_rx = random.randint(6, 10)
            upper_ry = random.randint(4, 8)
            generate_cave_blob(world, cx, upper_cy, upper_rx, upper_ry, 1, "stone")
            for y in range(upper_cy + upper_ry, cy - ry + 1):
                world.set_tile(cx, y, None)

#--------------------------------------------------------------------------------------------------------------------
def generate_trees(world, start_x, end_x):
    for x in range(start_x, end_x):
        surface = world.get_tile(x, GROUND_LEVEL)
        if surface and surface.kind == "grass":
            if random.random() < 0.1:  # 10% chance per column
                tree_height = random.randint(6, 9)
                for i in range(1, tree_height + 1):
                    world.set_tile(x, GROUND_LEVEL - i, "wood")
                canopy_y = GROUND_LEVEL - tree_height
                for cx in range(x - 1, x + 2):
                    for cy in range(canopy_y - 1, canopy_y + 2):
                        world.set_tile(cx, cy, "leaves")
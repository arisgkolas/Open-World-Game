import pygame as p
import sys
import math
import os
import random
#-------------------------------------------------------------------------------------------------------------------------------------------------
# Setup paths and initialization
base_path = os.path.dirname(__file__)
images_path = os.path.join(base_path, 'images')
p.init()
w, h = 800, 600
screen = p.display.set_mode((w, h))
p.display.set_caption("Open World Game")
tile_size = 32
sky = (135, 206, 235)
GROUND_LEVEL = 10
MOUNTAIN_SCALE = 1.5
soul_count = 10

#-------------------------------------------------------------------------------------------------------------------------------------------------
# Helper functions to load images
def load_texture(filename):
    path = os.path.join(images_path, filename)
    try:
        img = p.image.load(path).convert_alpha()
        # Scale to tile size
        return p.transform.scale(img, (tile_size, tile_size))
    except Exception as e:
        print(f"Failed to load image: {path}", e)
        return None
#-------------------------------------------------------------------------------------------------------------------------------------------------
def load_bg_image(filename):
    path = os.path.join(images_path, filename)
    try:
        return p.image.load(path).convert_alpha()
    except Exception as e:
        print(f"Failed to load background image: {path}", e)
        return None

# Define textures. If a texture file is missing, a fallback color is used.-------------------------------------------------------------------------------------------------------------------------------------------------
textures = {
    "grass": load_texture("grass.png"),      
    "dirt": load_texture("dirt.png"),        
    "cave_stone": load_texture("cave_stone.png"), 
    "water": load_texture("water.png"),      
    "wood": load_texture("wood.png"),
    "leaves": load_texture("leaves.png"),
    "stone": load_texture("stone.png")
}

# Load player animation images-------------------------------------------------------------------------------------------------------------------------------------------------
side_right = p.transform.scale(p.image.load(os.path.join(images_path, "side.png")).convert_alpha(), (24, 48))
move_right1 = p.transform.scale(p.image.load(os.path.join(images_path, "finishstep.png")).convert_alpha(), (24, 48))
move_right2 = p.transform.scale(p.image.load(os.path.join(images_path, "bigstep.png")).convert_alpha(), (24, 48))
side_left = p.transform.scale(p.image.load(os.path.join(images_path, "side2.png")).convert_alpha(), (24, 48))
move_left1 = p.transform.scale(p.image.load(os.path.join(images_path, "finishstep2.png")).convert_alpha(), (24, 48))
move_left2 = p.transform.scale(p.image.load(os.path.join(images_path, "bigstep2.png")).convert_alpha(), (24, 48))

# --- Tile and World Classes ----------------------------------------------------------------------------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------------------------------------------------------------------------
class World:

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

# Create the foreground world.
fg_world = World(layer="foreground")

# --- Advanced Water Flow Simulation ----------------------------------------------------------------------------------------------------------------------------------------------------
def update_water_flow(world):
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

# --- Utility Function: Fill Surface Cave Openings with Water ----------------------------------------------------------------------------------------------------------------------------------------------------
def fill_surface_caves_with_water(world, x_min, x_max, y_top, y_bottom):
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

# --- Cave Generation Functions --------------------------------------------------------------------------------------------------------------------------------------------------
def generate_cave_blob(world, cx, cy, rx, ry, entrance_width, cave_type):
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

#-------------------------------------------------------------------------------------------------------------------------------------------------
def generate_caves_in_layer(world, start_x, end_x, start_y, end_y, cave_type):
    width = end_x - start_x
    if cave_type == "dirt":
        num_blobs = max(8, width // 20)
        entrance_width = 2
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

# --- Generate Caves ----------------------------------------------------------------------------------------------------------------------------------------------------
# Dirt layer caves (higher) with narrow, coal-mine style entrances.
generate_caves_in_layer(fg_world, -300, 300, GROUND_LEVEL + 5, GROUND_LEVEL + 10, "dirt")
# Stone layer caves (lower) with larger dimensions.
generate_caves_in_layer(fg_world, -300, 300, GROUND_LEVEL + 15, GROUND_LEVEL + 24, "stone")
# Fill wide openings in the dirt layer with water.
fill_surface_caves_with_water(fg_world, -300, 300, GROUND_LEVEL + 1, GROUND_LEVEL + 4)

# --- Other World Generation: Trees ----------------------------------------------------------------------------------------------------------------------------------------------------
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
generate_trees(fg_world, -50, 150)

# --- Player, Mountain, and Cloud Classes ----------------------------------------------------------------------------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------------------------------------------------------------------------
class Soul:
    def __init__(self, img, x, y):
        self.x = x
        self.y = y
        self.image = img

    def draw(self, screen, x, y):
        '''if self.image:
            screen.blit(self.image, (x, y))
        else:'''
        p.draw.rect(screen, (67, 173, 162), p.Rect(x, y, tile_size, tile_size))
#-------------------------------------------------------------------------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------------------------------------------------------------------------
def pop_inventory():
    pass

# --- Initialize Mountains and Clouds ----------------------------------------------------------------------------------------------------------------------------------------------------
mountain_images_raw = [
    load_bg_image("mountain1.png"),
    load_bg_image("mountain2.png"),
    load_bg_image("mountain3.png")
]
mountain_images = [img for img in mountain_images_raw if img is not None]
cloud_images = [
    load_bg_image("cloud1.png"),
    load_bg_image("cloud2.png"),
    load_bg_image("cloud3.png")
]
cloud_images = [img for img in cloud_images if img is not None]

mountains = []
container_width = w * 2
x_offset = 0
prev_idx = None
grass_y = GROUND_LEVEL * tile_size
while x_offset < container_width:
    possible_indices = list(range(len(mountain_images)))
    if prev_idx is not None:
        possible_indices = [i for i in possible_indices if i != prev_idx]
    if not possible_indices:
        possible_indices = list(range(len(mountain_images)))
    idx = random.choice(possible_indices)
    image = mountain_images[idx]
    if image:
        scaled_img = p.transform.scale(image, (int(image.get_width() * MOUNTAIN_SCALE), int(image.get_height() * MOUNTAIN_SCALE)))
        y_pos = grass_y - scaled_img.get_height()
        mountain = Mountain(scaled_img, idx, x_offset, y_pos, parallax=0.3)
        mountains.append(mountain)
        prev_idx = idx
        x_offset += scaled_img.get_width()

clouds = [Cloud(cloud_images) for _ in range(12)]

soul_y = 0
soul_spacing = tile_size

soul_positions = [(0, soul_y + i * soul_spacing) for i in range(soul_count)]

# --- Main Game Loop ----------------------------------------------------------------------------------------------------------------------------------------------------
spawn_y = (GROUND_LEVEL - 2) * tile_size
player = Player(0, spawn_y)
clock = p.time.Clock()
camera_x = 0
camera_y = 0
camera_margin = 200

soul_image = load_texture("soul.png") or p.Surface((tile_size, tile_size))
soul_image.fill((67, 173, 162))  # fallback
souls = [Soul(lambda: soul_image, 0, 0) for _ in range(soul_count)]

inventory_open = False
while True:
# Keys-------------------------------------------------------------------------------------------------------------------------------------------------
    for event in p.event.get():
        if event.type == p.QUIT:
            p.quit()
            sys.exit()
        if event.type == p.KEYDOWN:
            if event.key == p.K_f:
                player.fly_mode = not player.fly_mode
                print("Fly mode:", player.fly_mode)
            elif event.key == p.K_e:
                inventory_open = not inventory_open
                print("Inventory open")
                pop_inventory()
        if event.type == p.MOUSEBUTTONDOWN:
            mx, my = p.mouse.get_pos()
            tx = (mx + camera_x) // tile_size
            ty = (my + camera_y) // tile_size
            if event.button == 1:
                fg_world.remove_tile(tx, ty)
            elif event.button == 3:
                fg_world.add_tile(tx, ty, "dirt")
    
    keys = p.key.get_pressed()
    player.update(fg_world, keys)

# Camera and paralax-------------------------------------------------------------------------------------------------------------------------------------------------
    if player.x - camera_x < camera_margin:
        camera_x = player.x - camera_margin
    elif player.x - camera_x > w - camera_margin - player.width:
        camera_x = player.x - (w - camera_margin - player.width)
    if player.y - camera_y < camera_margin:
        camera_y = player.y - camera_margin
    elif player.y - camera_y > h - camera_margin - player.height:
        camera_y = player.y - (h - camera_margin - player.height)
    
    update_water_flow(fg_world)
    
    screen.fill(sky)
    
    effective_cam = camera_x * 0.3
    while mountains and (mountains[-1].x + mountains[-1].image.get_width() < effective_cam + w):
        prev_idx = mountains[-1].image_id
        possible_indices = [i for i in range(len(mountain_images)) if i != prev_idx]
        if not possible_indices:
            possible_indices = list(range(len(mountain_images)))
        new_idx = random.choice(possible_indices)
        new_img = mountain_images[new_idx]
        new_scaled_img = p.transform.scale(new_img, (int(new_img.get_width() * MOUNTAIN_SCALE), int(new_img.get_height() * MOUNTAIN_SCALE)))
        new_x = mountains[-1].x + mountains[-1].image.get_width()
        new_mountain = Mountain(new_scaled_img, new_idx, new_x, grass_y - new_scaled_img.get_height(), parallax=0.3)
        mountains.append(new_mountain)
#-------------------------------------------------------------------------------------------------------------------------------------------------
    while mountains and (mountains[0].x > effective_cam):
        prev_idx = mountains[0].image_id
        possible_indices = [i for i in range(len(mountain_images)) if i != prev_idx]
        if not possible_indices:
            possible_indices = list(range(len(mountain_images)))
        new_idx = random.choice(possible_indices)
        new_img = mountain_images[new_idx]
        new_scaled_img = p.transform.scale(new_img, (int(new_img.get_width() * MOUNTAIN_SCALE), int(new_img.get_height() * MOUNTAIN_SCALE)))
        new_x = mountains[0].x - new_scaled_img.get_width()
        new_mountain = Mountain(new_scaled_img, new_idx, new_x, grass_y - new_scaled_img.get_height(), parallax=0.3)
        mountains.insert(0, new_mountain)
#-------------------------------------------------------------------------------------------------------------------------------------------------
    while mountains and (mountains[0].x + mountains[0].image.get_width() < effective_cam - w):
        mountains.pop(0)
    while mountains and (mountains[-1].x > effective_cam + 2 * w):
        mountains.pop()
    for mountain in mountains:
        mountain.draw(screen, camera_x, camera_y)
        
    for cloud in clouds:
        cloud.update()
        cloud.draw(screen, camera_x, camera_y)

    for i, (soul_x, soul_y) in enumerate(soul_positions):
        souls[i].draw(screen, soul_y, soul_x)

    fg_world.draw(camera_x, camera_y)
    start_x = math.floor(camera_x / tile_size)
    end_x = math.floor((camera_x + w) / tile_size) + 1
    start_y = max(math.floor(camera_y / tile_size), GROUND_LEVEL)
    end_y = math.floor((camera_y + h) / tile_size) + 1
    cave_stone_tile = Tile("cave_stone")
    for tx in range(start_x, end_x):
        for ty in range(start_y, end_y):
            if (tx, ty) in fg_world.modifications and fg_world.modifications[(tx, ty)] is None:
                cave_stone_tile.draw(screen, tx * tile_size, ty * tile_size, camera_x, camera_y)
#-------------------------------------------------------------------------------------------------------------------------------------------------
    player.draw(camera_x, camera_y)
    
    p.display.flip()
    clock.tick(60)

"""
experience TODO:
1) Item Pickups - Monsters -> daynight cycle

gameplay TODO:
1 - After the game is playable) Boss towards fungi dimention: "Disturbed" takes you to the dimention when awakened. When he is defeated, he drops materials to make a portal
"""

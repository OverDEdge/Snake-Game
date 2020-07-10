import pygame as pg
import random
from os import path
from . import settings

# Create vector
vec = pg.math.Vector2

def check_for_collision(sprite, group, remove):
    '''
    Checks for collision between a sprite and a group
    '''
    hits = pg.sprite.spritecollide(sprite, group, remove)
    if hits:
        return True

def remove_background_from_img(image, colorkey):
    '''
    Removes background from image
    '''

    image.set_colorkey(colorkey)
    image.convert_alpha()

    return image

# Animate movement for a sprite
def animate_moving(sprite, image_array):
    now = pg.time.get_ticks()
    if (now - sprite.last_change_img_time) > sprite.img_upd_time:
        sprite.image_id += 1

        if sprite.image_id >= len(image_array):
            sprite.image_id = 0

        image = image_array[sprite.image_id]

        sprite.last_change_img_time = now
        sprite.non_rot_image = image

def load_moving_images(sprite, spritesheet, image_coordinates, colorkey):
    for location in image_coordinates:
        image = spritesheet.get_image(*location, settings.SIZE)
        image = remove_background_from_img(image, colorkey)
        sprite.images.append(image)


class Snake(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        '''
        Initializing Snake head
        '''
        self._layer = settings.SNAKE_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.pos = vec(x, y) * settings.TILESIZE
        self.prev_pos = vec(self.pos.x, self.pos.y)
        self.vel = vec(1, 0)
        self.body_parts = [BodyPart(self.game, self, x - 1, y)]
        self.images = []
        self.colorkey = settings.WHITE
        load_moving_images(self, self.game.snake_spritesheet, settings.SNAKE_IMG_HEAD, self.colorkey)
        self.image_id = 0
        self.non_rot_image = self.images[self.image_id]
        self.image = self.non_rot_image
        self.non_rot_tail = self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_TAIL, settings.SIZE)
        self.tail = self.non_rot_tail
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        self.pos_update_time = 0
        self.collide = False
        self.key = 'none'
        self.dir = 'right'
        self.prev_dir = self.dir
        self.last_change_img_time = 0
        self.img_upd_time = settings.SWITCH_SPRITE_IMAGE

        # Key mappings
        self.inputState = {
                'up': False,
                'down': False,
                'right': False,
                'left': False,
                'none': False
        }

    def update(self):

        # Get user input
        self.move_pressed_key()
        self.move_is_key_pressed()
        self.move_in_direction()
        animate_moving(self, self.images)

        # Get current time
        now = pg.time.get_ticks()

        # Only update position at certain intervals
        # SNAKE_UPDATE_RATE determines snake speed
        if now - self.pos_update_time > settings.SNAKE_UPDATE_RATE:

            if check_for_collision(self, self.game.snake_body, False) or check_for_collision(self, self.game.walls, False):
                self.collide = True
            else:
                self.update_positions()

        self.update_eat_food()

    def update_eat_food(self):
        '''
        Check if snake has found food and if yes adds another body part
        '''
        # Check if snake eats food
        if check_for_collision(self, self.game.food, True):
            self.game.score += 10
            last_body_part = self.body_parts[-1]
            self.body_parts.append(BodyPart(self.game, self, last_body_part.pos.x, last_body_part.pos.y))
            Food(self.game)

    def update_positions(self):
        self.update_body_parts_positions()

        # Update snake head position
        self.pos += self.vel * settings.TILESIZE
        self.pos_update_time = pg.time.get_ticks()

        self.update_body_parts_img()
        self.update_head_img()
        self.update_tail_img()

        #self.update_screen_wrap()

        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos

    def update_body_parts_positions(self):
        '''
        Loops through the body parts and updates the positions
        Necessary to do in Snake object to get synced updates
        '''
        for i in range(len(self.body_parts) - 1, 0, -1):
            self.body_parts[i].pos = self.body_parts[i - 1].pos

        self.body_parts[0].pos = vec(self.pos.x, self.pos.y)

    def update_head_img(self):

        if self.dir == 'up':
            self.image = pg.transform.flip(self.non_rot_image, False, True)
        if self.dir == 'right':
            self.image = pg.transform.rotate(self.non_rot_image, 90)
        if self.dir == 'left':
            self.image = pg.transform.rotate(self.non_rot_image, -90)
        if self.dir == 'down':
            self.image = self.non_rot_image

    def update_body_parts_img(self):
        '''
        Sets the appropriate body image depending on position
        '''

        # Behind head
        if len(self.body_parts) > 1:
            self.body_parts[0].image = self.update_correct_body_part(self.body_parts[1].pos, self.body_parts[0].pos, self.pos)
            self.body_parts[0].image = remove_background_from_img(self.body_parts[0].image, self.colorkey)

        # Rest of body
        for i in range(1, len(self.body_parts) - 1):
            self.body_parts[i].image = self.update_correct_body_part(self.body_parts[i + 1].pos, self.body_parts[i].pos, self.body_parts[i - 1].pos)
            self.body_parts[i].image = remove_background_from_img(self.body_parts[i].image, self.colorkey)

    def update_tail_img(self):
        '''
        Set appropriate image for tail
        '''

        tail_pos = self.body_parts[-1].pos

        if len(self.body_parts) > 1:
            front_of_tail = self.body_parts[-2].pos
        else:
            front_of_tail = self.pos

        if front_of_tail.y < tail_pos.y:
            self.body_parts[-1].image = self.non_rot_tail
        if front_of_tail.x > tail_pos.x:
            self.body_parts[-1].image = pg.transform.rotate(self.non_rot_tail, 90)
        if front_of_tail.y > tail_pos.y:
            self.body_parts[-1].image = pg.transform.flip(self.non_rot_tail, False, True)
        if front_of_tail.x < tail_pos.x:
            self.body_parts[-1].image = pg.transform.rotate(self.non_rot_tail, -90)

        self.body_parts[-1].image = remove_background_from_img(self.body_parts[-1].image, self.colorkey)

    def update_correct_body_part(self, pos_pre, pos, pos_post):
        if pos_pre.x == pos_post.x:
            return self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_BODY, settings.SIZE)
        if pos_pre.y == pos_post.y:
            return pg.transform.rotate(self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_BODY, settings.SIZE), 90)
        if (pos.x < pos_post.x and pos_pre.y < pos.y or
            pos_pre.x > pos.x and pos.y > pos_post.y):
            return self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_TURN[0], settings.SIZE)
        if (pos.x < pos_post.x and pos_pre.y > pos.y or
            pos_pre.x > pos.x and pos.y < pos_post.y):
            return self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_TURN[1], settings.SIZE)
        if (pos.x > pos_post.x and pos.y < pos_pre.y or
            pos_pre.x < pos.x and pos.y < pos_post.y):
            return self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_TURN[2], settings.SIZE)
        if (pos.x > pos_post.x and pos.y > pos_pre.y or
            pos_pre.x < pos.x and pos.y > pos_post.y):
            return self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_TURN[3], settings.SIZE)

    def update_screen_wrap(self):
        '''
        Wraps snake position from edge of screen to other side
        '''
        if self.pos.x > settings.WIDTH - settings.TILESIZE:
            self.pos.x = 0
        elif self.pos.x < 0:
            self.pos.x = settings.WIDTH - settings.TILESIZE
        if self.pos.y > settings.HEIGHT - settings.TILESIZE:
            self.pos.y = 0
        elif self.pos.y < 0:
            self.pos.y = settings.HEIGHT - settings.TILESIZE

    def move_pressed_key(self):
        '''
        Gets the key inputs and sets the correct binding
        '''
        keys = pg.key.get_pressed()
        for binding, keysBound in settings.MOVE_BINDINGS.items():
            for key in keysBound:
                if keys[key]:
                    self.inputState[binding] = True
                    break
                else:
                    self.inputState[binding] = False

    def move_is_key_pressed(self):
        '''
        Removes bindings when key is no longer pressed
        '''
        if not self.inputState[self.key]:
            self.key = 'none'

    def move_in_direction(self):
        '''
        Loops over all directions and sets velocity based on user input
        '''
        directions = ('left', 'right', 'up', 'down')
        vel = (vec(-1, 0), vec(1, 0), vec(0, -1), vec(0, 1))
        vel_check = (-self.vel.x, self.vel.x, -self.vel.y, self.vel.y)

        for i, dir in enumerate(directions):
            if self.inputState[dir] and vel_check[i] >= 0:
                if self.key == 'none':
                    self.vel = vel[i]
                    self.dir = dir
                    self.key = dir

        # To get smooth game feel give user reaction immediatly when turning
        if self.prev_dir != self.dir:
            self.pos_update_time = 0
            self.prev_dir = self.dir

class BodyPart(pg.sprite.Sprite):
    def __init__(self, game, snake, x, y):
        self._layer = settings.BODY_LAYER
        self.groups = game.all_sprites, game.snake_body
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.transform.rotate(self.game.snake_spritesheet.get_image(*settings.SNAKE_IMG_TAIL, settings.SIZE), 90)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * settings.TILESIZE
        self.rect.topleft = self.pos

    def update(self):
        # Update rectangle
        self.rect.topleft = self.pos

class Food(pg.sprite.Sprite):
    def __init__(self, game):
        self._layer = settings.FOOD_LAYER
        self.game = game
        self.groups = game.all_sprites, game.food
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.transform.scale(pg.image.load(path.join(settings.IMG_FOLDER, settings.FOOD_IMG)).convert(), settings.SIZE)
        self.image = remove_background_from_img(self.image, settings.BLACK)
        self.rect = self.image.get_rect()
        self.place_food()
        self.pos_update_time = 0

    def place_food(self):
        '''
        Places food at a random location, checking that a sprite doesn't already
        exist there.
        '''
        self.pos = vec(random.randrange(settings.GRIDWIDTH - 1), random.randrange(settings.GRIDHEIGHT - 1)) * settings.TILESIZE
        self.rect.topleft = self.pos
        if check_for_collision(self, self.game.walls, False) or check_for_collision(self, self.game.snake_body, False):
            self.place_food()

    def update(self):
        now = pg.time.get_ticks()

        if (now - self.pos_update_time) > settings.FOOD_POS_UPDATE_RATE:
            self.get_new_position()
            self.pos_update_time = now

    def get_new_position(self):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dir = random.choice(directions)
        self.pos.x += dir[0] * settings.TILESIZE
        self.pos.y += dir[1] * settings.TILESIZE
        self.rect.topleft = self.pos
        if check_for_collision(self, self.game.walls, False) or check_for_collision(self, self.game.snake_body, False):
            self.pos.x -= dir[0] * settings.TILESIZE
            self.pos.y -= dir[1] * settings.TILESIZE
            self.get_new_position()

class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        # Add to sprites group
        self._layer = settings.WALL_LAYER
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.transform.scale(pg.image.load(path.join(settings.IMG_FOLDER, settings.WALL_IMG)).convert(), settings.SIZE)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * settings.TILESIZE
        self.rect.topleft = self.pos

class Ground(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        # Add to sprites group
        self._layer = settings.GROUND_LAYER
        self.groups = game.all_sprites, game.ground
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface(settings.SIZE)
        self.image.fill(settings.BGCOLOR)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * settings.TILESIZE
        self.rect.topleft = self.pos

class Spritesheet:
    # Utility class for loading and parsing spritessheets
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()

    def get_image(self, x, y, width, height, size):
        # Grab an image out of a larger Spreadsheet
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pg.transform.scale(image, (int(size[0]), int(size[1])))
        return image

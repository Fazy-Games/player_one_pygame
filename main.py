# Imports
# random and pathlib are parts of the Python Standard Library, basically core features of the language
# random is a library for generating pseudo-random numbers, with all kinds of distributions, ranges etc
# pathlib is basically a better way to deal with file paths (because file paths can be a mess, Windows vs Unix different formats, relative vs absolute paths etc
# the "from XYZ import ABC" notation basically means that we are only important one class or function or something from the library
# pygame is the one library that needs to be installed with pip, it is not part of the Python Standard Library
import random
from pathlib import Path
import pygame

# and finally config is my own file, config.py which is just kinda poorly named file with constants and whatnot
import config

### INITIALIZATION
# Create the main window and set it to have desired width and height, the double brackets are here because pygame.display.set_mode expects a tuple
# Tuple is basically a pair of two variables, look it up if you want
# Alternatively it could be in two lines like this:
# windows_size_tuple = (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
# MAIN_WINDOW = pygame.display.set_mode(windows_size_tuple)
MAIN_WINDOW = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

## Changing the window title to the desired text (string)
pygame.display.set_caption(config.CAPTION_STRING)

## Directories
# Path().absolute() basically creates a Path objects (used to handling file paths) and gets its absolute path, so in this case the path to the directory the
# script runs in, you can print it to see, like print(BASE_DIR)
root_dir_path = Path()

# This is a Pathlib way of joining two paths, from say "C:/Wow/Elite" to "C:/Wow/Elite/Assets"
assets_dir_path = root_dir_path / 'Assets'

## Load and setup image assets
# Whoa, a lot is happening on this line 44. Two function calls (pygame.transform.scale() and pygame.image.load(). Start from the inside, we are calling
# image.load with just one parameter – a path to file, kinda like this pygame.image.load("C:/Wow/Elite/picture.png") but we are being fancy about it and are
# combining the path in place there, from three elements - use the assets directory path, look for Sprites subdirectory and in there, grab the png
# this function loads the image and returns object of Surface type (this is pygame stuff), which is what the image.scale() function wants as its input
# So we are dumping output of the load function into the scale function, which also takes another Tuple - heigh and width it should scale the image to
# The result is another Surface, which we will use in the actual game to show on screen, we just needed to load and resize iz
# This is done with all the images

player_spaceship_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'player_spaceship_blue_cruiser.png'),
                                              (config.PLAYER_WIDTH, config.PLAYER_HEIGHT))
# Notice that I did not put he bullet size in config yet, so it is hardcoded
player_bullet_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'bullet_basic_blue.png'),
                                           (16, 16))
green_enemy_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'spacebug_green.png'),
                                         (config.GREEN_ENEMY_WIDTH, config.GREEN_ENEMY_HEIGHT))
blue_background_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Backgrounds' / 'blue_nebula_8_bg.png'),
                                             (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

## Change the default pygame icon to a nice MaSu icon
program_icon = pygame.image.load((assets_dir_path / 'icon.png'))
pygame.display.set_icon(program_icon)

## Setup music and sounds
# This is mostly pygame stuff, mixer is the object responsible for playing music and sounds and has to be initialized, all audio has to be loaded in,
# similar to loading images above
pygame.mixer.init()
player_one_song_path = assets_dir_path / 'Sounds' / 'player_one.mp3'
pygame.mixer.music.load(player_one_song_path)
pygame.mixer.music.set_volume(0.25)
pygame.mixer.music.play()

# We are preparing these but not playing them yet
enemy_hit_sound = pygame.mixer.Sound(assets_dir_path / 'Sounds' / "Hit_Hurt4.wav")
enemy_hit_sound.set_volume(0.03)
laser_sound = pygame.mixer.Sound(assets_dir_path / 'Sounds' / "Laser_Shoot3.wav")
laser_sound.set_volume(0.03)


# This function basically says "smash this number value between these two limits, say it gets (7, -1, 5) then it retuns 5, we use it mostly to avoid things
# getting outside of the game window
def clamp_integer(value, lower_bound, upper_bound):
    return lower_bound if value < lower_bound else upper_bound if value > upper_bound else value


# Get a list of enemies, move them down (along the y axis, point 0,0 is the left top corner of the window), if they are below bottom of the screen,
# remove them from the list (which means they won't be drawn and basically will cease to exist)
def handle_enemies(enemies):
    for enemy in enemies:
        enemy.y += config.GREEN_ENEMY_VELOCITY
        if enemy.y > config.WINDOW_HEIGHT:
            enemies.remove(enemy)


# Similarly to handling enemies, we first move each bullet (these are player bullets exclusively right now) based on its velocity upwards (notice the -=) and
# then for each individual bullet, we check every single enemy with the pygame function colliderect, collide rectangle, which basically checks if two
# rectangles overlap. If they do, delete both the bullet and the enemy
# The "continue" statement skips rest of the "for enemy in enemies" loop, making sure that this one bullet will not delete more than 1 enemy
# We also remove bullets that fly above the screen level
def handle_bullets(bullets, enemies):
    for bullet in bullets:
        bullet.y -= config.PLAYER_BULLET_VELOCITY
        for enemy in enemies:
            if enemy.colliderect(bullet):
                bullets.remove(bullet)
                enemies.remove(enemy)
                pygame.mixer.Sound.play(enemy_hit_sound)
                continue
        if bullet.y < 0:
            bullets.remove(bullet)


# This function gets the state of the keyboard (keys_pressed) and moves the player object accordingly
# Every condition reads like this "if direction button (WSAD or arrows) was pressed and moving on defined player velocity would not result in getting outside
# of the game window (minus some border space), move the player in such a way"
# The asymmetry is caused by the fact that the positioning defining point for player rectangle (and any rectangle) is their top left corner,
# so we have to keep that in mind for the not leaving game window check
def handle_movement(keys_pressed, player):
    if keys_pressed[pygame.K_UP] and player.y - config.PLAYER_VELOCITY > config.BORDER_SPACE:
        player.y -= config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_DOWN] and player.y + config.PLAYER_VELOCITY + player.height < config.WINDOW_HEIGHT - config.BORDER_SPACE:
        player.y += config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_LEFT] and player.x - config.PLAYER_VELOCITY > config.BORDER_SPACE:
        player.x -= config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_RIGHT] and player.x + config.PLAYER_VELOCITY + player.width < config.WINDOW_WIDTH - config.BORDER_SPACE:
        player.x += config.PLAYER_VELOCITY


# This is a simplifed version of the function - the background is static here
# It uses pygame function blit which draws the images on the next frame (every frame is remade completely)
# AFAIK this is pretty standard with graphics
# MAIN_WINDOW.blit just gets what to show and where
# Then also blit every enemy and bullet and don't forget to update the display with this new frame (or Surface, to be more precise)
def draw_window(player, bullets, enemies):
    MAIN_WINDOW.blit(blue_background_img, (0, 0))

    MAIN_WINDOW.blit(player_spaceship_img, (player.x, player.y))

    for bullet in bullets:
        MAIN_WINDOW.blit(player_bullet_img, (bullet.x, bullet.y))

    for enemy in enemies:
        MAIN_WINDOW.blit(green_enemy_img, (enemy.x, enemy.y))
    pygame.display.update()


# Moving background version, try it out by swapping it in
# TL;DR version is "We only have one image, but we have to blit it twice to create this illusion of one seamless background. As it travels down,
# it would be blank on top, so we fill that with bottom of the same image. So I have 2 images of the same background that keep scrolling in a way that they
# always cover the whole game window. For that we need to keep track of how much it scrolled (that is the weird background_shift_y variable,
# which is something called a function attribute (initialized below the function)) and have to do a bit of math on how to show these two images (the percent
# sign is modulo)
def draw_window_better(player, bullets, enemies):
    draw_window_better.background_shift_y += 1
    relative_bg_y = draw_window_better.background_shift_y % blue_background_img.get_rect().height
    MAIN_WINDOW.blit(blue_background_img, (0, relative_bg_y - blue_background_img.get_rect().height))
    if draw_window_better.background_shift_y > config.WINDOW_HEIGHT:
        MAIN_WINDOW.blit(blue_background_img, (0, relative_bg_y))

    MAIN_WINDOW.blit(player_spaceship_img, (player.x, player.y))

    for bullet in bullets:
        MAIN_WINDOW.blit(player_bullet_img, (bullet.x, bullet.y))

    for enemy in enemies:
        MAIN_WINDOW.blit(green_enemy_img, (enemy.x, enemy.y))
    pygame.display.update()
draw_window_better.background_shift_y = config.WINDOW_HEIGHT


# This function gets the enemies list and the time (imagine a number like 13543 ms) when an enemy last spawned
# The if clause asks whether a second has passed since that, if that's the case, spawn a new enemy, otherwise just return the old spawn time
# The spawning itself is just generating two random numbers (for x and y position) and then creating another rectangle and adding it to the list of enemies
def handle_enemy_spawn(enemies, last_spawn_time):
    current_time = pygame.time.get_ticks()
    if current_time > last_spawn_time + config.GREEN_ENEMY_SPAWN_PERIOD:
        enemy_x_position = random.randint(config.BORDER_SPACE, config.WINDOW_WIDTH - config.BORDER_SPACE - config.GREEN_ENEMY_WIDTH)
        enemy_y_position = random.randint(config.BORDER_SPACE, config.WINDOW_HEIGHT / 4)

        enemy = pygame.Rect(enemy_x_position, enemy_y_position, config.GREEN_ENEMY_WIDTH, config.GREEN_ENEMY_HEIGHT)

        enemies.append(enemy)
        spawn_time = current_time
    else:
        spawn_time = last_spawn_time

    # We are returning spawn time to have it available in the main function for the next iteration
    return spawn_time


# This function gets the bullets list and the time when we last shot a bullet, it also gets player object (to know player location so we can align the
# bullets from there)
# Otherwise it is very similar to handle_enemy_spawn, just with no RNG
def handle_shooting(player, bullets, last_shot_time):
    current_time = pygame.time.get_ticks()
    if current_time - last_shot_time > config.PLAYER_SHOOTING_PERIOD:
        bullet = pygame.Rect(player.x + config.PLAYER_BULLET_WIDTH, player.y, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
        bullets.append(bullet)
        pygame.mixer.Sound.play(laser_sound)
        shot_time = current_time
    else:
        shot_time = last_shot_time

    # We are returning shot time to have it available in the main function for the next iteration
    return shot_time


def main():
    # Create the actual player object (not the image, graphics, but the actual rectangle for game handling)
    # It says " create rectangle of width = config.PLAYER_WIDTH, heigh = config.PLAYER_HEIGHT in middle of the screen (horizontally, on x axis),
    # near bottom (7/8 of window height from top)
    player = pygame.Rect(config.WINDOW_WIDTH / 2, (config.WINDOW_HEIGHT / 8) * 7, config.PLAYER_WIDTH, config.PLAYER_HEIGHT)

    # Real time games almost always use a game loop, which has some sort of internal clock, we are creating that here
    clock = pygame.time.Clock()
    # Since the game will run in a basically endless loop, we could use a variable to keep track of whether it should keep running
    game_is_running = True

    # Two nice lists to keep track of bullets and enemies, empty for now
    bullets = []
    enemies = []

    # These two variables will be used as primitive trackers for cooldowns, in this case cooldown of shooting and cooldown of enemy spawning
    last_shot_time = 0
    last_spawn_time = 0

    ### THE GAME LOOP
    while game_is_running:
        # Advance the game time, each iteration of this loop is basically one frame, so this advances the game clock by 1000 / 60 (in milliseconds)
        clock.tick(config.FPS)

        # This is pygame stuff, the function pygame.event.get() gets all the events from the queue, for now that is only about handling players pressing
        # Escape or clicking the close button (the top right cross)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_is_running = False
                pygame.quit()

        # We have to check game_is_running variable to prevent running the code below that, which would cause errors (because pygame.quit() has already been
        # called)
        if not game_is_running:
            break

        # This pygame function gets all the keypresses that happened since previous tick and returns as an array of zeroes and ones (falses and trues,
        # basically), giving you an accurate state of the keyboard
        keys_pressed = pygame.key.get_pressed()

        # First we handle spawning new enemies, this is done randomly and relies on whether enough time has passed since the previous spawn
        last_spawn_time = handle_enemy_spawn(enemies, last_spawn_time)

        # Handling shooting, the condition basically reads "check if LCTRL was pressed since last tick"
        if keys_pressed[pygame.K_LCTRL]:
            last_shot_time = handle_shooting(player, bullets, last_shot_time)

        # Handling player movements
        handle_movement(keys_pressed, player)

        # Handling bullet movements and bullets hitting enemies
        handle_bullets(bullets, enemies)

        # Handle enemy movement (pretty primitive right now)
        handle_enemies(enemies)

        # And finally draw everything
        draw_window_better(player, bullets, enemies)


if __name__ == '__main__':
    main()

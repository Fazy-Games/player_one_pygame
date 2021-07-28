import os
import pygame
import random
import config
from pathlib import Path

# Directories
BASE_DIR = Path().absolute()
ASSETS_DIR = os.path.join(BASE_DIR, 'Assets')

# INIT
MAIN_WINDOW = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
pygame.display.set_caption(config.CAPTION_STRING)

# Load and setup image assets
PLAYER_SPACESHIP_IMAGE = pygame.image.load(os.path.join(ASSETS_DIR, 'Sprites', 'player_spaceship_blue_cruiser.png'))
PLAYER_SPACESHIP = pygame.transform.scale(PLAYER_SPACESHIP_IMAGE, (config.PLAYER_WIDTH, config.PLAYER_HEIGHT))
PLAYER_BULLET_IMAGE = pygame.image.load(os.path.join(ASSETS_DIR, 'Sprites', 'bullet_basic_blue.png'))
PLAYER_BULLET = pygame.transform.scale(PLAYER_BULLET_IMAGE, (16, 16))
GREEN_SPACESHIP_IMAGE = pygame.image.load(os.path.join(ASSETS_DIR, 'Sprites', 'spacebug_green.png'))
GREEN_SPACESHIP = pygame.transform.rotate(pygame.transform.scale(GREEN_SPACESHIP_IMAGE, (config.PLAYER_WIDTH*2, config.PLAYER_HEIGHT*2)), 180)
BLUE_BACKGROUND = pygame.image.load(os.path.join(ASSETS_DIR, 'Backgrounds', 'blue_nebula_8_bg.png'))
SPACE = pygame.transform.scale(BLUE_BACKGROUND, (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

# Setup program icon
ICON = os.path.join(ASSETS_DIR, 'icon.png')
PROGRAM_ICON = pygame.image.load(ICON)
pygame.display.set_icon(PROGRAM_ICON)

# Load and setup music and sounds
pygame.mixer.init()
THE_SONG = os.path.join(ASSETS_DIR, 'Sounds', 'player_one.mp3')
pygame.mixer.music.load(THE_SONG)
pygame.mixer.music.set_volume(0.25)
pygame.mixer.music.play()
enemy_hit_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'Sounds', "Hit_Hurt4.wav"))
enemy_hit_sound.set_volume(0.03)
laser_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'Sounds', "Laser_Shoot3.wav"))
laser_sound.set_volume(0.03)


def clamp_integer(value, lower_bound, upper_bound):
    return lower_bound if value < lower_bound else upper_bound if value > upper_bound else value


def handle_enemies(enemies):
    for enemy in enemies:
        enemy.y += config.GREEN_ENEMY_VELOCITY
        if enemy.y > config.WINDOW_HEIGHT:
            enemies.remove(enemy)


def handle_bullets(bullets, enemies):
    for bullet in bullets:
        bullet.y -= config.PLAYER_BULLET_SPEED
        is_destroyed = False
        for enemy in enemies:
            if enemy.colliderect(bullet) and not is_destroyed:
                bullets.remove(bullet)
                enemies.remove(enemy)
                pygame.mixer.Sound.play(enemy_hit_sound)
                is_destroyed = True
        if bullet.y < 0 and not is_destroyed:
            bullets.remove(bullet)


def handle_movement(keys_pressed, player, jump_is_ready):
    if keys_pressed[pygame.K_UP] and player.y - config.PLAYER_VELOCITY > config.BORDER_SPACE:
        player.y -= config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_DOWN] and player.y + config.PLAYER_VELOCITY + player.height < config.WINDOW_HEIGHT - config.BORDER_SPACE:
        player.y += config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_SPACE]:
        if keys_pressed[pygame.K_RIGHT] and keys_pressed[pygame.K_LEFT]:
            return jump_is_ready

        if keys_pressed[pygame.K_RIGHT] and jump_is_ready:
            player.x = clamp_integer(player.x + config.DASH_VELOCITY + player.width,
                                     config.BORDER_SPACE, config.WINDOW_WIDTH - config.BORDER_SPACE - player.width)
            jump_is_ready = False
            return jump_is_ready

        if keys_pressed[pygame.K_LEFT] and jump_is_ready:
            player.x = clamp_integer(player.x - config.DASH_VELOCITY, config.BORDER_SPACE, config.WINDOW_WIDTH - config.BORDER_SPACE)
            jump_is_ready = False
            return jump_is_ready

    if keys_pressed[pygame.K_LEFT] and player.x - config.PLAYER_VELOCITY > config.BORDER_SPACE:
        player.x -= config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_RIGHT] and player.x + config.PLAYER_VELOCITY + player.width < config.WINDOW_WIDTH - config.BORDER_SPACE:
        player.x += config.PLAYER_VELOCITY
    return jump_is_ready


def draw_window(player, bg_y, bullets, enemies):
    relative_bg_y = bg_y % SPACE.get_rect().height
    MAIN_WINDOW.blit(SPACE, (0, relative_bg_y - SPACE.get_rect().height))
    if bg_y > config.WINDOW_HEIGHT:
        MAIN_WINDOW.blit(SPACE, (0, relative_bg_y))

    MAIN_WINDOW.blit(PLAYER_SPACESHIP, (player.x, player.y))

    for bullet in bullets:
        MAIN_WINDOW.blit(PLAYER_BULLET, (bullet.x, bullet.y))

    for enemy in enemies:
        MAIN_WINDOW.blit(GREEN_SPACESHIP, (enemy.x, enemy.y))
    pygame.display.update()


def main():
    player = pygame.Rect(config.WINDOW_WIDTH / 2, (config.WINDOW_HEIGHT / 8) * 7, config.PLAYER_WIDTH, config.PLAYER_HEIGHT)
    clock = pygame.time.Clock()
    game_is_running = True
    bg_y = config.WINDOW_HEIGHT
    jump_is_ready = True
    jump_cd = config.FPS * 3
    bullets = []
    enemies = []
    previous_time = 0
    previous_time_enemy = 0
    i = 0
    while game_is_running:
        clock.tick(config.FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_is_running = False
                pygame.quit()

        if not game_is_running:
            break
        keys_pressed = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        if current_time - previous_time_enemy > (1500-i):
            i = i+25
            if i > 1400:
                i = 1400
            previous_time_enemy = current_time
            enemy = pygame.Rect(random.randint(config.BORDER_SPACE, config.WINDOW_WIDTH - config.BORDER_SPACE - config.PLAYER_WIDTH*2),
                                random.randint(config.BORDER_SPACE, int(config.WINDOW_HEIGHT/4)),
                                config.PLAYER_WIDTH*2, config.PLAYER_HEIGHT*2)
            enemies.append(enemy)

        if keys_pressed[pygame.K_LCTRL]:
            if current_time - previous_time > 133:
                previous_time = current_time
                bullet = pygame.Rect(
                    player.x + player.width / 4, player.y, config.PLAYER_WIDTH / 4, config.PLAYER_HEIGHT / 4)
                bullets.append(bullet)
                pygame.mixer.Sound.play(laser_sound)

        if not jump_is_ready:
            jump_cd -= 1
            if jump_cd == 0:
                jump_cd = config.FPS * 3
                jump_is_ready = True
        jump_is_ready = handle_movement(keys_pressed, player, jump_is_ready)
        handle_bullets(bullets, enemies)
        handle_enemies(enemies)
        draw_window(player, bg_y, bullets, enemies)
        bg_y += 1


if __name__ == '__main__':
    main()

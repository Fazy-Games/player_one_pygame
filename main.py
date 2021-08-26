import random
from pathlib import Path
import pygame
import config

# region Initialization
MAIN_WINDOW = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
pygame.display.set_caption(config.CAPTION_STRING)

## Directories
root_dir_path = Path()
assets_dir_path = root_dir_path / 'Assets'

## Image assets
player_spaceship_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'player_spaceship_blue_cruiser.png'), (config.PLAYER_WIDTH,
                                                                                                                                     config.PLAYER_HEIGHT))
player_bullet_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'bullet_basic_blue.png'), (16, 16))
green_enemy_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'spacebug_green.png'), (config.GREEN_ENEMY_WIDTH,
                                                                                                                 config.GREEN_ENEMY_HEIGHT))
blue_background_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Backgrounds' / 'blue_nebula_8_bg.png'), (config.WINDOW_WIDTH,
                                                                                                                           config.WINDOW_HEIGHT))
## Icon
program_icon = pygame.image.load((assets_dir_path / 'icon.png'))
pygame.display.set_icon(program_icon)

## Music and sounds
pygame.mixer.init()
player_one_song_path = assets_dir_path / 'Sounds' / 'player_one.mp3'
pygame.mixer.music.load(player_one_song_path)
pygame.mixer.music.set_volume(0.25)
pygame.mixer.music.play()

enemy_hit_sound = pygame.mixer.Sound(assets_dir_path / 'Sounds' / "Hit_Hurt4.wav")
enemy_hit_sound.set_volume(0.03)
laser_sound = pygame.mixer.Sound(assets_dir_path / 'Sounds' / "Laser_Shoot3.wav")
laser_sound.set_volume(0.03)

## Fonts
pygame.font.init()
base_font = pygame.font.SysFont('Consolas', 20)
# endregion


def clamp_integer(value, lower_bound, upper_bound):
    return lower_bound if value < lower_bound else upper_bound if value > upper_bound else value


def handle_enemies(enemies):
    for enemy in enemies:
        enemy.y += config.GREEN_ENEMY_VELOCITY
        if enemy.y > config.WINDOW_HEIGHT:
            enemies.remove(enemy)


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


def handle_movement(keys_pressed, player, sprint_flag):
    if keys_pressed[pygame.K_UP] \
       and player.y - (config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY) > config.BORDER_SPACE:
        player.y -= config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_DOWN] \
       and player.y + (config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY) + player.height < config.WINDOW_HEIGHT - config.BORDER_SPACE:
        player.y += config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_LEFT] \
       and player.x - (config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY) > config.BORDER_SPACE:
        player.x -= config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY

    if keys_pressed[pygame.K_RIGHT] \
       and player.x + (config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY) + player.width < config.WINDOW_WIDTH - config.BORDER_SPACE:
        player.x += config.PLAYER_SPRINT_VELOCITY if sprint_flag else config.PLAYER_VELOCITY


def draw_window(player, bullets, enemies, sprint_flag):
    draw_window.background_shift_y += 1
    relative_bg_y = draw_window.background_shift_y % blue_background_img.get_rect().height
    MAIN_WINDOW.blit(blue_background_img, (0, relative_bg_y - blue_background_img.get_rect().height))
    if draw_window.background_shift_y > config.WINDOW_HEIGHT:
        MAIN_WINDOW.blit(blue_background_img, (0, relative_bg_y))

    MAIN_WINDOW.blit(player_spaceship_img, (player.x, player.y))

    for bullet in bullets:
        MAIN_WINDOW.blit(player_bullet_img, (bullet.x, bullet.y))

    for enemy in enemies:
        MAIN_WINDOW.blit(green_enemy_img, (enemy.x, enemy.y))

    sprint_state = 'Active' if sprint_flag else 'Inactive'
    font_surface = base_font.render(f'Sprint: {sprint_state}', False, (255, 255, 255))
    MAIN_WINDOW.blit(font_surface, (0, config.WINDOW_HEIGHT - 24))
    pygame.display.update()


draw_window.background_shift_y = config.WINDOW_HEIGHT


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
    return spawn_time


def handle_shooting(player, bullets, last_shot_time):
    current_time = pygame.time.get_ticks()
    if current_time - last_shot_time > config.PLAYER_SHOOTING_PERIOD:
        bullet = pygame.Rect(player.x + config.PLAYER_BULLET_WIDTH, player.y, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
        bullets.append(bullet)
        pygame.mixer.Sound.play(laser_sound)
        shot_time = current_time
    else:
        shot_time = last_shot_time
    return shot_time


def handle_sprint(keys_pressed, sprint_flag, last_sprint_time):
    current_time = pygame.time.get_ticks()

    if sprint_flag and current_time - config.PLAYER_SPRINT_DURATION > last_sprint_time:
        sprint_flag = False
        return sprint_flag, last_sprint_time

    if keys_pressed[pygame.K_LSHIFT] and (current_time - last_sprint_time > config.PLAYER_SPRINT_PERIOD or last_sprint_time == 0):
        sprint_flag = True
        # Add a sound effect possibly
        last_sprint_time = current_time
        return sprint_flag, last_sprint_time

    return sprint_flag, last_sprint_time


def main():
    player = pygame.Rect(config.WINDOW_WIDTH / 2, (config.WINDOW_HEIGHT / 8) * 7, config.PLAYER_WIDTH, config.PLAYER_HEIGHT)
    clock = pygame.time.Clock()
    game_is_running = True

    bullets = []
    enemies = []

    last_shot_time = 0
    last_spawn_time = 0
    last_sprint_time = 0
    sprint_flag = False

    while game_is_running:
        clock.tick(config.FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_is_running = False
                pygame.quit()
        if not game_is_running:
            break

        keys_pressed = pygame.key.get_pressed()

        last_spawn_time = handle_enemy_spawn(enemies, last_spawn_time)

        if keys_pressed[pygame.K_LCTRL]:
            last_shot_time = handle_shooting(player, bullets, last_shot_time)

        sprint_flag, last_sprint_time = handle_sprint(keys_pressed, sprint_flag, last_sprint_time)

        handle_movement(keys_pressed, player, sprint_flag)
        handle_bullets(bullets, enemies)
        handle_enemies(enemies)
        draw_window(player, bullets, enemies, sprint_flag)


if __name__ == '__main__':
    main()

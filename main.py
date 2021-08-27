import random
from pathlib import Path
import pygame
import config
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# region Initialization
MAIN_WINDOW = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
pygame.display.set_caption(config.CAPTION_STRING)

## Directories
root_dir_path = Path()
assets_dir_path = root_dir_path / 'Assets'

## Image assets
player_spaceship_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'player_spaceship_blue_cruiser.png').convert_alpha(), (config.PLAYER_WIDTH,
                                                                                                                                     config.PLAYER_HEIGHT))
player_bullet_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'bullet_basic_blue.png').convert_alpha(), (16, 16))
green_enemy_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Sprites' / 'spacebug_green.png').convert_alpha(), (config.GREEN_ENEMY_WIDTH,
                                                                                                                 config.GREEN_ENEMY_HEIGHT))
blue_background_img = pygame.transform.scale(pygame.image.load(assets_dir_path / 'Backgrounds' / 'blue_nebula_8_bg.png').convert(), (config.WINDOW_WIDTH,
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
laser_sound_boosted = pygame.mixer.Sound(assets_dir_path / 'Sounds' / "Laser_Shoot3.wav")
laser_sound.set_volume(0.03)
laser_sound_boosted.set_volume(0.05)

## Fonts
pygame.font.init()
base_font = pygame.font.SysFont('Consolas', 20)
# endregion


def clamp_integer(value, lower_bound, upper_bound):
    return lower_bound if value < lower_bound else upper_bound if value > upper_bound else value


class Game:
    def __init__(self):
        self.player_rect = pygame.Rect(config.WINDOW_WIDTH / 2, (config.WINDOW_HEIGHT / 8) * 7, config.PLAYER_WIDTH, config.PLAYER_HEIGHT)
        self.clock = pygame.time.Clock()
        self.is_running = True

        self.bullets = []
        self.enemies = []

        self.last_shot_time = 0
        self.last_spawn_time = 0
        self.last_sprint_time = 0
        self.last_gun_boost_time = 0
        self.sprint_flag = False
        self.gunboost_charges = 0
        self.score = 0

        self.background_shift_y = config.WINDOW_HEIGHT

    def game_loop(self):
        while self.is_running:
            self.clock.tick(config.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                    pygame.quit()
            if not self.is_running:
                break

            keys_pressed = pygame.key.get_pressed()

            self.handle_enemy_spawn()

            if keys_pressed[pygame.K_f] and (self.last_gun_boost_time == 0 or pygame.time.get_ticks() - config.PLAYER_GUN_BOOST_COOLDOWN > self.last_gun_boost_time):
                self.gunboost_charges = 30
                self.last_gun_boost_time = pygame.time.get_ticks()

            if keys_pressed[pygame.K_LCTRL]:
                self.handle_shooting()
                if self.gunboost_charges and self.last_shot_time == pygame.time.get_ticks():
                    self.gunboost_charges -= 1

            self.handle_sprint(keys_pressed)
            self.handle_movement(keys_pressed)
            self.handle_bullets()
            self.handle_enemies()
            self.draw_window()

    def handle_enemies(self):
        for enemy in self.enemies:
            enemy.y += config.GREEN_ENEMY_VELOCITY
            if enemy.y > config.WINDOW_HEIGHT:
                self.enemies.remove(enemy)

    def handle_bullets(self):
        for bullet in self.bullets:
            bullet.y -= config.PLAYER_BULLET_VELOCITY
            for enemy in self.enemies:
                try:
                    if enemy.colliderect(bullet):
                        pygame.mixer.Sound.play(enemy_hit_sound)
                        self.score += 1000
                        self.enemies.remove(enemy)
                        self.bullets.remove(bullet)
                        continue
                except ValueError:
                    continue
            if bullet.y < 0:
                self.bullets.remove(bullet)

    def handle_movement(self, keys_pressed):
        if keys_pressed[pygame.K_UP] \
                and self.player_rect.y - (config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY) > config.BORDER_SPACE:
            self.player_rect.y -= config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

        if keys_pressed[pygame.K_DOWN] \
                and self.player_rect.y + (config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY) + self.player_rect.height < config.WINDOW_HEIGHT - config.BORDER_SPACE:
            self.player_rect.y += config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

        if keys_pressed[pygame.K_LEFT] \
                and self.player_rect.x - (config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY) > config.BORDER_SPACE:
            self.player_rect.x -= config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

        if keys_pressed[pygame.K_RIGHT] \
                and self.player_rect.x + (config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY) + self.player_rect.width < config.WINDOW_WIDTH - config.BORDER_SPACE:
            self.player_rect.x += config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

    def draw_window(self):
        self.background_shift_y += 1
        relative_bg_y = self.background_shift_y % blue_background_img.get_rect().height
        MAIN_WINDOW.blit(blue_background_img, (0, relative_bg_y - blue_background_img.get_rect().height))
        if self.background_shift_y > config.WINDOW_HEIGHT:
            MAIN_WINDOW.blit(blue_background_img, (0, relative_bg_y))

        MAIN_WINDOW.blit(player_spaceship_img, (self.player_rect.x, self.player_rect.y))

        for bullet in self.bullets:
            MAIN_WINDOW.blit(player_bullet_img, (bullet.x, bullet.y))

        for enemy in self.enemies:
            MAIN_WINDOW.blit(green_enemy_img, (enemy.x, enemy.y))

        sprint_state = 'Active' if self.sprint_flag else 'Inactive'
        sprint_status_text = base_font.render(f'Sprint: {sprint_state}', False, (255, 255, 255))
        gunboost_charges_text = base_font.render(f'Extra bullets: {self.gunboost_charges}', False, (255, 255, 255))
        MAIN_WINDOW.blit(sprint_status_text, (0, config.WINDOW_HEIGHT - 48))
        MAIN_WINDOW.blit(gunboost_charges_text, (0, config.WINDOW_HEIGHT - 24))

        score_text = base_font.render(f'SCORE: {self.score}', False, (255, 255, 255))
        MAIN_WINDOW.blit(score_text, (config.WINDOW_WIDTH - score_text.get_width(), config.WINDOW_HEIGHT - 24))
        pygame.display.update()

    def handle_enemy_spawn(self):
        current_time = pygame.time.get_ticks()
        if current_time > self.last_spawn_time + config.GREEN_ENEMY_SPAWN_PERIOD:
            enemy_x_position = random.randint(config.BORDER_SPACE, config.WINDOW_WIDTH - config.BORDER_SPACE - config.GREEN_ENEMY_WIDTH)
            enemy_y_position = random.randint(config.BORDER_SPACE, config.WINDOW_HEIGHT / 4)

            enemy = pygame.Rect(enemy_x_position, enemy_y_position, config.GREEN_ENEMY_WIDTH, config.GREEN_ENEMY_HEIGHT)

            self.enemies.append(enemy)
            self.last_spawn_time = current_time

    def handle_shooting(self):
        current_time = pygame.time.get_ticks()
        if self.gunboost_charges:
            if current_time - self.last_shot_time > config.PLAYER_SHOOTING_COOLDOWN/2:
                bullet_one = pygame.Rect(self.player_rect.x + config.PLAYER_BULLET_WIDTH-7, self.player_rect.y, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                bullet_two = pygame.Rect(self.player_rect.x + config.PLAYER_BULLET_WIDTH+7, self.player_rect.y, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                self.bullets.extend((bullet_one, bullet_two))
                pygame.mixer.Sound.play(laser_sound_boosted)
                self.last_shot_time = current_time
        else:
            if current_time - self.last_shot_time > config.PLAYER_SHOOTING_COOLDOWN:
                bullet = pygame.Rect(self.player_rect.x + config.PLAYER_BULLET_WIDTH, self.player_rect.y, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                self.bullets.append(bullet)
                pygame.mixer.Sound.play(laser_sound)
                self.last_shot_time = current_time

    def handle_sprint(self, keys_pressed):
        current_time = pygame.time.get_ticks()

        if self.sprint_flag and current_time - config.PLAYER_SPRINT_DURATION > self.last_sprint_time:
            self.sprint_flag = False

        if keys_pressed[pygame.K_LSHIFT] and (current_time - self.last_sprint_time > config.PLAYER_SPRINT_COOLDOWN or self.last_sprint_time == 0):
            self.sprint_flag = True
            # Add a sound effect possibly
            self.last_sprint_time = current_time


def main():
    the_game = Game()
    the_game.game_loop()


if __name__ == '__main__':
    main()

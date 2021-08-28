import random
from pathlib import Path
import pygame as pg
import config
import srt


class Game:
    def __init__(self):
        self.player_rect = pg.Rect(config.WINDOW_WIDTH / 2, (config.WINDOW_HEIGHT / 8) * 7, config.PLAYER_WIDTH,
                                   config.PLAYER_HEIGHT)
        self.clock = pg.time.Clock()
        self.is_running = True

        self.bullets = []
        self.enemies = []

        self.last_shot_time = 0
        self.last_spawn_time = 0
        self.last_sprint_time = config.PLAYER_INITIAL_SPRINT_COOLDOWN
        self.last_gunboost_time = config.PLAYER_INITIAL_GUNBOOST_COOLDOWN
        self.last_bomb_time = config.PLAYER_INITIAL_BOMB_COOLDOWN
        self.sprint_flag = False
        self.gunboost_charges = 0
        self.score = 0
        self.health = config.PLAYER_STARTING_HEALTH
        self.background_shift_y = config.WINDOW_HEIGHT
        self.current_time = 0

        self.game_window = pg.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pg.display.set_caption(config.CAPTION_STRING)

        root_dir_path = Path()
        assets_dir_path = root_dir_path / 'Assets'

        self.player_spaceship_img = pg.transform.scale(
            pg.image.load(assets_dir_path / 'Sprites' / 'player_spaceship_blue_cruiser.png').convert_alpha(),
            (config.PLAYER_WIDTH,
             config.PLAYER_HEIGHT))
        self.player_bullet_img = pg.transform.scale(
            pg.image.load(assets_dir_path / 'Sprites' / 'bullet_basic_blue.png').convert_alpha(), (16, 16))
        self.green_enemy_img = pg.transform.scale(
            pg.image.load(assets_dir_path / 'Sprites' / 'spacebug_green.png').convert_alpha(),
            (config.GREEN_ENEMY_WIDTH,
             config.GREEN_ENEMY_HEIGHT))
        self.blue_background_img = pg.transform.scale(
            pg.image.load(assets_dir_path / 'Backgrounds' / 'blue_nebula_8_bg.png').convert(), (config.WINDOW_WIDTH,
                                                                                                config.WINDOW_HEIGHT))
        program_icon = pg.image.load((assets_dir_path / 'icon.png'))
        pg.display.set_icon(program_icon)

        pg.mixer.init()
        player_one_song_path = assets_dir_path / 'Sounds' / 'player_one.mp3'
        pg.mixer.music.load(player_one_song_path)
        pg.mixer.music.set_volume(0.25)
        pg.mixer.music.play()

        self.enemy_hit_sound = pg.mixer.Sound(assets_dir_path / 'Sounds' / "Hit_Hurt4.wav")
        self.enemy_hit_sound.set_volume(0.03)
        self.laser_sound = pg.mixer.Sound(assets_dir_path / 'Sounds' / "Laser_Shoot3.wav")
        self.laser_sound_boosted = pg.mixer.Sound(assets_dir_path / 'Sounds' / "Laser_Shoot3.wav")
        self.laser_sound.set_volume(0.03)
        self.laser_sound_boosted.set_volume(0.05)

        pg.font.init()
        self.base_font = pg.font.SysFont('Consolas', 16)
        self.subtitles_font = pg.font.SysFont('Consolas', 30)
        subtitles_file_path = assets_dir_path / 'player_one.srt'
        self.song_subtitles = None
        with open(subtitles_file_path, 'r', encoding='utf8') as srt_file:
            subtitle_generator = srt.parse(srt_file)
            self.song_subtitles = list(subtitle_generator)

    def game_loop(self):
        while self.is_running:
            self.clock.tick(config.FPS)
            self.current_time = pg.time.get_ticks()

            # region Handle events and quitting
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.is_running = False
                    pg.quit()
            if self.health <= 0:
                self.is_running = False
                print(f'Game over, your final score was {self.score}')
            if not self.is_running:
                break
            # endregion

            keys_pressed = pg.key.get_pressed()

            self.handle_enemy_spawn()

            if keys_pressed[pg.K_x]:
                self.handle_gunboost()

            if keys_pressed[pg.K_LCTRL]:
                self.handle_shooting()

            if keys_pressed[pg.K_SPACE]:
                self.handle_bomb()

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
                self.score -= 250
            if enemy.colliderect(self.player_rect):
                pg.mixer.Sound.play(self.enemy_hit_sound)
                # Add better sound
                self.enemies.remove(enemy)
                self.health -= 10

    def handle_bullets(self):
        for bullet in self.bullets:
            bullet.y -= config.PLAYER_BULLET_VELOCITY
            for enemy in self.enemies:
                try:
                    if enemy.colliderect(bullet):
                        pg.mixer.Sound.play(self.enemy_hit_sound)
                        self.score += 1000
                        if random.randint(1, 100) > 90:
                            self.health += 5
                        self.enemies.remove(enemy)
                        self.bullets.remove(bullet)
                        continue
                except ValueError:
                    continue
            if bullet.y < 0:
                self.bullets.remove(bullet)

    def handle_movement(self, keys_pressed):
        if keys_pressed[pg.K_UP] \
                and self.player_rect.y - (
                config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY) > config.BORDER_SPACE:
            self.player_rect.y -= config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

        if keys_pressed[pg.K_DOWN] \
                and self.player_rect.y + (
                config.PLAYER_SPRINT_VELOCITY if self.sprint_flag 
                else config.PLAYER_VELOCITY) + self.player_rect.height < config.WINDOW_HEIGHT - config.BORDER_SPACE:
            self.player_rect.y += config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

        if keys_pressed[pg.K_LEFT] \
                and self.player_rect.x - (
                config.PLAYER_SPRINT_VELOCITY if self.sprint_flag
                else config.PLAYER_VELOCITY) > config.BORDER_SPACE:
            self.player_rect.x -= config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

        if keys_pressed[pg.K_RIGHT] \
                and self.player_rect.x + (
                config.PLAYER_SPRINT_VELOCITY if self.sprint_flag 
                else config.PLAYER_VELOCITY) + self.player_rect.width < config.WINDOW_WIDTH - config.BORDER_SPACE:
            self.player_rect.x += config.PLAYER_SPRINT_VELOCITY if self.sprint_flag else config.PLAYER_VELOCITY

    def draw_status(self):
        sprint_cooldown = config.PLAYER_SPRINT_COOLDOWN - (self.current_time - self.last_sprint_time)
        sprint_cooldown_string = f'{sprint_cooldown/1000:.1f}' if sprint_cooldown > 0 else 'RDY'
        sprint_cooldown_text = self.base_font.render(f'Sprint CD: {sprint_cooldown_string}', False, (255, 255, 255))
        gunboost_cooldown = config.PLAYER_GUNBOOST_COOLDOWN - (self.current_time - self.last_gunboost_time)
        gunboost_cooldown_string = f'{gunboost_cooldown/1000:.1f}' if gunboost_cooldown > 0 else 'RDY'
        gunboost_cooldown_text = self.base_font.render(f'Gunboost CD: {gunboost_cooldown_string}', False, (255, 255, 255))
        gunboost_charges_text = self.base_font.render(f'Gunboost charges: {self.gunboost_charges}', False, (255, 255, 255))
        bomb_cooldown = config.PLAYER_BOMB_COOLDOWN - (self.current_time - self.last_bomb_time)
        bomb_cooldown_string = f'{bomb_cooldown/1000:.1f}' if bomb_cooldown > 0 else 'RDY'
        bomb_cooldown_text = self.base_font.render(f'Bomb CD: {bomb_cooldown_string}', False, (255, 255, 255))
        health_text = self.base_font.render(f'HEALTH: {self.health}', False, (255, 255, 255))
        score_text = self.base_font.render(f'SCORE: {self.score}', False, (255, 255, 255))
        for surface in (sprint_cooldown_text, gunboost_cooldown_text, gunboost_charges_text,
                        bomb_cooldown_text, health_text, score_text):
            surface.set_alpha(150)

        self.game_window.blit(sprint_cooldown_text, (0, config.WINDOW_HEIGHT - 5*sprint_cooldown_text.get_height()))
        self.game_window.blit(gunboost_cooldown_text, (0, config.WINDOW_HEIGHT - 4*gunboost_cooldown_text.get_height()))
        self.game_window.blit(gunboost_charges_text, (0, config.WINDOW_HEIGHT - 3*gunboost_charges_text.get_height()))
        self.game_window.blit(bomb_cooldown_text, (0, config.WINDOW_HEIGHT - 2*bomb_cooldown_text.get_height()))
        self.game_window.blit(health_text, (0, config.WINDOW_HEIGHT - health_text.get_height()))
        self.game_window.blit(score_text, (config.WINDOW_WIDTH - score_text.get_width(), config.WINDOW_HEIGHT - health_text.get_height()))

    def draw_lyrics(self):
        for subtitle in self.song_subtitles:
            subtitle_start_ms = subtitle.start.seconds * 1000 + subtitle.start.microseconds / 1000
            subtitle_end_ms = subtitle.end.seconds * 1000 + subtitle.end.microseconds / 1000
            if (self.current_time >= subtitle_start_ms) and (self.current_time < subtitle_end_ms):
                lyrics_text = self.subtitles_font.render(subtitle.content, False, (255, 255, 255))
                lyrics_text.set_alpha(200)
                self.game_window.blit(lyrics_text, (config.WINDOW_WIDTH/2 - lyrics_text.get_width()/2, 24))

    def draw_window(self):
        self.background_shift_y += 1
        relative_bg_y = self.background_shift_y % self.blue_background_img.get_rect().height
        self.game_window.blit(self.blue_background_img, (0, relative_bg_y - self.blue_background_img.get_rect().height))
        if self.background_shift_y > config.WINDOW_HEIGHT:
            self.game_window.blit(self.blue_background_img, (0, relative_bg_y))

        self.game_window.blit(self.player_spaceship_img, (self.player_rect.x, self.player_rect.y))

        for bullet in self.bullets:
            self.game_window.blit(self.player_bullet_img, (bullet.x, bullet.y))

        for enemy in self.enemies:
            self.game_window.blit(self.green_enemy_img, (enemy.x, enemy.y))
        self.draw_status()
        self.draw_lyrics()
        pg.display.update()

    def handle_enemy_spawn(self):
        if self.current_time > self.last_spawn_time + config.GREEN_ENEMY_SPAWN_PERIOD:
            enemy_x_position = random.randint(config.BORDER_SPACE,
                                              config.WINDOW_WIDTH - config.BORDER_SPACE - config.GREEN_ENEMY_WIDTH)
            enemy_y_position = random.randint(config.BORDER_SPACE, config.WINDOW_HEIGHT / 4)

            enemy = pg.Rect(enemy_x_position, enemy_y_position, config.GREEN_ENEMY_WIDTH, config.GREEN_ENEMY_HEIGHT)

            self.enemies.append(enemy)
            self.last_spawn_time = self.current_time

    def handle_shooting(self):
        if self.gunboost_charges:
            if self.current_time - self.last_shot_time > config.PLAYER_SHOOTING_COOLDOWN / 2:
                bullet_one = pg.Rect(self.player_rect.x + config.PLAYER_BULLET_WIDTH - 7, self.player_rect.y,
                                     config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                bullet_two = pg.Rect(self.player_rect.x + config.PLAYER_BULLET_WIDTH + 7, self.player_rect.y,
                                     config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                self.bullets.extend((bullet_one, bullet_two))
                pg.mixer.Sound.play(self.laser_sound_boosted)
                self.last_shot_time = self.current_time
                self.gunboost_charges -= 1
        else:
            if self.current_time - self.last_shot_time > config.PLAYER_SHOOTING_COOLDOWN:
                bullet = pg.Rect(self.player_rect.x + config.PLAYER_BULLET_WIDTH, self.player_rect.y,
                                 config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                self.bullets.append(bullet)
                pg.mixer.Sound.play(self.laser_sound)
                self.last_shot_time = self.current_time

    def handle_sprint(self, keys_pressed):
        if self.sprint_flag and self.current_time - config.PLAYER_SPRINT_DURATION > self.last_sprint_time:
            self.sprint_flag = False

        if keys_pressed[pg.K_LSHIFT] and self.current_time - self.last_sprint_time > config.PLAYER_SPRINT_COOLDOWN:
            self.sprint_flag = True
            # Add a sound effect possibly
            self.last_sprint_time = self.current_time

    def handle_gunboost(self):
        if self.current_time - config.PLAYER_GUNBOOST_COOLDOWN > self.last_gunboost_time:
            self.gunboost_charges = 40
            self.last_gunboost_time = self.current_time

    def handle_bomb(self):
        if self.current_time - config.PLAYER_BOMB_COOLDOWN > self.last_bomb_time:
            for n in range(63):
                bomb_bullet = pg.Rect(n*12, config.WINDOW_HEIGHT - 10, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                self.bullets.append(bomb_bullet)
            for n in range(63):
                bomb_bullet = pg.Rect(n*12, config.WINDOW_HEIGHT - 5, config.PLAYER_BULLET_WIDTH, config.PLAYER_BULLET_HEIGHT)
                self.bullets.append(bomb_bullet)
            pg.mixer.Sound.play(self.laser_sound_boosted)
            self.last_bomb_time = self.current_time

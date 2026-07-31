#!/usr/bin/env python3
"""
Woke Invaders - Redesigned with original anime character photos as player sprites
"""
import pygame, random, sys, os
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 800, 600, 60
BLACK, WHITE, PURPLE, PINK, HOT_PINK = (0,0,0), (255,255,255), (160,40,200), (255,105,180), (255,20,147)
RED, CYAN, GREEN, YELLOW, ORANGE = (220,30,40), (0,220,230), (40,200,60), (255,230,40), (255,140,20)
GRAY, GOLD, BLUE_HAIR, NEON_PINK, RAINBOW_PINK = (90,90,90), (255,200,40), (60,120,255), (255,20,147), (255,100,200)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WOKE INVADERS - Original Characters Edition")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("Courier", 42, bold=True)
font_med = pygame.font.SysFont("Courier", 24, bold=True)
font_small = pygame.font.SysFont("Courier", 18)
font_tiny = pygame.font.SysFont("Courier", 14)
# Load sprites from a "sprites" folder next to this script (works on Windows/Mac/Linux)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(SCRIPT_DIR, "sprites")

def load_and_scale(path, max_height=95):
    try: img = pygame.image.load(path).convert_alpha()
    except: img = pygame.image.load(path).convert()
    w, h = img.get_size()
    scale = max_height / float(h)
    return pygame.transform.smoothscale(img, (max(20, int(w * scale)), max_height))

def load_and_scale_large(path, max_height=220):
    try: img = pygame.image.load(path).convert_alpha()
    except: img = pygame.image.load(path).convert()
    w, h = img.get_size()
    scale = max_height / float(h)
    return pygame.transform.smoothscale(img, (max(30, int(w * scale)), max_height))

def safe_load(filename, max_height, large=False):
    path = os.path.join(SPRITE_DIR, filename)
    if not os.path.exists(path):
        print(f"ERROR: Missing sprite file: {path}")
        print("Make sure the 'sprites' folder is in the same folder as woke_invaders.py")
        print("Expected files: char1_goth.png, char2_cat.png, char3_red.png, char4_don.png")
        input("Press Enter to exit...")
        sys.exit(1)
    if large:
        return load_and_scale_large(path, max_height)
    return load_and_scale(path, max_height)

char_surfaces = [
    safe_load("char1_goth.png", 100),
    safe_load("char2_cat.png", 100),
    safe_load("char3_red.png", 110),
    safe_load("char4_don.png", 105),
]
char_surfaces_large = [
    safe_load("char1_goth.png", 230, large=True),
    safe_load("char2_cat.png", 230, large=True),
    safe_load("char3_red.png", 250, large=True),
    safe_load("char4_don.png", 240, large=True),
]
char_names = ["DAVINYA", "SHIRO", "RED MIKU", "DON"]
char_colors = [PURPLE, YELLOW, RED, GOLD]
char_abilities = [
    "VOID DRAIN - Freeze all enemies for 3s",
    "POUNCE - Speed boost + triple shot",
    "BARRAGE - Rapid fire mode",
    "INTIMIDATE - Reverse + heavily slow enemies"
]
# Load enemy sprites from images (same folder as characters)
def load_enemy(filename, max_height=40):
    path = os.path.join(SPRITE_DIR, filename)
    if not os.path.exists(path):
        print(f"ERROR: Missing enemy sprite: {path}")
        input("Press Enter to exit...")
        sys.exit(1)
    try:
        img = pygame.image.load(path).convert_alpha()
    except:
        img = pygame.image.load(path).convert()
    w, h = img.get_size()
    scale = max_height / float(h)
    new_w = max(16, int(w * scale))
    return pygame.transform.smoothscale(img, (new_w, max_height))

enemy_a_surf = load_enemy("enemy_a.png", 42)
enemy_b_surf = load_enemy("enemy_b.png", 38)
enemy_c_surf = load_enemy("enemy_c.png", 40)

# Keep simple pixel bullets and explosions (small)
PIXEL_SCALE = 3
def make_surface_from_pixels(pixel_data, scale=PIXEL_SCALE):
    h = len(pixel_data)
    w = len(pixel_data[0]) if h > 0 else 0
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    for y, row in enumerate(pixel_data):
        for x, color in enumerate(row):
            if color is not None:
                pygame.draw.rect(surf, color, (x * scale, y * scale, scale, scale))
    return surf

# Character laser colors: DAVINYA=purple, SHIRO=yellow, RED MIKU=red, DON=gold
CHAR_LASER_COLORS = [PURPLE, YELLOW, RED, GOLD]

def make_colored_bullet(color):
    """Create a small laser bullet surface in the given color."""
    surf = pygame.Surface((6, 16), pygame.SRCALPHA)
    # Core
    pygame.draw.rect(surf, color, (1, 0, 4, 14))
    # Bright tip
    bright = tuple(min(255, c + 80) for c in color)
    pygame.draw.rect(surf, bright, (2, 0, 2, 6))
    # Glow edges
    pygame.draw.rect(surf, color, (0, 2, 6, 10))
    return surf

# Pre-make colored bullets for each character + enemy
player_bullet_surfs = [make_colored_bullet(c) for c in CHAR_LASER_COLORS]
enemy_bullet_surf = make_colored_bullet(HOT_PINK)

EXPLOSION_1 = [[None,None,YELLOW,None,None],[None,ORANGE,WHITE,ORANGE,None],[YELLOW,WHITE,WHITE,WHITE,YELLOW],[None,ORANGE,WHITE,ORANGE,None],[None,None,YELLOW,None,None]]
EXPLOSION_2 = [[None,ORANGE,None,ORANGE,None],[ORANGE,None,YELLOW,None,ORANGE],[None,YELLOW,None,YELLOW,None],[ORANGE,None,YELLOW,None,ORANGE],[None,ORANGE,None,ORANGE,None]]
explosion_surfs = [make_surface_from_pixels(EXPLOSION_1), make_surface_from_pixels(EXPLOSION_2)]

# Power-up definitions
POWERUP_TYPES = {
    "life":   {"color": GREEN,  "label": "+LIFE",   "duration": 0},
    "rapid":  {"color": CYAN,   "label": "RAPID",   "duration": 480},  # 8 sec
    "spread": {"color": YELLOW, "label": "SPREAD",  "duration": 480},
    "shield": {"color": (80,160,255), "label": "SHIELD", "duration": 300},  # 5 sec
    "slow":   {"color": PURPLE, "label": "SLOW",    "duration": 360},  # 6 sec
}

class Player:
    def __init__(self, char_index):
        self.char_index = char_index
        self.image = char_surfaces[char_index]
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 12
        self.base_speed = 6
        self.speed = self.base_speed
        self.lives = 3
        self.cooldown = 0
        self.invincible = 0
        self.ability_cooldown = 0
        self.ability_active = 0
        self.ability_max_cooldown = 420
        self.triple_shot = False
        self.rapid_fire = False
        self.freeze_enemies = False
        self.laser_color = CHAR_LASER_COLORS[char_index]
        self.bullet_surf = player_bullet_surfs[char_index]
        # Power-up timers
        self.powerup_timers = {"rapid": 0, "spread": 0, "shield": 0, "slow": 0}

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.rect.x += self.speed
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.cooldown > 0: self.cooldown -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.ability_cooldown > 0: self.ability_cooldown -= 1
        if self.ability_active > 0:
            self.ability_active -= 1
            if self.ability_active == 0:
                self.speed = self.base_speed
                # Don't fully clear triple/rapid here if power-up is still active
                if self.powerup_timers["spread"] <= 0:
                    self.triple_shot = False
                if self.powerup_timers["rapid"] <= 0:
                    self.rapid_fire = False
                self.freeze_enemies = False
        # Tick down power-up timers
        for k in list(self.powerup_timers.keys()):
            if self.powerup_timers[k] > 0:
                self.powerup_timers[k] -= 1
                if self.powerup_timers[k] == 0:
                    if k == "rapid":
                        self.rapid_fire = False
                    elif k == "spread":
                        self.triple_shot = False
                    elif k == "shield":
                        pass  # invincible handled separately
                    elif k == "slow":
                        pass  # handled in Game

    def can_use_ability(self):
        return self.ability_cooldown == 0 and self.ability_active == 0

    def use_ability(self, game):
        if not self.can_use_ability(): return
        self.ability_cooldown = self.ability_max_cooldown
        self.ability_active = 180
        if self.char_index == 0:
            self.freeze_enemies = True
            game.message = "VOID DRAIN!"; game.message_timer = 70
        elif self.char_index == 1:
            self.speed = self.base_speed + 5
            self.triple_shot = True
            game.message = "POUNCE!"; game.message_timer = 70
        elif self.char_index == 2:
            self.rapid_fire = True
            self.cooldown = 0
            game.message = "BARRAGE!"; game.message_timer = 70
        elif self.char_index == 3:
            game.enemy_direction *= -1
            game.enemy_speed_modifier = 0.25
            game.message = "INTIMIDATE!"; game.message_timer = 70

    def apply_powerup(self, ptype, game):
        if ptype == "life":
            self.lives = min(self.lives + 1, 6)
            game.message = "+1 LIFE!"
            game.message_timer = 60
        elif ptype == "rapid":
            self.rapid_fire = True
            self.powerup_timers["rapid"] = POWERUP_TYPES["rapid"]["duration"]
            game.message = "RAPID FIRE!"
            game.message_timer = 60
        elif ptype == "spread":
            self.triple_shot = True
            self.powerup_timers["spread"] = POWERUP_TYPES["spread"]["duration"]
            game.message = "SPREAD SHOT!"
            game.message_timer = 60
        elif ptype == "shield":
            self.invincible = max(self.invincible, POWERUP_TYPES["shield"]["duration"])
            self.powerup_timers["shield"] = POWERUP_TYPES["shield"]["duration"]
            game.message = "SHIELD!"
            game.message_timer = 60
        elif ptype == "slow":
            game.enemy_speed_modifier = 0.35
            self.powerup_timers["slow"] = POWERUP_TYPES["slow"]["duration"]
            game.message = "SLOW FIELD!"
            game.message_timer = 60

    def shoot(self):
        fire_rate = 6 if self.rapid_fire else 14
        if self.cooldown == 0:
            self.cooldown = fire_rate
            bullets = []
            if self.triple_shot:
                bullets.append(Bullet(self.rect.centerx - 16, self.rect.top, -11, True, self.bullet_surf))
                bullets.append(Bullet(self.rect.centerx, self.rect.top, -11, True, self.bullet_surf))
                bullets.append(Bullet(self.rect.centerx + 16, self.rect.top, -11, True, self.bullet_surf))
            else:
                bullets.append(Bullet(self.rect.centerx, self.rect.top, -11, True, self.bullet_surf))
            return bullets
        return []

    def draw(self, surface):
        if self.invincible == 0 or (self.invincible // 3) % 2 == 0:
            surface.blit(self.image, self.rect)
            # Shield visual
            if self.powerup_timers["shield"] > 0:
                pygame.draw.circle(surface, (80, 160, 255), self.rect.center, max(self.rect.width, self.rect.height)//2 + 8, 2)

class Bullet:
    def __init__(self, x, y, speed, is_player=True, image=None):
        self.is_player = is_player
        self.image = image if image is not None else (player_bullet_surfs[0] if is_player else enemy_bullet_surf)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
    def update(self):
        self.rect.y += self.speed
        return 0 <= self.rect.y <= SCREEN_HEIGHT
    def draw(self, surface): surface.blit(self.image, self.rect)

class PowerUp:
    def __init__(self, x, y, ptype):
        self.type = ptype
        self.color = POWERUP_TYPES[ptype]["color"]
        self.label = POWERUP_TYPES[ptype]["label"]
        self.rect = pygame.Rect(x - 12, y - 12, 24, 24)
        self.speed = 2.2
        self.alive = True
    def update(self):
        self.rect.y += self.speed
        return self.rect.top < SCREEN_HEIGHT
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
        # Small letter
        letter = self.label[0]
        txt = font_tiny.render(letter, True, BLACK)
        surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))


class Enemy:
    def __init__(self, x, y, enemy_type):
        self.type = enemy_type
        if enemy_type == 0: self.image = enemy_a_surf; self.points = 30
        elif enemy_type == 1: self.image = enemy_b_surf; self.points = 20
        else: self.image = enemy_c_surf; self.points = 10
        self.rect = self.image.get_rect(topleft=(x, y))
        self.alive = True
    def draw(self, surface):
        if self.alive: surface.blit(self.image, self.rect)

class Explosion:
    def __init__(self, x, y):
        self.x = x; self.y = y; self.frame = 0; self.max_frames = 8
    def update(self):
        self.frame += 1
        return self.frame < self.max_frames
    def draw(self, surface):
        img = explosion_surfs[min(self.frame // 4, 1)]
        surface.blit(img, img.get_rect(center=(self.x, self.y)))

class Game:
    def __init__(self):
        self.state = "menu"
        self.selected_char = 0
        self.player = None
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.explosions = []
        self.powerups = []
        self.score = 0
        self.level = 1
        self.enemy_direction = 1
        self.enemy_speed_modifier = 1.0
        self.enemy_move_timer = 0
        self.enemy_shoot_timer = 0
        self.high_score = 0
        self.message = ""
        self.message_timer = 0
    def start_game(self):
        self.player = Player(self.selected_char)
        self.score = 0
        self.level = 1
        self.bullets = []
        self.enemy_bullets = []
        self.explosions = []
        self.powerups = []
        self.spawn_enemies()
        self.state = "playing"
        self.enemy_direction = 1
        self.enemy_speed_modifier = 1.0
    def spawn_enemies(self):
        self.enemies = []
        for row in range(5):
            for col in range(10):
                etype = 0 if row < 1 else (1 if row < 3 else 2)
                self.enemies.append(Enemy(60 + col * 65, 50 + row * 48, etype))
    def spawn_powerup(self, x, y):
        # ~18% chance
        if random.random() < 0.18:
            ptype = random.choice(list(POWERUP_TYPES.keys()))
            self.powerups.append(PowerUp(x, y, ptype))
    def update_enemies(self):
        if not any(e.alive for e in self.enemies): return
        if self.player and self.player.freeze_enemies: return
        self.enemy_move_timer += 1
        base_interval = max(7, 28 - self.level * 2)
        move_interval = max(4, int(base_interval / max(0.2, self.enemy_speed_modifier)))
        if self.enemy_move_timer >= move_interval:
            self.enemy_move_timer = 0
            leftmost = min(e.rect.left for e in self.enemies if e.alive)
            rightmost = max(e.rect.right for e in self.enemies if e.alive)
            should_descend = False
            if self.enemy_direction > 0 and rightmost >= SCREEN_WIDTH - 15:
                self.enemy_direction = -1; should_descend = True
            elif self.enemy_direction < 0 and leftmost <= 15:
                self.enemy_direction = 1; should_descend = True
            step = max(4, int(12 * self.enemy_speed_modifier))
            for e in self.enemies:
                if e.alive:
                    if should_descend: e.rect.y += 18
                    else: e.rect.x += self.enemy_direction * step
            for e in self.enemies:
                if e.alive and e.rect.bottom >= self.player.rect.top - 5:
                    self.player.lives = 0; self.state = "gameover"; return
        self.enemy_shoot_timer += 1
        shoot_rate = max(32, 70 - self.level * 4)
        if self.enemy_speed_modifier < 0.5: shoot_rate = int(shoot_rate * 1.9)
        if self.enemy_shoot_timer > shoot_rate:
            self.enemy_shoot_timer = 0
            alive = [e for e in self.enemies if e.alive]
            if alive:
                shooter = random.choice(alive)
                self.enemy_bullets.append(Bullet(shooter.rect.centerx, shooter.rect.bottom, 5, False, enemy_bullet_surf))
        # Slowly recover from slow power-up
        if self.player and self.player.powerup_timers.get("slow", 0) <= 0:
            if self.enemy_speed_modifier < 1.0:
                self.enemy_speed_modifier = min(1.0, self.enemy_speed_modifier + 0.003)
    def update(self, keys):
        if self.state == "playing":
            self.player.update(keys)
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_q]) and self.player.can_use_ability():
                self.player.use_ability(self)
            if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
                self.bullets.extend(self.player.shoot())
            self.bullets = [b for b in self.bullets if b.update()]
            self.enemy_bullets = [b for b in self.enemy_bullets if b.update()]
            # Player bullets vs enemies + chance to drop power-up
            for b in self.bullets[:]:
                for e in self.enemies:
                    if e.alive and b.rect.colliderect(e.rect):
                        e.alive = False
                        self.score += e.points
                        self.explosions.append(Explosion(e.rect.centerx, e.rect.centery))
                        self.spawn_powerup(e.rect.centerx, e.rect.centery)
                        if b in self.bullets: self.bullets.remove(b)
                        break
            # Enemy bullets vs player
            if self.player.invincible == 0:
                for b in self.enemy_bullets[:]:
                    if b.rect.colliderect(self.player.rect):
                        self.player.lives -= 1
                        self.player.invincible = 70
                        self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery))
                        if b in self.enemy_bullets: self.enemy_bullets.remove(b)
                        if self.player.lives <= 0:
                            self.state = "gameover"
                            if self.score > self.high_score: self.high_score = self.score
                        break
            # Power-ups
            self.powerups = [p for p in self.powerups if p.update()]
            for p in self.powerups[:]:
                if p.rect.colliderect(self.player.rect):
                    self.player.apply_powerup(p.type, self)
                    self.powerups.remove(p)
            self.explosions = [ex for ex in self.explosions if ex.update()]
            self.update_enemies()
            if all(not e.alive for e in self.enemies):
                self.level += 1
                self.spawn_enemies()
                self.message = f"LEVEL {self.level}!"
                self.message_timer = 90
                self.bullets.clear()
                self.enemy_bullets.clear()
                self.powerups.clear()
                self.enemy_speed_modifier = 1.0
            if self.message_timer > 0: self.message_timer -= 1

    def draw_menu(self):
        screen.fill(BLACK)
        title = font_large.render("WOKE INVADERS", True, NEON_PINK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 60))
        subtitle = font_med.render("Original Anime Characters Edition", True, PURPLE)
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 115))
        lines = ["Play as DAVINYA, SHIRO, RED MIKU or DON!", "Lasers match your character. Collect power-ups!", "", "MOVE: Arrow Keys / WASD", "SHOOT: Space / W / Up", "ABILITY: Left Shift or Q", "", "Press ENTER to choose your fighter", "Press ESC to quit"]
        for i, line in enumerate(lines):
            color = WHITE if i < 2 else GRAY
            txt = font_small.render(line, True, color)
            screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 175 + i * 28))
        if self.high_score > 0:
            hs = font_small.render(f"HIGH SCORE: {self.high_score}", True, GOLD)
            screen.blit(hs, (SCREEN_WIDTH//2 - hs.get_width()//2, 520))
    def draw_select(self):
        screen.fill(BLACK)
        title = font_med.render("SELECT YOUR CHARACTER", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 15))
        large = char_surfaces_large[self.selected_char]
        rect = large.get_rect(center=(SCREEN_WIDTH // 2, 250))
        pygame.draw.rect(screen, char_colors[self.selected_char], rect.inflate(16, 16), 3)
        screen.blit(large, rect)
        name = font_med.render(char_names[self.selected_char], True, char_colors[self.selected_char])
        screen.blit(name, (SCREEN_WIDTH//2 - name.get_width()//2, 400))
        ab = font_tiny.render(char_abilities[self.selected_char], True, char_colors[self.selected_char])
        screen.blit(ab, (SCREEN_WIDTH//2 - ab.get_width()//2, 435))
        for i in range(4):
            preview = pygame.transform.smoothscale(char_surfaces[i], (50, 55))
            px = 180 + i * 120
            py = 490
            if i == self.selected_char: pygame.draw.rect(screen, char_colors[i], (px-4, py-4, 58, 63), 2)
            screen.blit(preview, (px, py))
        hint = font_tiny.render("LEFT / RIGHT to change   |   ENTER to start   |   ESC back", True, GRAY)
        screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 565))
    def draw_playing(self):
        screen.fill(BLACK)
        for i in range(40):
            x = (i * 97 + pygame.time.get_ticks() // 45) % SCREEN_WIDTH
            y = (i * 53) % SCREEN_HEIGHT
            brightness = 70 + (i * 41) % 160
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)
        for e in self.enemies: e.draw(screen)
        self.player.draw(screen)
        for b in self.bullets: b.draw(screen)
        for b in self.enemy_bullets: b.draw(screen)
        for p in self.powerups: p.draw(screen)
        for ex in self.explosions: ex.draw(screen)
        # HUD
        score_txt = font_small.render(f"SCORE: {self.score}", True, WHITE)
        screen.blit(score_txt, (12, 6))
        level_txt = font_small.render(f"LEVEL: {self.level}", True, CYAN)
        screen.blit(level_txt, (12, 30))
        lives_txt = font_small.render(f"LIVES: {self.player.lives}", True, RED)
        screen.blit(lives_txt, (SCREEN_WIDTH - 125, 6))
        char_txt = font_tiny.render(char_names[self.player.char_index], True, char_colors[self.player.char_index])
        screen.blit(char_txt, (SCREEN_WIDTH - 125, 30))
        # Ability status
        if self.player.can_use_ability():
            ab_txt = font_tiny.render("ABILITY READY [SHIFT/Q]", True, GREEN)
        elif self.player.ability_active > 0:
            ab_txt = font_tiny.render("ABILITY ACTIVE!", True, YELLOW)
        else:
            secs = max(1, self.player.ability_cooldown // 60)
            ab_txt = font_tiny.render(f"Ability CD: {secs}s", True, GRAY)
        screen.blit(ab_txt, (SCREEN_WIDTH // 2 - ab_txt.get_width() // 2, 6))
        # Active power-up indicators
        active = []
        if self.player.powerup_timers.get("rapid", 0) > 0: active.append(("RAPID", CYAN))
        if self.player.powerup_timers.get("spread", 0) > 0: active.append(("SPREAD", YELLOW))
        if self.player.powerup_timers.get("shield", 0) > 0: active.append(("SHIELD", (80,160,255)))
        if self.player.powerup_timers.get("slow", 0) > 0: active.append(("SLOW", PURPLE))
        for i, (name, col) in enumerate(active):
            t = font_tiny.render(name, True, col)
            screen.blit(t, (12, 55 + i * 18))
        if self.message_timer > 0:
            msg = font_med.render(self.message, True, YELLOW)
            screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, SCREEN_HEIGHT//2 - 40))

    def draw_gameover(self):
        screen.fill(BLACK)
        title = font_large.render("GAME OVER", True, RED)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 140))
        score = font_med.render(f"Final Score: {self.score}", True, WHITE)
        screen.blit(score, (SCREEN_WIDTH//2 - score.get_width()//2, 230))
        if self.score >= self.high_score and self.score > 0:
            hs = font_small.render("NEW HIGH SCORE!", True, GOLD)
            screen.blit(hs, (SCREEN_WIDTH//2 - hs.get_width()//2, 290))
        else:
            hs = font_small.render(f"High Score: {self.high_score}", True, GRAY)
            screen.blit(hs, (SCREEN_WIDTH//2 - hs.get_width()//2, 290))
        again = font_small.render("ENTER = play again    |    ESC = menu", True, WHITE)
        screen.blit(again, (SCREEN_WIDTH//2 - again.get_width()//2, 400))
    def draw(self):
        if self.state == "menu": self.draw_menu()
        elif self.state == "select": self.draw_select()
        elif self.state == "playing": self.draw_playing()
        elif self.state == "gameover": self.draw_gameover()
        pygame.display.flip()

def main():
    game = Game()
    running = True
    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state in ("playing", "gameover"): game.state = "menu"
                    elif game.state == "select": game.state = "menu"
                    else: running = False
                if event.key == pygame.K_RETURN:
                    if game.state == "menu": game.state = "select"
                    elif game.state == "select": game.start_game()
                    elif game.state == "gameover": game.start_game()
                if game.state == "select":
                    if event.key in (pygame.K_LEFT, pygame.K_a): game.selected_char = (game.selected_char - 1) % 4
                    if event.key in (pygame.K_RIGHT, pygame.K_d): game.selected_char = (game.selected_char + 1) % 4
        game.update(keys)
        game.draw()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

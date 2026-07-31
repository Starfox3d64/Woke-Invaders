#!/usr/bin/env python3
"""
Woke Invaders - Full Edition
DAVINYA / SHIRO / RED MIKU / DON
Difficulty modes, power-ups, colored lasers, combos, pause, high scores, SFX
"""
import pygame, random, sys, os, json, math
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except Exception:
    pass

SCREEN_WIDTH, SCREEN_HEIGHT, FPS = 800, 600, 60
BLACK, WHITE, PURPLE, PINK, HOT_PINK = (0,0,0), (255,255,255), (160,40,200), (255,105,180), (255,20,147)
RED, CYAN, GREEN, YELLOW, ORANGE = (220,30,40), (0,220,230), (40,200,60), (255,230,40), (255,140,20)
GRAY, GOLD, BLUE_HAIR, NEON_PINK = (90,90,90), (255,200,40), (60,120,255), (255,20,147)
DARK = (25, 25, 35)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WOKE INVADERS")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("Courier", 42, bold=True)
font_med = pygame.font.SysFont("Courier", 24, bold=True)
font_small = pygame.font.SysFont("Courier", 18)
font_tiny = pygame.font.SysFont("Courier", 14)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(SCRIPT_DIR, "sprites")
HIGHSCORE_FILE = os.path.join(SCRIPT_DIR, "highscores.json")

DIFFICULTIES = {
    "EASY":   {"lives": 5, "enemy_speed": 0.75, "shoot_mult": 1.35, "drop_rate": 0.28, "rows": 4, "cols": 8},
    "NORMAL": {"lives": 3, "enemy_speed": 1.0,  "shoot_mult": 1.0,  "drop_rate": 0.18, "rows": 5, "cols": 10},
    "HARD":   {"lives": 2, "enemy_speed": 1.4,  "shoot_mult": 0.7,  "drop_rate": 0.11, "rows": 6, "cols": 11},
}

def load_highscores():
    try:
        with open(HIGHSCORE_FILE) as f: return json.load(f)
    except: return {"EASY": 0, "NORMAL": 0, "HARD": 0}

def save_highscores(data):
    try:
        with open(HIGHSCORE_FILE, "w") as f: json.dump(data, f)
    except: pass

def create_tone(freq, ms=50, vol=0.2):
    try:
        import array
        sr = 22050
        n = int(sr * ms / 1000)
        buf = array.array("h", [int(vol * 32767 * math.sin(2 * math.pi * freq * i / sr)) for i in range(n)])
        return pygame.mixer.Sound(buffer=buf)
    except: return None

snd_shoot = create_tone(900, 35, 0.12)
snd_hit = create_tone(280, 70, 0.22)
snd_power = create_tone(700, 100, 0.25)
snd_hurt = create_tone(150, 120, 0.28)
snd_select = create_tone(550, 40, 0.18)

def play(s):
    if s:
        try: s.play()
        except: pass

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
        print("ERROR: Missing sprite:", path)
        print("Keep the sprites folder next to woke_invaders.py")
        input("Press Enter to exit...")
        sys.exit(1)
    return load_and_scale_large(path, max_height) if large else load_and_scale(path, max_height)

char_surfaces = [safe_load("char1_goth.png", 100), safe_load("char2_cat.png", 100),
                 safe_load("char3_red.png", 110), safe_load("char4_don.png", 105)]
char_surfaces_large = [safe_load("char1_goth.png", 230, True), safe_load("char2_cat.png", 230, True),
                       safe_load("char3_red.png", 250, True), safe_load("char4_don.png", 240, True)]
char_names = ["DAVINYA", "SHIRO", "RED MIKU", "DON"]
char_colors = [PURPLE, YELLOW, RED, GOLD]
char_abilities = ["VOID DRAIN - Freeze enemies", "POUNCE - Speed + triple shot",
                  "BARRAGE - Rapid fire", "INTIMIDATE - Reverse & slow"]

def load_enemy(filename, max_height=40):
    path = os.path.join(SPRITE_DIR, filename)
    if not os.path.exists(path):
        print("ERROR: Missing", path); input(); sys.exit(1)
    try: img = pygame.image.load(path).convert_alpha()
    except: img = pygame.image.load(path).convert()
    w, h = img.get_size()
    scale = max_height / float(h)
    return pygame.transform.smoothscale(img, (max(16, int(w * scale)), max_height))

enemy_a_surf = load_enemy("enemy_a.png", 42)
enemy_b_surf = load_enemy("enemy_b.png", 38)
enemy_c_surf = load_enemy("enemy_c.png", 40)

CHAR_LASER_COLORS = [PURPLE, YELLOW, RED, GOLD]
def make_colored_bullet(color):
    surf = pygame.Surface((6, 16), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (1, 0, 4, 14))
    bright = tuple(min(255, c + 90) for c in color)
    pygame.draw.rect(surf, bright, (2, 0, 2, 6))
    pygame.draw.rect(surf, color, (0, 2, 6, 10))
    return surf
player_bullet_surfs = [make_colored_bullet(c) for c in CHAR_LASER_COLORS]
enemy_bullet_surf = make_colored_bullet(HOT_PINK)

PIXEL_SCALE = 3
def make_surface_from_pixels(pixel_data, scale=PIXEL_SCALE):
    h = len(pixel_data); w = len(pixel_data[0]) if h else 0
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    for y, row in enumerate(pixel_data):
        for x, color in enumerate(row):
            if color is not None:
                pygame.draw.rect(surf, color, (x * scale, y * scale, scale, scale))
    return surf
EXPLOSION_1 = [[None,None,YELLOW,None,None],[None,ORANGE,WHITE,ORANGE,None],[YELLOW,WHITE,WHITE,WHITE,YELLOW],[None,ORANGE,WHITE,ORANGE,None],[None,None,YELLOW,None,None]]
EXPLOSION_2 = [[None,ORANGE,None,ORANGE,None],[ORANGE,None,YELLOW,None,ORANGE],[None,YELLOW,None,YELLOW,None],[ORANGE,None,YELLOW,None,ORANGE],[None,ORANGE,None,ORANGE,None]]
explosion_surfs = [make_surface_from_pixels(EXPLOSION_1), make_surface_from_pixels(EXPLOSION_2)]

POWERUP_TYPES = {
    "life":   {"color": GREEN, "label": "+LIFE", "duration": 0},
    "rapid":  {"color": CYAN, "label": "RAPID", "duration": 480},
    "spread": {"color": YELLOW, "label": "SPREAD", "duration": 480},
    "shield": {"color": (80,160,255), "label": "SHIELD", "duration": 300},
    "slow":   {"color": PURPLE, "label": "SLOW", "duration": 360},
}

class Player:
    def __init__(self, char_index, difficulty):
        self.char_index = char_index
        self.image = char_surfaces[char_index]
        self.rect = self.image.get_rect(centerx=SCREEN_WIDTH//2, bottom=SCREEN_HEIGHT-12)
        self.base_speed = 6
        self.speed = 6
        self.lives = DIFFICULTIES[difficulty]["lives"]
        self.cooldown = 0
        self.invincible = 0
        self.ability_cooldown = 0
        self.ability_active = 0
        self.ability_max_cooldown = 420
        self.triple_shot = False
        self.rapid_fire = False
        self.freeze_enemies = False
        self.bullet_surf = player_bullet_surfs[char_index]
        self.powerup_timers = {"rapid":0,"spread":0,"shield":0,"slow":0}
        self.combo = 0
        self.combo_timer = 0
    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.rect.x += self.speed
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.cooldown > 0: self.cooldown -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.ability_cooldown > 0: self.ability_cooldown -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0: self.combo = 0
        if self.ability_active > 0:
            self.ability_active -= 1
            if self.ability_active == 0:
                self.speed = self.base_speed
                if self.powerup_timers["spread"] <= 0: self.triple_shot = False
                if self.powerup_timers["rapid"] <= 0: self.rapid_fire = False
                self.freeze_enemies = False
        for k in list(self.powerup_timers):
            if self.powerup_timers[k] > 0:
                self.powerup_timers[k] -= 1
                if self.powerup_timers[k] == 0:
                    if k == "rapid": self.rapid_fire = False
                    elif k == "spread": self.triple_shot = False
    def can_use_ability(self):
        return self.ability_cooldown == 0 and self.ability_active == 0
    def use_ability(self, game):
        if not self.can_use_ability(): return
        self.ability_cooldown = self.ability_max_cooldown
        self.ability_active = 180
        play(snd_power)
        if self.char_index == 0:
            self.freeze_enemies = True; game.message = "VOID DRAIN!"; game.message_timer = 70
        elif self.char_index == 1:
            self.speed = self.base_speed + 5; self.triple_shot = True
            game.message = "POUNCE!"; game.message_timer = 70
        elif self.char_index == 2:
            self.rapid_fire = True; self.cooldown = 0
            game.message = "BARRAGE!"; game.message_timer = 70
        else:
            game.enemy_direction *= -1; game.enemy_speed_modifier = 0.25
            game.message = "INTIMIDATE!"; game.message_timer = 70
    def apply_powerup(self, ptype, game):
        play(snd_power)
        if ptype == "life":
            self.lives = min(self.lives + 1, 8); game.message = "+1 LIFE!"
        elif ptype == "rapid":
            self.rapid_fire = True; self.powerup_timers["rapid"] = 480; game.message = "RAPID FIRE!"
        elif ptype == "spread":
            self.triple_shot = True; self.powerup_timers["spread"] = 480; game.message = "SPREAD SHOT!"
        elif ptype == "shield":
            self.invincible = max(self.invincible, 300); self.powerup_timers["shield"] = 300; game.message = "SHIELD!"
        elif ptype == "slow":
            game.enemy_speed_modifier = 0.35; self.powerup_timers["slow"] = 360; game.message = "SLOW FIELD!"
        game.message_timer = 55
    def shoot(self):
        rate = 6 if self.rapid_fire else 13
        if self.cooldown == 0:
            self.cooldown = rate
            play(snd_shoot)
            if self.triple_shot:
                return [Bullet(self.rect.centerx-16, self.rect.top, -11, True, self.bullet_surf),
                        Bullet(self.rect.centerx, self.rect.top, -11, True, self.bullet_surf),
                        Bullet(self.rect.centerx+16, self.rect.top, -11, True, self.bullet_surf)]
            return [Bullet(self.rect.centerx, self.rect.top, -11, True, self.bullet_surf)]
        return []
    def draw(self, surface):
        if self.invincible == 0 or (self.invincible // 3) % 2 == 0:
            surface.blit(self.image, self.rect)
            if self.powerup_timers["shield"] > 0:
                pygame.draw.circle(surface, (80,160,255), self.rect.center, max(self.rect.w, self.rect.h)//2 + 8, 2)

class Bullet:
    def __init__(self, x, y, speed, is_player=True, image=None):
        self.is_player = is_player
        self.image = image if image else player_bullet_surfs[0]
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
        self.rect = pygame.Rect(x-12, y-12, 24, 24)
        self.speed = 2.3
    def update(self):
        self.rect.y += self.speed
        return self.rect.top < SCREEN_HEIGHT
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
        t = font_tiny.render(self.label[0], True, BLACK)
        surface.blit(t, (self.rect.centerx - t.get_width()//2, self.rect.centery - t.get_height()//2))

class Enemy:
    def __init__(self, x, y, etype):
        self.type = etype
        if etype == 0: self.image = enemy_a_surf; self.points = 30
        elif etype == 1: self.image = enemy_b_surf; self.points = 20
        else: self.image = enemy_c_surf; self.points = 10
        self.rect = self.image.get_rect(topleft=(x, y))
        self.alive = True
    def draw(self, surface):
        if self.alive: surface.blit(self.image, self.rect)

class Explosion:
    def __init__(self, x, y):
        self.x = x; self.y = y; self.frame = 0
    def update(self):
        self.frame += 1
        return self.frame < 8
    def draw(self, surface):
        img = explosion_surfs[min(self.frame // 4, 1)]
        surface.blit(img, img.get_rect(center=(self.x, self.y)))

class FloatingText:
    def __init__(self, x, y, text, color=YELLOW):
        self.x = x; self.y = y; self.text = text; self.color = color; self.life = 40
    def update(self):
        self.y -= 1.2; self.life -= 1
        return self.life > 0
    def draw(self, surface):
        t = font_tiny.render(self.text, True, self.color)
        surface.blit(t, (self.x - t.get_width()//2, self.y))

class Game:
    def __init__(self):
        self.state = "menu"
        self.selected_char = 0
        self.difficulty = "NORMAL"
        self.diff_index = 1
        self.player = None
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.explosions = []
        self.powerups = []
        self.float_texts = []
        self.score = 0
        self.level = 1
        self.enemy_direction = 1
        self.enemy_speed_modifier = 1.0
        self.enemy_move_timer = 0
        self.enemy_shoot_timer = 0
        self.highscores = load_highscores()
        self.message = ""
        self.message_timer = 0
        self.shake = 0
    def start_game(self):
        self.player = Player(self.selected_char, self.difficulty)
        self.score = 0; self.level = 1
        self.bullets = []; self.enemy_bullets = []; self.explosions = []
        self.powerups = []; self.float_texts = []
        self.spawn_enemies()
        self.state = "playing"
        self.enemy_direction = 1; self.enemy_speed_modifier = 1.0; self.shake = 0
    def spawn_enemies(self):
        self.enemies = []
        cfg = DIFFICULTIES[self.difficulty]
        rows, cols = cfg["rows"], cfg["cols"]
        spacing_x = 62 if cols <= 10 else 54
        start_x = max(20, (SCREEN_WIDTH - cols * spacing_x) // 2)
        for row in range(rows):
            for col in range(cols):
                etype = 0 if row < 1 else (1 if row < 3 else 2)
                self.enemies.append(Enemy(start_x + col * spacing_x, 45 + row * 46, etype))
    def spawn_powerup(self, x, y):
        if random.random() < DIFFICULTIES[self.difficulty]["drop_rate"]:
            self.powerups.append(PowerUp(x, y, random.choice(list(POWERUP_TYPES.keys()))))
    def update_enemies(self):
        if not any(e.alive for e in self.enemies): return
        if self.player and self.player.freeze_enemies: return
        cfg = DIFFICULTIES[self.difficulty]
        self.enemy_move_timer += 1
        base = max(5, int(24 / cfg["enemy_speed"]) - self.level)
        interval = max(3, int(base / max(0.2, self.enemy_speed_modifier)))
        if self.enemy_move_timer >= interval:
            self.enemy_move_timer = 0
            left = min(e.rect.left for e in self.enemies if e.alive)
            right = max(e.rect.right for e in self.enemies if e.alive)
            descend = False
            if self.enemy_direction > 0 and right >= SCREEN_WIDTH - 12:
                self.enemy_direction = -1; descend = True
            elif self.enemy_direction < 0 and left <= 12:
                self.enemy_direction = 1; descend = True
            step = max(3, int(10 * self.enemy_speed_modifier * cfg["enemy_speed"]))
            for e in self.enemies:
                if e.alive:
                    if descend: e.rect.y += 15
                    else: e.rect.x += self.enemy_direction * step
            for e in self.enemies:
                if e.alive and e.rect.bottom >= self.player.rect.top - 4:
                    self.player.lives = 0; self.state = "gameover"; return
        self.enemy_shoot_timer += 1
        rate = max(26, int(60 * cfg["shoot_mult"]) - self.level * 3)
        if self.enemy_speed_modifier < 0.5: rate = int(rate * 1.8)
        if self.enemy_shoot_timer > rate:
            self.enemy_shoot_timer = 0
            alive = [e for e in self.enemies if e.alive]
            if alive:
                s = random.choice(alive)
                self.enemy_bullets.append(Bullet(s.rect.centerx, s.rect.bottom, 5, False, enemy_bullet_surf))
        if self.player and self.player.powerup_timers.get("slow", 0) <= 0:
            if self.enemy_speed_modifier < 1.0:
                self.enemy_speed_modifier = min(1.0, self.enemy_speed_modifier + 0.003)
    def update(self, keys):
        if self.state != "playing": return
        if self.shake > 0: self.shake -= 1
        self.player.update(keys)
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_q]) and self.player.can_use_ability():
            self.player.use_ability(self)
        if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
            self.bullets.extend(self.player.shoot())
        self.bullets = [b for b in self.bullets if b.update()]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.update()]
        for b in self.bullets[:]:
            for e in self.enemies:
                if e.alive and b.rect.colliderect(e.rect):
                    e.alive = False
                    self.player.combo += 1
                    self.player.combo_timer = 90
                    mult = 1 + min(self.player.combo // 5, 4)
                    pts = e.points * mult
                    self.score += pts
                    self.explosions.append(Explosion(e.rect.centerx, e.rect.centery))
                    self.float_texts.append(FloatingText(e.rect.centerx, e.rect.centery-8, f"+{pts}", ORANGE if mult > 1 else YELLOW))
                    self.spawn_powerup(e.rect.centerx, e.rect.centery)
                    play(snd_hit)
                    if b in self.bullets: self.bullets.remove(b)
                    break
        if self.player.invincible == 0:
            for b in self.enemy_bullets[:]:
                if b.rect.colliderect(self.player.rect):
                    self.player.lives -= 1
                    self.player.invincible = 80
                    self.player.combo = 0
                    self.shake = 12
                    self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery))
                    play(snd_hurt)
                    if b in self.enemy_bullets: self.enemy_bullets.remove(b)
                    if self.player.lives <= 0:
                        self.state = "gameover"
                        if self.score > self.highscores.get(self.difficulty, 0):
                            self.highscores[self.difficulty] = self.score
                            save_highscores(self.highscores)
                    break
        self.powerups = [p for p in self.powerups if p.update()]
        for p in self.powerups[:]:
            if p.rect.colliderect(self.player.rect):
                self.player.apply_powerup(p.type, self)
                self.powerups.remove(p)
        self.explosions = [ex for ex in self.explosions if ex.update()]
        self.float_texts = [ft for ft in self.float_texts if ft.update()]
        self.update_enemies()
        if all(not e.alive for e in self.enemies):
            self.level += 1
            self.spawn_enemies()
            self.message = f"LEVEL {self.level}!"
            self.message_timer = 80
            self.bullets.clear(); self.enemy_bullets.clear(); self.powerups.clear()
            self.enemy_speed_modifier = 1.0
        if self.message_timer > 0: self.message_timer -= 1

    def draw_menu(self):
        screen.fill(BLACK)
        t = font_large.render("WOKE INVADERS", True, NEON_PINK)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 60))
        s = font_med.render("Defend reality. Collect power-ups.", True, PURPLE)
        screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 120))
        lines = ["Difficulty modes  •  Combos  •  High scores", "Colored lasers  •  Character abilities", "", "ENTER - Start", "ESC - Quit"]
        for i, line in enumerate(lines):
            c = WHITE if i < 2 else GRAY
            tt = font_small.render(line, True, c)
            screen.blit(tt, (SCREEN_WIDTH//2 - tt.get_width()//2, 190 + i*28))
        y = 370
        for d in ["EASY", "NORMAL", "HARD"]:
            hs = self.highscores.get(d, 0)
            tt = font_tiny.render(f"{d}: {hs}", True, GOLD if hs else GRAY)
            screen.blit(tt, (SCREEN_WIDTH//2 - tt.get_width()//2, y)); y += 22

    def draw_difficulty(self):
        screen.fill(BLACK)
        t = font_med.render("SELECT DIFFICULTY", True, WHITE)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 80))
        diffs = list(DIFFICULTIES.keys())
        for i, d in enumerate(diffs):
            col = GOLD if i == self.diff_index else GRAY
            lab = font_med.render(d, True, col)
            screen.blit(lab, (SCREEN_WIDTH//2 - lab.get_width()//2, 170 + i*60))
            cfg = DIFFICULTIES[d]
            desc = font_tiny.render(f"Lives {cfg['lives']}  |  Enemy speed {cfg['enemy_speed']}x", True, GRAY)
            screen.blit(desc, (SCREEN_WIDTH//2 - desc.get_width()//2, 200 + i*60))
        h = font_small.render("UP/DOWN  •  ENTER confirm  •  ESC back", True, GRAY)
        screen.blit(h, (SCREEN_WIDTH//2 - h.get_width()//2, 520))

    def draw_select(self):
        screen.fill(BLACK)
        t = font_med.render("SELECT CHARACTER", True, WHITE)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 12))
        large = char_surfaces_large[self.selected_char]
        rect = large.get_rect(center=(SCREEN_WIDTH//2, 235))
        pygame.draw.rect(screen, char_colors[self.selected_char], rect.inflate(14, 14), 3)
        screen.blit(large, rect)
        name = font_med.render(char_names[self.selected_char], True, char_colors[self.selected_char])
        screen.blit(name, (SCREEN_WIDTH//2 - name.get_width()//2, 385))
        ab = font_tiny.render(char_abilities[self.selected_char], True, char_colors[self.selected_char])
        screen.blit(ab, (SCREEN_WIDTH//2 - ab.get_width()//2, 420))
        for i in range(4):
            prev = pygame.transform.smoothscale(char_surfaces[i], (48, 52))
            px = 190 + i * 110; py = 475
            if i == self.selected_char:
                pygame.draw.rect(screen, char_colors[i], (px-3, py-3, 54, 58), 2)
            screen.blit(prev, (px, py))
        h = font_tiny.render("LEFT/RIGHT  •  ENTER start  •  ESC back", True, GRAY)
        screen.blit(h, (SCREEN_WIDTH//2 - h.get_width()//2, 555))

    def draw_playing(self):
        ox = random.randint(-self.shake, self.shake) if self.shake else 0
        oy = random.randint(-self.shake, self.shake) if self.shake else 0
        screen.fill(BLACK)
        for i in range(40):
            x = (i * 97 + pygame.time.get_ticks() // 45) % SCREEN_WIDTH
            y = (i * 53) % SCREEN_HEIGHT
            b = 70 + (i * 41) % 160
            pygame.draw.circle(screen, (b, b, b), (x + ox, y + oy), 1)
        for e in self.enemies:
            if e.alive: screen.blit(e.image, (e.rect.x + ox, e.rect.y + oy))
        self.player.draw(screen)
        for b in self.bullets: screen.blit(b.image, (b.rect.x + ox, b.rect.y + oy))
        for b in self.enemy_bullets: screen.blit(b.image, (b.rect.x + ox, b.rect.y + oy))
        for p in self.powerups: p.draw(screen)
        for ex in self.explosions: ex.draw(screen)
        for ft in self.float_texts: ft.draw(screen)
        screen.blit(font_small.render(f"SCORE: {self.score}", True, WHITE), (12, 6))
        screen.blit(font_small.render(f"LVL {self.level}", True, CYAN), (12, 28))
        screen.blit(font_small.render(f"LIVES: {self.player.lives}", True, RED), (SCREEN_WIDTH-125, 6))
        screen.blit(font_tiny.render(char_names[self.player.char_index], True, char_colors[self.player.char_index]), (SCREEN_WIDTH-125, 28))
        if self.player.combo >= 3:
            c = font_small.render(f"COMBO x{1+min(self.player.combo//5,4)}", True, ORANGE)
            screen.blit(c, (SCREEN_WIDTH//2 - c.get_width()//2, 28))
        if self.player.can_use_ability():
            ab = font_tiny.render("ABILITY READY [SHIFT/Q]", True, GREEN)
        elif self.player.ability_active > 0:
            ab = font_tiny.render("ABILITY ACTIVE!", True, YELLOW)
        else:
            ab = font_tiny.render(f"Ability {max(1,self.player.ability_cooldown//60)}s", True, GRAY)
        screen.blit(ab, (SCREEN_WIDTH//2 - ab.get_width()//2, 6))
        # cooldown bar
        bw = 120
        filled = 0 if self.player.can_use_ability() else int(bw * (1 - self.player.ability_cooldown / self.player.ability_max_cooldown))
        pygame.draw.rect(screen, DARK, (SCREEN_WIDTH//2 - bw//2, 24, bw, 5))
        pygame.draw.rect(screen, char_colors[self.player.char_index], (SCREEN_WIDTH//2 - bw//2, 24, filled, 5))
        active = []
        if self.player.powerup_timers.get("rapid",0) > 0: active.append(("RAPID", CYAN))
        if self.player.powerup_timers.get("spread",0) > 0: active.append(("SPREAD", YELLOW))
        if self.player.powerup_timers.get("shield",0) > 0: active.append(("SHIELD", (80,160,255)))
        if self.player.powerup_timers.get("slow",0) > 0: active.append(("SLOW", PURPLE))
        for i,(n,c) in enumerate(active):
            screen.blit(font_tiny.render(n, True, c), (12, 52 + i*16))
        if self.message_timer > 0:
            m = font_med.render(self.message, True, YELLOW)
            screen.blit(m, (SCREEN_WIDTH//2 - m.get_width()//2, SCREEN_HEIGHT//2 - 40))

    def draw_paused(self):
        self.draw_playing()
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))
        t = font_large.render("PAUSED", True, WHITE)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 220))
        h = font_small.render("P or ESC = Resume    Q = Quit to Menu", True, GRAY)
        screen.blit(h, (SCREEN_WIDTH//2 - h.get_width()//2, 300))

    def draw_gameover(self):
        screen.fill(BLACK)
        t = font_large.render("GAME OVER", True, RED)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 110))
        screen.blit(font_med.render(f"Score: {self.score}", True, WHITE), (SCREEN_WIDTH//2 - 80, 200))
        screen.blit(font_small.render(f"Difficulty: {self.difficulty}", True, GRAY), (SCREEN_WIDTH//2 - 70, 245))
        hs = self.highscores.get(self.difficulty, 0)
        if self.score >= hs and self.score > 0:
            screen.blit(font_small.render("NEW HIGH SCORE!", True, GOLD), (SCREEN_WIDTH//2 - 80, 290))
        else:
            screen.blit(font_small.render(f"High Score: {hs}", True, GRAY), (SCREEN_WIDTH//2 - 70, 290))
        screen.blit(font_small.render("ENTER = Play Again    ESC = Menu", True, WHITE), (SCREEN_WIDTH//2 - 150, 380))

    def draw(self):
        if self.state == "menu": self.draw_menu()
        elif self.state == "difficulty": self.draw_difficulty()
        elif self.state == "select": self.draw_select()
        elif self.state == "playing": self.draw_playing()
        elif self.state == "paused": self.draw_paused()
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
                    if game.state == "playing": game.state = "paused"
                    elif game.state == "paused": game.state = "playing"
                    elif game.state in ("difficulty", "select", "gameover"): game.state = "menu"
                    else: running = False
                if event.key == pygame.K_p and game.state in ("playing", "paused"):
                    game.state = "paused" if game.state == "playing" else "playing"
                if event.key == pygame.K_q and game.state == "paused":
                    game.state = "menu"
                if event.key == pygame.K_RETURN:
                    if game.state == "menu":
                        game.state = "difficulty"; play(snd_select)
                    elif game.state == "difficulty":
                        game.difficulty = list(DIFFICULTIES.keys())[game.diff_index]
                        game.state = "select"; play(snd_select)
                    elif game.state == "select":
                        game.start_game(); play(snd_select)
                    elif game.state == "gameover":
                        game.start_game()
                if game.state == "difficulty":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        game.diff_index = (game.diff_index - 1) % 3; play(snd_select)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        game.diff_index = (game.diff_index + 1) % 3; play(snd_select)
                if game.state == "select":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        game.selected_char = (game.selected_char - 1) % 4; play(snd_select)
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        game.selected_char = (game.selected_char + 1) % 4; play(snd_select)
        if game.state == "playing":
            game.update(keys)
        game.draw()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

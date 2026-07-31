#!/usr/bin/env python3
"""
Woke Invaders - Combat Expanded Edition
DAVINYA / SHIRO / RED MIKU / DON

New systems:
- Parry / Reflector Shield (E or F)
- Overheat + EMP Vent (hold fire, release at high heat)
- Screen-edge Warp (Pac-Man style)
- Splitter enemies
- Bullet-Time (R or Shift+R)
- Stronger combos, floating debris, better feedback
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
BLUE = (60, 140, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WOKE INVADERS - Combat Edition")
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
snd_parry = create_tone(1200, 60, 0.3)
snd_emp = create_tone(180, 200, 0.35)
snd_slow = create_tone(400, 80, 0.2)

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

# Make a slightly bigger splitter sprite by scaling
splitter_surf = pygame.transform.smoothscale(enemy_a_surf, (int(enemy_a_surf.get_width()*1.35), int(enemy_a_surf.get_height()*1.35)))

CHAR_LASER_COLORS = [PURPLE, YELLOW, RED, GOLD]
def make_colored_bullet(color, w=6, h=16):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (1, 0, w-2, h-2))
    bright = tuple(min(255, c + 90) for c in color)
    pygame.draw.rect(surf, bright, (2, 0, w-4, h//3))
    return surf
player_bullet_surfs = [make_colored_bullet(c) for c in CHAR_LASER_COLORS]
enemy_bullet_surf = make_colored_bullet(HOT_PINK)
reflected_bullet_surf = make_colored_bullet(CYAN, 5, 14)

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
        # New combat systems
        self.heat = 0.0          # 0-100
        self.overheating = False
        self.parry_cooldown = 0
        self.parry_active = 0    # frames the reflector is up
        self.bullet_time = 100.0 # energy 0-100
        self.bullet_time_active = 0
        self.holding_fire = False

    def update(self, keys, time_scale=1.0):
        # Movement with wrap
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.speed
        self.rect.x += int(dx * time_scale)
        # Screen-edge warp (Pac-Man style)
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH:
            self.rect.right = 0

        if self.cooldown > 0: self.cooldown = max(0, self.cooldown - time_scale)
        if self.invincible > 0: self.invincible = max(0, self.invincible - time_scale)
        if self.ability_cooldown > 0: self.ability_cooldown = max(0, self.ability_cooldown - time_scale)
        if self.parry_cooldown > 0: self.parry_cooldown = max(0, self.parry_cooldown - time_scale)
        if self.parry_active > 0: self.parry_active = max(0, self.parry_active - time_scale)
        if self.combo_timer > 0:
            self.combo_timer = max(0, self.combo_timer - time_scale)
            if self.combo_timer <= 0: self.combo = 0
        if self.ability_active > 0:
            self.ability_active = max(0, self.ability_active - time_scale)
            if self.ability_active <= 0:
                self.speed = self.base_speed
                if self.powerup_timers["spread"] <= 0: self.triple_shot = False
                if self.powerup_timers["rapid"] <= 0: self.rapid_fire = False
                self.freeze_enemies = False
        for k in list(self.powerup_timers):
            if self.powerup_timers[k] > 0:
                self.powerup_timers[k] = max(0, self.powerup_timers[k] - time_scale)
                if self.powerup_timers[k] <= 0:
                    if k == "rapid": self.rapid_fire = False
                    elif k == "spread": self.triple_shot = False

        # Bullet time energy regen
        if self.bullet_time_active > 0:
            self.bullet_time_active = max(0, self.bullet_time_active - 1)
            self.bullet_time = max(0, self.bullet_time - 0.9)
        else:
            self.bullet_time = min(100, self.bullet_time + 0.12)

        # Overheat build while holding fire
        if self.holding_fire and not self.overheating:
            self.heat = min(100, self.heat + 0.55 * time_scale)
            if self.heat >= 100:
                self.overheating = True
        else:
            if not self.holding_fire:
                self.heat = max(0, self.heat - 0.8 * time_scale)
                if self.heat < 30:
                    self.overheating = False

    def can_use_ability(self):
        return self.ability_cooldown <= 0 and self.ability_active <= 0

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

    def try_parry(self):
        if self.parry_cooldown <= 0 and self.parry_active <= 0:
            self.parry_active = 18   # ~0.3s window
            self.parry_cooldown = 90
            play(snd_parry)
            return True
        return False

    def try_bullet_time(self):
        if self.bullet_time >= 35 and self.bullet_time_active <= 0:
            self.bullet_time_active = 90  # ~1.5s of slow-mo
            play(snd_slow)
            return True
        return False

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
        if self.overheating and self.heat > 70:
            return []  # can't shoot while overheating hard
        rate = 5 if self.rapid_fire else 12
        # Note: fire_rate_bonus is applied from Game when needed; keep base here
        if self.cooldown <= 0:
            self.cooldown = rate
            play(snd_shoot)
            if self.triple_shot:
                return [Bullet(self.rect.centerx-16, self.rect.top, -12, True, self.bullet_surf),
                        Bullet(self.rect.centerx, self.rect.top, -12, True, self.bullet_surf),
                        Bullet(self.rect.centerx+16, self.rect.top, -12, True, self.bullet_surf)]
            return [Bullet(self.rect.centerx, self.rect.top, -12, True, self.bullet_surf)]
        return []

    def vent_emp(self, game):
        """Manual vent at high heat = EMP that clears nearby enemy bullets."""
        if self.heat < 60: return False
        play(snd_emp)
        # Clear enemy bullets near player
        radius = 140 + int(self.heat)
        cleared = 0
        for b in game.enemy_bullets[:]:
            dist = math.hypot(b.rect.centerx - self.rect.centerx, b.rect.centery - self.rect.centery)
            if dist < radius:
                game.enemy_bullets.remove(b)
                game.explosions.append(Explosion(b.rect.centerx, b.rect.centery))
                cleared += 1
        self.heat = 0
        self.overheating = False
        game.message = f"EMP VENT! ({cleared})"
        game.message_timer = 50
        return True

    def draw(self, surface):
        if self.invincible <= 0 or (int(self.invincible) // 3) % 2 == 0:
            surface.blit(self.image, self.rect)
            if self.powerup_timers["shield"] > 0 or self.parry_active > 0:
                col = CYAN if self.parry_active > 0 else (80,160,255)
                pygame.draw.circle(surface, col, self.rect.center,
                                   max(self.rect.w, self.rect.h)//2 + 10, 2)
            if self.bullet_time_active > 0:
                pygame.draw.circle(surface, (180, 220, 255), self.rect.center,
                                   max(self.rect.w, self.rect.h)//2 + 16, 1)

class Bullet:
    def __init__(self, x, y, speed, is_player=True, image=None, reflected=False):
        self.is_player = is_player
        self.image = image if image else player_bullet_surfs[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.reflected = reflected
    def update(self, time_scale=1.0):
        self.rect.y += self.speed * time_scale
        return -20 <= self.rect.y <= SCREEN_HEIGHT + 20
    def draw(self, surface): surface.blit(self.image, self.rect)

class PowerUp:
    def __init__(self, x, y, ptype):
        self.type = ptype
        self.color = POWERUP_TYPES[ptype]["color"]
        self.label = POWERUP_TYPES[ptype]["label"]
        self.rect = pygame.Rect(x-12, y-12, 24, 24)
        self.speed = 2.3
    def update(self, time_scale=1.0):
        self.rect.y += self.speed * time_scale
        return self.rect.top < SCREEN_HEIGHT
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=4)
        t = font_tiny.render(self.label[0], True, BLACK)
        surface.blit(t, (self.rect.centerx - t.get_width()//2, self.rect.centery - t.get_height()//2))

class Enemy:
    def __init__(self, x, y, etype, is_splitter=False, is_bounty=False, is_boss=False):
        self.type = etype
        self.is_splitter = is_splitter
        self.is_bounty = is_bounty
        self.is_boss = is_boss
        self.diving = False
        self.dive_speed = 0
        if is_boss:
            self.image = pygame.transform.smoothscale(enemy_a_surf, (70, 55))
            self.points = 300
            self.hp = 12
        elif is_splitter:
            self.image = splitter_surf
            self.points = 50
            self.hp = 2
        elif etype == 0:
            self.image = enemy_a_surf; self.points = 30; self.hp = 1
        elif etype == 1:
            self.image = enemy_b_surf; self.points = 20; self.hp = 1
        else:
            self.image = enemy_c_surf; self.points = 10; self.hp = 1
        if is_bounty:
            self.points = int(self.points * 2.5)
            self.hp = max(self.hp, 2)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.alive = True
    def draw(self, surface):
        if self.alive:
            surface.blit(self.image, self.rect)
            if self.is_bounty:
                # glowing outline
                pygame.draw.rect(surface, GOLD, self.rect.inflate(6, 6), 2)
            if self.is_boss:
                # health pips
                for i in range(min(self.hp, 12)):
                    pygame.draw.rect(surface, RED if i < self.hp else DARK,
                                     (self.rect.left + i*5, self.rect.top - 8, 4, 4))


class Explosion:
    def __init__(self, x, y):
        self.x = x; self.y = y; self.frame = 0
    def update(self, time_scale=1.0):
        self.frame += time_scale
        return self.frame < 8
    def draw(self, surface):
        img = explosion_surfs[min(int(self.frame) // 4, 1)]
        surface.blit(img, img.get_rect(center=(self.x, self.y)))

class FloatingText:
    def __init__(self, x, y, text, color=YELLOW):
        self.x = x; self.y = y; self.text = text; self.color = color; self.life = 45
    def update(self, time_scale=1.0):
        self.y -= 1.3 * time_scale; self.life -= time_scale
        return self.life > 0
    def draw(self, surface):
        t = font_tiny.render(self.text, True, self.color)
        surface.blit(t, (self.x - t.get_width()//2, self.y))

class Debris:
    """Floating cover / hazard."""
    def __init__(self):
        self.rect = pygame.Rect(random.randint(40, SCREEN_WIDTH-60), random.randint(180, 380), 28, 18)
        self.vx = random.choice([-1.2, -0.8, 0.8, 1.2])
        self.hp = 3
        self.color = (90, 90, 110)
    def update(self, time_scale=1.0):
        self.rect.x += self.vx * time_scale
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.vx *= -1
        return self.hp > 0
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=3)
        pygame.draw.rect(surface, GRAY, self.rect, 1, border_radius=3)

# Wave Mutators (risk / reward cards between levels)
MUTATORS = [
    {"id": "haste", "name": "HASTE", "desc": "Enemies +25% speed, Score x1.5", "apply": "haste"},
    {"id": "glass", "name": "GLASS CANNON", "desc": "You take double damage, +40% fire rate", "apply": "glass"},
    {"id": "rich", "name": "BOUNTY HUNTER", "desc": "More Bounty targets, +20% score", "apply": "rich"},
    {"id": "swarm", "name": "SWARM", "desc": "Extra enemies, power-ups drop more", "apply": "swarm"},
    {"id": "fortress", "name": "FORTRESS", "desc": "More debris cover, enemies shoot less", "apply": "fortress"},
    {"id": "overclock", "name": "OVERCLOCK", "desc": "Bullet-Time recharges faster, heat builds faster", "apply": "overclock"},
    {"id": "vampire", "name": "VAMPIRE", "desc": "Kills restore a tiny bit of Bullet-Time", "apply": "vampire"},
    {"id": "chaos", "name": "CHAOS", "desc": "Random enemy types, higher risk/reward", "apply": "chaos"},
]

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
        self.debris = []
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
        self.formation_name = "PHALANX"
        self.time_scale = 1.0
        # Mutator system
        self.active_mutators = []
        self.mutator_choices = []
        self.mutator_index = 0
        self.score_mult = 1.0
        self.bounty_bonus = False
        self.extra_enemies = False
        self.fire_rate_bonus = 1.0
        self.double_damage = False
        self.vampire = False
        self.chaos_mode = False

    def start_game(self):
        self.player = Player(self.selected_char, self.difficulty)
        self.score = 0
        self.level = 1
        self.bullets = []
        self.enemy_bullets = []
        self.explosions = []
        self.powerups = []
        self.float_texts = []
        self.debris = [Debris() for _ in range(3)]
        self.formation_name = "PHALANX"
        self.active_mutators = []
        self.score_mult = 1.0
        self.bounty_bonus = False
        self.extra_enemies = False
        self.fire_rate_bonus = 1.0
        self.double_damage = False
        self.vampire = False
        self.chaos_mode = False
        self.spawn_enemies()
        self.state = "playing"
        self.enemy_direction = 1
        self.enemy_speed_modifier = 1.0
        self.shake = 0
        self.time_scale = 1.0
        self.message = f"LEVEL 1 - {self.formation_name}"
        self.message_timer = 70

    def apply_mutator(self, mut):
        self.active_mutators.append(mut["name"])
        aid = mut["apply"]
        if aid == "haste":
            self.enemy_speed_modifier = min(2.0, self.enemy_speed_modifier * 1.25)
            self.score_mult *= 1.5
        elif aid == "glass":
            self.double_damage = True
            self.fire_rate_bonus = 1.4
        elif aid == "rich":
            self.bounty_bonus = True
            self.score_mult *= 1.2
        elif aid == "swarm":
            self.extra_enemies = True
            # drop rate effectively higher via more kills
        elif aid == "fortress":
            for _ in range(4):
                self.debris.append(Debris())
            # slight shoot reduction handled in update
        elif aid == "overclock":
            self.player.bullet_time = min(100, self.player.bullet_time + 40)
        elif aid == "vampire":
            self.vampire = True
        elif aid == "chaos":
            self.chaos_mode = True
            self.score_mult *= 1.3

    def offer_mutators(self):
        """Pick 3 random mutators for the player to choose from."""
        pool = MUTATORS[:]
        random.shuffle(pool)
        self.mutator_choices = pool[:3]
        self.mutator_index = 0
        self.state = "mutator"


    def spawn_enemies(self):
        self.enemies = []
        cfg = DIFFICULTIES[self.difficulty]
        base_rows = cfg["rows"] + (1 if self.extra_enemies else 0)
        base_cols = cfg["cols"] + (1 if self.extra_enemies else 0)
        form_id = (self.level - 1) % 8
        spacing_x, spacing_y = 58, 44
        enemies = []
        bounty_chance = 0.12 if self.bounty_bonus else 0.05

        def add(x, y, etype=None, splitter=False, bounty=False, boss=False):
            if etype is None:
                rowish = max(0, (y - 40) // spacing_y)
                etype = 0 if rowish < 1 else (1 if rowish < 3 else 2)
            if self.chaos_mode and not boss:
                etype = random.randint(0, 2)
            is_bounty = bounty or (random.random() < bounty_chance and not boss)
            enemies.append(Enemy(int(x), int(y), etype, is_splitter=splitter, is_bounty=is_bounty, is_boss=boss))

        if form_id == 0:
            self.formation_name = "PHALANX"
            cols, rows = base_cols, base_rows
            start_x = (SCREEN_WIDTH - cols * spacing_x) // 2
            for r in range(rows):
                for c in range(cols):
                    add(start_x + c * spacing_x, 45 + r * spacing_y, splitter=(r==0 and c%4==0 and self.level>2))
        elif form_id == 1:
            self.formation_name = "SPEARHEAD"
            rows = base_rows + 1
            for r in range(rows):
                count = 2 + r * 2
                total_w = (count - 1) * spacing_x
                start_x = (SCREEN_WIDTH - total_w) // 2
                for c in range(count):
                    add(start_x + c * spacing_x, 45 + r * spacing_y)
        elif form_id == 2:
            self.formation_name = "FLANKERS"
            rows = base_rows
            cols = max(3, base_cols // 2 - 1)
            for side in (0, 1):
                start_x = 40 if side == 0 else SCREEN_WIDTH - 40 - cols * spacing_x
                for r in range(rows):
                    for c in range(cols):
                        add(start_x + c * spacing_x, 50 + r * spacing_y)
        elif form_id == 3:
            self.formation_name = "DIAMOND"
            mid = SCREEN_WIDTH // 2
            layers = min(5, base_rows)
            for r in range(layers):
                count = 1 + r * 2
                if r > layers // 2: count = 1 + (layers - 1 - r) * 2
                total_w = (count - 1) * spacing_x
                start_x = mid - total_w // 2
                for c in range(count):
                    add(start_x + c * spacing_x, 50 + r * spacing_y, splitter=(r==0))
        elif form_id == 4:
            self.formation_name = "SCATTER"
            cols, rows = base_cols + 1, base_rows
            start_x = (SCREEN_WIDTH - cols * spacing_x) // 2
            for r in range(rows):
                for c in range(cols):
                    if (r + c) % 2 == 0:
                        add(start_x + c * spacing_x, 45 + r * spacing_y)
        elif form_id == 5:
            self.formation_name = "WEDGE"
            rows = base_rows + 1
            for r in range(rows):
                count = max(2, (rows - r) * 2 - 1)
                total_w = (count - 1) * spacing_x
                start_x = (SCREEN_WIDTH - total_w) // 2
                for c in range(count):
                    add(start_x + c * spacing_x, 45 + r * spacing_y)
        elif form_id == 6:
            self.formation_name = "PILLARS"
            cols = min(6, base_cols // 2 + 1)
            rows = base_rows + 1
            gap = (SCREEN_WIDTH - 80) // (cols + 1)
            for c in range(cols):
                x = 40 + (c + 1) * gap
                for r in range(rows):
                    add(x - 15, 45 + r * spacing_y, splitter=(r==0 and self.level>3))
        else:
            self.formation_name = "CRESCENT"
            count = base_cols + 2
            for i in range(count):
                t = i / max(1, count - 1)
                x = 60 + t * (SCREEN_WIDTH - 120)
                y = 80 + abs(t - 0.5) * 140
                add(x, y, 0 if abs(t-0.5) < 0.2 else 1)

        # Mini-boss every 5 levels
        if self.level % 5 == 0:
            enemies.append(Enemy(SCREEN_WIDTH//2 - 35, 50, 0, is_boss=True))
            self.formation_name = "BOSS WAVE - " + self.formation_name

        self.enemies = enemies

    def spawn_powerup(self, x, y):
        rate = DIFFICULTIES[self.difficulty]["drop_rate"]
        if self.extra_enemies: rate *= 1.3
        if random.random() < rate:
            self.powerups.append(PowerUp(x, y, random.choice(list(POWERUP_TYPES.keys()))))

    def update_enemies(self, time_scale=1.0):
        if not any(e.alive for e in self.enemies): return
        if self.player and self.player.freeze_enemies: return
        cfg = DIFFICULTIES[self.difficulty]
        self.enemy_move_timer += time_scale
        base = max(5, int(24 / cfg["enemy_speed"]) - self.level)
        interval = max(3, int(base / max(0.2, self.enemy_speed_modifier)))
        if self.enemy_move_timer >= interval:
            self.enemy_move_timer = 0
            alive_non_dive = [e for e in self.enemies if e.alive and not e.diving]
            if alive_non_dive:
                left = min(e.rect.left for e in alive_non_dive)
                right = max(e.rect.right for e in alive_non_dive)
                descend = False
                if self.enemy_direction > 0 and right >= SCREEN_WIDTH - 12:
                    self.enemy_direction = -1; descend = True
                elif self.enemy_direction < 0 and left <= 12:
                    self.enemy_direction = 1; descend = True
                step = max(3, int(10 * self.enemy_speed_modifier * cfg["enemy_speed"]))
                for e in self.enemies:
                    if e.alive and not e.diving:
                        if descend: e.rect.y += 15
                        else: e.rect.x += self.enemy_direction * step
            # Chance for an enemy to start diving
            if random.random() < 0.08 + self.level * 0.005:
                candidates = [e for e in self.enemies if e.alive and not e.diving and not e.is_boss]
                if candidates:
                    diver = random.choice(candidates)
                    diver.diving = True
                    diver.dive_speed = 3.5 + random.random() * 2
            for e in self.enemies:
                if e.alive and e.rect.bottom >= self.player.rect.top - 4:
                    self.player.lives = 0; self.state = "gameover"; return
        # Update divers independently
        for e in self.enemies:
            if e.alive and e.diving:
                e.rect.y += e.dive_speed * time_scale
                # slight tracking toward player
                if e.rect.centerx < self.player.rect.centerx:
                    e.rect.x += 1.2 * time_scale
                else:
                    e.rect.x -= 1.2 * time_scale
                if e.rect.top > SCREEN_HEIGHT:
                    e.alive = False
        self.enemy_shoot_timer += time_scale
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
        # Bullet time scale
        self.time_scale = 0.35 if self.player.bullet_time_active > 0 else 1.0
        ts = self.time_scale

        if self.shake > 0: self.shake = max(0, self.shake - 1)
        self.player.holding_fire = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        self.player.update(keys, ts)

        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_q]) and self.player.can_use_ability():
            self.player.use_ability(self)
        # Parry
        if keys[pygame.K_e] or keys[pygame.K_f]:
            self.player.try_parry()
        # Bullet time
        if keys[pygame.K_r]:
            self.player.try_bullet_time()
        # EMP vent (release fire when hot, or press V)
        if keys[pygame.K_v] or (not self.player.holding_fire and self.player.heat > 75 and self.player.overheating):
            self.player.vent_emp(self)

        if self.player.holding_fire:
            self.bullets.extend(self.player.shoot())

        self.bullets = [b for b in self.bullets if b.update(ts)]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.update(ts)]

        # Player bullets vs enemies + splitters
        for b in self.bullets[:]:
            for e in self.enemies:
                if e.alive and b.rect.colliderect(e.rect):
                    e.hp -= 1
                    if e.hp <= 0:
                        e.alive = False
                        if e.is_splitter:
                            self.enemies.append(Enemy(e.rect.centerx - 20, e.rect.centery + 10, 2))
                            self.enemies.append(Enemy(e.rect.centerx + 20, e.rect.centery + 10, 2))
                            self.float_texts.append(FloatingText(e.rect.centerx, e.rect.centery, "SPLIT!", ORANGE))
                        if e.is_bounty:
                            self.float_texts.append(FloatingText(e.rect.centerx, e.rect.centery - 20, "BOUNTY!", GOLD))
                            # Stage buff: small permanent-ish bonuses
                            self.player.base_speed = min(9, self.player.base_speed + 0.3)
                            self.player.bullet_time = min(100, self.player.bullet_time + 20)
                            self.message = "BOUNTY CLAIMED!"
                            self.message_timer = 50
                        if e.is_boss:
                            self.float_texts.append(FloatingText(e.rect.centerx, e.rect.centery - 25, "BOSS DOWN!", RED))
                            self.player.lives = min(self.player.lives + 1, 8)
                        self.player.combo += 1
                        self.player.combo_timer = 100
                        mult = 1 + min(self.player.combo // 4, 5)
                        pts = int(e.points * mult * self.score_mult)
                        self.score += pts
                        self.explosions.append(Explosion(e.rect.centerx, e.rect.centery))
                        self.float_texts.append(FloatingText(e.rect.centerx, e.rect.centery-8, f"+{pts}", ORANGE if mult > 1 else YELLOW))
                        self.spawn_powerup(e.rect.centerx, e.rect.centery)
                        if self.vampire:
                            self.player.bullet_time = min(100, self.player.bullet_time + 4)
                        play(snd_hit)
                    if b in self.bullets: self.bullets.remove(b)
                    break
            # Debris can block player shots
            for d in self.debris:
                if d.hp > 0 and b.rect.colliderect(d.rect):
                    d.hp -= 1
                    if b in self.bullets: self.bullets.remove(b)
                    break

        # Enemy bullets vs player + parry reflect
        for b in self.enemy_bullets[:]:
            if self.player.parry_active > 0 and b.rect.colliderect(self.player.rect.inflate(20, 20)):
                # Reflect!
                self.enemy_bullets.remove(b)
                reflected = Bullet(b.rect.centerx, b.rect.centery, -9, True, reflected_bullet_surf, reflected=True)
                self.bullets.append(reflected)
                self.float_texts.append(FloatingText(self.player.rect.centerx, self.player.rect.top - 10, "PARRY!", CYAN))
                play(snd_parry)
                continue
            if self.player.invincible <= 0 and b.rect.colliderect(self.player.rect):
                dmg = 2 if self.double_damage else 1
                self.player.lives -= dmg
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

        self.powerups = [p for p in self.powerups if p.update(ts)]
        for p in self.powerups[:]:
            if p.rect.colliderect(self.player.rect):
                self.player.apply_powerup(p.type, self)
                self.powerups.remove(p)
        self.explosions = [ex for ex in self.explosions if ex.update(ts)]
        self.float_texts = [ft for ft in self.float_texts if ft.update(ts)]
        self.debris = [d for d in self.debris if d.update(ts)]
        if len(self.debris) < 2 and random.random() < 0.004:
            self.debris.append(Debris())

        self.update_enemies(ts)
        if all(not e.alive for e in self.enemies):
            self.level += 1
            self.bullets.clear()
            self.enemy_bullets.clear()
            self.powerups.clear()
            self.player.bullet_time = min(100, self.player.bullet_time + 25)
            # Offer mutators every level after 1
            if self.level > 1:
                self.offer_mutators()
            else:
                self.spawn_enemies()
                self.message = f"LEVEL {self.level} - {self.formation_name}"
                self.message_timer = 80

        if self.message_timer > 0: self.message_timer -= 1

    # ---------- Drawing ----------
    def draw_menu(self):
        screen.fill(BLACK)
        t = font_large.render("WOKE INVADERS", True, NEON_PINK)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
        s = font_med.render("Combat Expanded Edition", True, PURPLE)
        screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 105))
        lines = [
            "NEW: Parry • Overheat EMP • Bullet-Time • Warp",
            "Splitters • Debris • Stronger Combos",
            "",
            "ENTER - Start   |   ESC - Quit"
        ]
        for i, line in enumerate(lines):
            c = WHITE if i < 2 else GRAY
            tt = font_small.render(line, True, c)
            screen.blit(tt, (SCREEN_WIDTH//2 - tt.get_width()//2, 170 + i*28))
        y = 320
        for d in ["EASY", "NORMAL", "HARD"]:
            hs = self.highscores.get(d, 0)
            tt = font_tiny.render(f"{d}: {hs}", True, GOLD if hs else GRAY)
            screen.blit(tt, (SCREEN_WIDTH//2 - tt.get_width()//2, y)); y += 22
        # Controls reminder
        ctrl = [
            "Shoot: Space/W   Ability: Shift/Q",
            "Parry: E/F   EMP Vent: V   Bullet-Time: R",
            "Warp: fly off left/right edge"
        ]
        for i, line in enumerate(ctrl):
            tt = font_tiny.render(line, True, GRAY)
            screen.blit(tt, (SCREEN_WIDTH//2 - tt.get_width()//2, 420 + i*18))

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
            desc = font_tiny.render(f"Lives {cfg['lives']}  |  Speed {cfg['enemy_speed']}x", True, GRAY)
            screen.blit(desc, (SCREEN_WIDTH//2 - desc.get_width()//2, 200 + i*60))
        h = font_small.render("UP/DOWN  •  ENTER  •  ESC", True, GRAY)
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
        h = font_tiny.render("LEFT/RIGHT  •  ENTER  •  ESC", True, GRAY)
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
        for d in self.debris: d.draw(screen)
        for e in self.enemies:
            if e.alive: screen.blit(e.image, (e.rect.x + ox, e.rect.y + oy))
        self.player.draw(screen)
        for b in self.bullets: screen.blit(b.image, (b.rect.x + ox, b.rect.y + oy))
        for b in self.enemy_bullets: screen.blit(b.image, (b.rect.x + ox, b.rect.y + oy))
        for p in self.powerups: p.draw(screen)
        for ex in self.explosions: ex.draw(screen)
        for ft in self.float_texts: ft.draw(screen)

        # HUD
        screen.blit(font_small.render(f"SCORE: {self.score}", True, WHITE), (12, 6))
        screen.blit(font_small.render(f"LVL {self.level}", True, CYAN), (12, 28))
        fname = getattr(self, "formation_name", "")
        if fname: screen.blit(font_tiny.render(fname, True, GRAY), (12, 48))
        screen.blit(font_small.render(f"LIVES: {self.player.lives}", True, RED), (SCREEN_WIDTH-125, 6))
        screen.blit(font_tiny.render(char_names[self.player.char_index], True, char_colors[self.player.char_index]), (SCREEN_WIDTH-125, 28))

        if self.player.combo >= 3:
            c = font_small.render(f"COMBO x{1+min(self.player.combo//4,5)}", True, ORANGE)
            screen.blit(c, (SCREEN_WIDTH//2 - c.get_width()//2, 28))

        # Ability status
        if self.player.can_use_ability():
            ab = font_tiny.render("ABILITY [SHIFT/Q]", True, GREEN)
        elif self.player.ability_active > 0:
            ab = font_tiny.render("ABILITY ACTIVE", True, YELLOW)
        else:
            ab = font_tiny.render(f"Ability {max(1,int(self.player.ability_cooldown)//60)}s", True, GRAY)
        screen.blit(ab, (SCREEN_WIDTH//2 - ab.get_width()//2, 6))

        # Heat bar
        hw = 100
        pygame.draw.rect(screen, DARK, (SCREEN_WIDTH//2 - hw//2, 48, hw, 7))
        heat_col = ORANGE if self.player.heat < 70 else RED
        pygame.draw.rect(screen, heat_col, (SCREEN_WIDTH//2 - hw//2, 48, int(hw * self.player.heat/100), 7))
        if self.player.overheating:
            screen.blit(font_tiny.render("OVERHEAT - V to VENT", True, RED), (SCREEN_WIDTH//2 - 60, 58))

        # Bullet time bar
        bw = 80
        pygame.draw.rect(screen, DARK, (SCREEN_WIDTH-100, 50, bw, 6))
        pygame.draw.rect(screen, (150, 200, 255), (SCREEN_WIDTH-100, 50, int(bw * self.player.bullet_time/100), 6))
        screen.blit(font_tiny.render("R", True, (150,200,255)), (SCREEN_WIDTH-112, 46))

        # Parry cooldown indicator
        if self.player.parry_cooldown > 0:
            screen.blit(font_tiny.render("Parry CD", True, GRAY), (SCREEN_WIDTH-100, 62))
        elif self.player.parry_active > 0:
            screen.blit(font_tiny.render("PARRY!", True, CYAN), (SCREEN_WIDTH-90, 62))
        else:
            screen.blit(font_tiny.render("E/F Parry", True, GREEN), (SCREEN_WIDTH-100, 62))

        active = []
        if self.player.powerup_timers.get("rapid",0) > 0: active.append(("RAPID", CYAN))
        if self.player.powerup_timers.get("spread",0) > 0: active.append(("SPREAD", YELLOW))
        if self.player.powerup_timers.get("shield",0) > 0: active.append(("SHIELD", (80,160,255)))
        if self.player.powerup_timers.get("slow",0) > 0: active.append(("SLOW", PURPLE))
        for i,(n,c) in enumerate(active):
            screen.blit(font_tiny.render(n, True, c), (12, 68 + i*16))

        if self.message_timer > 0:
            m = font_med.render(self.message, True, YELLOW)
            screen.blit(m, (SCREEN_WIDTH//2 - m.get_width()//2, SCREEN_HEIGHT//2 - 40))

        if self.player.bullet_time_active > 0:
            # slight blue tint overlay for bullet time
            ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            ov.fill((100, 160, 255, 25))
            screen.blit(ov, (0,0))

    def draw_paused(self):
        self.draw_playing()
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0,0,0,170))
        screen.blit(ov, (0,0))
        t = font_large.render("PAUSED", True, WHITE)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 200))
        lines = ["P / ESC = Resume", "Q = Quit to Menu", "",
                 "E/F = Parry   V = EMP Vent   R = Bullet-Time",
                 "Fly off edge = Warp"]
        for i, line in enumerate(lines):
            tt = font_small.render(line, True, GRAY if i > 1 else WHITE)
            screen.blit(tt, (SCREEN_WIDTH//2 - tt.get_width()//2, 270 + i*26))

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

    def draw_mutator(self):
        screen.fill(BLACK)
        t = font_med.render("CHOOSE A MUTATOR", True, WHITE)
        screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
        sub = font_tiny.render(f"Level {self.level}  •  Active: {', '.join(self.active_mutators) or 'None'}", True, GRAY)
        screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 90))
        for i, mut in enumerate(self.mutator_choices):
            y = 150 + i * 100
            col = GOLD if i == self.mutator_index else GRAY
            pygame.draw.rect(screen, col, (120, y, 560, 80), 2, border_radius=6)
            name = font_med.render(mut["name"], True, col)
            screen.blit(name, (140, y + 12))
            desc = font_small.render(mut["desc"], True, WHITE)
            screen.blit(desc, (140, y + 45))
        h = font_small.render("UP/DOWN  •  ENTER to accept", True, GRAY)
        screen.blit(h, (SCREEN_WIDTH//2 - h.get_width()//2, 520))

    def draw(self):
        if self.state == "menu": self.draw_menu()
        elif self.state == "difficulty": self.draw_difficulty()
        elif self.state == "select": self.draw_select()
        elif self.state == "playing": self.draw_playing()
        elif self.state == "paused": self.draw_paused()
        elif self.state == "gameover": self.draw_gameover()
        elif self.state == "mutator": self.draw_mutator()
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
                    elif game.state in ("difficulty", "select", "gameover", "mutator"): game.state = "menu"
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
                    elif game.state == "mutator":
                        # Apply chosen mutator and start next wave
                        chosen = game.mutator_choices[game.mutator_index]
                        game.apply_mutator(chosen)
                        game.spawn_enemies()
                        game.message = f"LEVEL {game.level} - {game.formation_name}"
                        game.message_timer = 80
                        game.state = "playing"
                        play(snd_power)
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
                if game.state == "mutator":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        game.mutator_index = (game.mutator_index - 1) % 3; play(snd_select)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        game.mutator_index = (game.mutator_index + 1) % 3; play(snd_select)
        if game.state == "playing":
            game.update(keys)
        game.draw()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

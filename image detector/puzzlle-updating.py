import os
import sys
import random
import math
import pygame

# ---------------- SETTINGS ----------------
WIN_W, WIN_H = 1000, 720
MARGIN = 24
BOARD_PAD = 16
STRIP_GAP = 8
TOPBAR_H = 80
BOTTOMBAR_H = 90

BG = (248, 250, 255)
PANEL = (255, 255, 255)
PANEL_BORDER = (190, 205, 255)
PANEL_SHADOW = (220, 228, 255)

TEXT = (40, 50, 70)
TEXT_SUB = (90, 105, 140)
ACCENT = (90, 130, 255)
ACCENT_DARK = (60, 100, 230)
GOOD = (0, 180, 120)
HILITE = (255, 180, 80)
GHOST = (236, 240, 255)

# Number badge (left-side)
BADGE_BG = (255, 247, 215)
BADGE_BORDER = (210, 190, 150)
BADGE_TEXT = (80, 55, 0)
BADGE_W = 48                 # width of left badge area
BADGE_RADIUS = 12            # rounded corner radius

TITLE = "Picture Strip Puzzle"
IMAGE_FILE = "picture.jpg"
MUSIC_FILE = "bg_music.mp3"   # optional
SWAP_SFX = "swap.wav"         # optional
WIN_SFX = "win.wav"           # optional

DIFFICULTIES = {"Easy": 4, "Medium": 6, "Hard": 8}
DEFAULT_DIFF = "Medium"

# --------------- HELPERS ------------------

def load_image_or_placeholder(path, w=1200, h=800):
    if not os.path.exists(path):
        surf = pygame.Surface((w, h))
        surf.fill((210, 240, 255))
        center = (w//2, h//2)
        pygame.draw.circle(surf, (255, 230, 100), center, min(w, h)//4)
        pygame.draw.circle(surf, (0,0,0), (center[0]-60, center[1]-40), 18)
        pygame.draw.circle(surf, (0,0,0), (center+60, center[1]-40), 18)
        pygame.draw.arc(surf, (0,0,0), (center-90, center[1]-40, 180, 160), math.pi*0.15, math.pi*0.85, 7)
        colors = [(255,0,0),(255,128,0),(255,255,0),(0,200,0),(0,150,255),(150,0,255)]
        for i,c in enumerate(colors):
            pygame.draw.arc(surf, c, (80+i*6, 60+i*6, w-160-i*12, h-120-i*12), math.pi, math.pi*2, 8)
        return surf.convert()
    return pygame.image.load(path).convert()

def try_play_music(path, vol=0.35):
    try:
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)
            return True
    except Exception:
        pass
    return False

def try_load_sound(path):
    try:
        if os.path.exists(path):
            return pygame.mixer.Sound(path)
    except Exception:
        pass
    return None

def rounded_rect(surface, rect, color, radius=14, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def draw_shadow_panel(surface, rect, radius=16, shadow=8):
    shadow_rect = rect.move(shadow, shadow)
    rounded_rect(surface, shadow_rect, PANEL_SHADOW, radius)
    rounded_rect(surface, rect, PANEL, radius)
    pygame.draw.rect(surface, PANEL_BORDER, rect, width=2, border_radius=radius)

def fit_image_to_rect(img, target_rect):
    img_w, img_h = img.get_size()
    tw, th = target_rect.width, target_rect.height
    if img_w == 0 or img_h == 0:
        scaled = pygame.Surface((1, 1))
        return scaled, pygame.Rect(target_rect.x, target_rect.y, 1, 1)
    scale = min(tw/img_w, th/img_h)
    nw, nh = max(1, int(img_w*scale)), max(1, int(img_h*scale))
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    x = target_rect.x + (tw - nw)//2
    y = target_rect.y + (th - nh)//2
    return scaled, pygame.Rect(x, y, nw, nh)

class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.hover = False
        self.active = False

    def draw(self, screen, font):
        base = ACCENT if (self.active or self.hover) else (255,255,255)
        txt_col = (255,255,255) if (self.active or self.hover) else ACCENT_DARK
        rounded_rect(screen, self.rect.move(3,3), PANEL_SHADOW, 12)
        rounded_rect(screen, self.rect, base, 12)
        pygame.draw.rect(screen, ACCENT_DARK, self.rect, 2, border_radius=12)
        label = font.render(self.label, True, txt_col)
        screen.blit(label, (self.rect.centerx - label.get_width()//2,
                            self.rect.centery - label.get_height()//2))

    def handle(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                return True
        return False

class Strip:
    # CHANGED: no bottom label; draw a left badge instead.
    def __init__(self, image_scaled, src_rect, correct_index):
        self.image_scaled = image_scaled
        self.src_rect = src_rect
        self.correct_index = correct_index
        self.cache = None  # ((width, strip_h), Surface)

    def render(self, width, strip_h, font):
        key = (width, strip_h)
        if self.cache and self.cache[0] == key:
            return self.cache[1]

        # Picture area is full height; image drawn offset to the right of the badge
        picture_w = max(1, width - BADGE_W)
        part = self.image_scaled.subsurface(self.src_rect).copy()
        part_scaled = pygame.transform.smoothscale(part, (picture_w, strip_h))

        surf = pygame.Surface((width, strip_h), pygame.SRCALPHA)

        # Badge background on the left side
        badge_rect = pygame.Rect(0, 0, BADGE_W, strip_h)
        rounded_rect(surf, badge_rect, BADGE_BG, BADGE_RADIUS)
        pygame.draw.rect(surf, BADGE_BORDER, badge_rect, 2, border_radius=BADGE_RADIUS)

        # Number text centered in the badge
        txt = font.render(str(self.correct_index + 1), True, BADGE_TEXT)
        surf.blit(txt, (badge_rect.centerx - txt.get_width()//2,
                        badge_rect.centery - txt.get_height()//2))

        # Picture slice to the right of the badge
        surf.blit(part_scaled, (BADGE_W, 0))

        self.cache = (key, surf)
        return surf

def build_strips(image_scaled, rows):
    w, h = image_scaled.get_size()
    base = h // rows
    remainder = h - base*rows
    rects, y = [], 0
    for i in range(rows):
        hh = base + (1 if i < remainder else 0)
        rects.append(pygame.Rect(0, y, w, hh))
        y += hh
    return [Strip(image_scaled, r, i) for i, r in enumerate(rects)]

def make_confetti(n, win_w, win_h):
    cols = [(255,0,0),(255,128,0),(255,220,0),(0,200,120),(0,150,255),(150,0,255),(255,105,180)]
    parts = []
    for _ in range(n):
        parts.append({
            "x": random.uniform(0, win_w),
            "y": random.uniform(-200, -20),
            "vx": random.uniform(-40, 40),
            "vy": random.uniform(120, 260),
            "size": random.randint(4, 9),
            "color": random.choice(cols)
        })
    return parts

# --------------- MAIN --------------------

def main():
    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except Exception:
        pass

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("Comic Sans MS, Arial Rounded MT Bold", 42, bold=True)
    ui_font = pygame.font.SysFont("Nunito, Comic Sans MS, Arial", 24, bold=True)
    strip_font = pygame.font.SysFont("Baloo, Comic Sans MS, Arial", 28, bold=True)
    win_font = pygame.font.SysFont("Comic Sans MS, Arial Rounded MT Bold", 64, bold=True)

    music_on = try_play_music(MUSIC_FILE, 0.35)
    swap_sfx = try_load_sound(SWAP_SFX)
    win_sfx = try_load_sound(WIN_SFX)

    topbar = pygame.Rect(0, 0, WIN_W, TOPBAR_H)
    bottombar = pygame.Rect(0, WIN_H - BOTTOMBAR_H, WIN_W, BOTTOMBAR_H)
    board_rect = pygame.Rect(MARGIN, TOPBAR_H + MARGIN, WIN_W - 2*MARGIN, WIN_H - TOPBAR_H - BOTTOMBAR_H - 2*MARGIN)
    inner_board = board_rect.inflate(-2*BOARD_PAD, -2*BOARD_PAD)
    picture_area = inner_board.inflate(-2*BOARD_PAD, -2*BOARD_PAD)

    full_img = load_image_or_placeholder(IMAGE_FILE)

    diff_name = DEFAULT_DIFF
    rows = DIFFICULTIES[diff_name]

    # Buttons
    btn_w, btn_h = 150, 44
    spacing = 16
    btns = {}
    btns["Shuffle"] = Button((MARGIN, WIN_H - BOTTOMBAR_H + (BOTTOMBAR_H-btn_h)//2, btn_w, btn_h), "Shuffle")
    dx = MARGIN + btn_w + spacing
    for name in ["Easy", "Medium", "Hard"]:
        btns[name] = Button((dx, WIN_H - BOTTOMBAR_H + (BOTTOMBAR_H-btn_h)//2, 120, btn_h), name)
        dx += 120 + 10
    btns["Mute"] = Button((WIN_W - MARGIN - 110, WIN_H - BOTTOMBAR_H + (BOTTOMBAR_H-btn_h)//2, 110, btn_h),
                          "Mute" if music_on else "Unmute")

    def rebuild_assets(rows):
        scaled_img, scaled_rect = fit_image_to_rect(full_img, picture_area)
        strips = build_strips(scaled_img, rows)

        total_gap = STRIP_GAP * (rows - 1)
        # CHANGED: no bottom label; compute height purely from image slices
        strip_pic_h = max(1, scaled_img.get_height() // rows)
        strip_h = max(70, strip_pic_h)  # minimum click-friendly height

        total_h = rows*strip_h + total_gap
        final_width = min(scaled_img.get_width() + BADGE_W, picture_area.width)

        start_x = picture_area.x + (picture_area.width - final_width)//2
        start_y = picture_area.y + (picture_area.height - total_h)//2
        dest_rects = []
        y = start_y
        for _ in range(rows):
            dest_rects.append(pygame.Rect(start_x, y, final_width, strip_h))
            y += strip_h + STRIP_GAP
        return scaled_img, scaled_rect, strips, dest_rects, strip_h

    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
    order = list(range(rows))
    random.shuffle(order)

    selected_pos = None
    won = False
    confetti = []
    swap_anim = 0.0
    swap_pair = None

    def is_solved():
        return all(order[i] == i for i in range(len(order)))

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            for b in btns.values():
                b.handle(ev)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and not won:
                mx, my = ev.pos

                # Buttons
                if btns["Shuffle"].rect.collidepoint((mx, my)):
                    random.shuffle(order); selected_pos=None; won=False
                    confetti.clear(); swap_anim=0.0; swap_pair=None
                    continue
                if btns["Easy"].rect.collidepoint((mx, my)):
                    diff_name="Easy"; rows=DIFFICULTIES[diff_name]
                    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
                    order=list(range(rows)); random.shuffle(order); selected_pos=None; won=False
                    continue
                if btns["Medium"].rect.collidepoint((mx, my)):
                    diff_name="Medium"; rows=DIFFICULTIES[diff_name]
                    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
                    order=list(range(rows)); random.shuffle(order); selected_pos=None; won=False
                    continue
                if btns["Hard"].rect.collidepoint((mx, my)):
                    diff_name="Hard"; rows=DIFFICULTIES[diff_name]
                    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
                    order=list(range(rows)); random.shuffle(order); selected_pos=None; won=False
                    continue
                if btns["Mute"].rect.collidepoint((mx, my)):
                    if pygame.mixer.get_init():
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.pause(); btns["Mute"].label="Unmute"
                        else:
                            pygame.mixer.music.unpause(); btns["Mute"].label="Mute"
                    continue

                # Strips
                clicked = None
                for i, r in enumerate(dest_rects):
                    rr = r.inflate(8, 8)
                    if rr.collidepoint(mx, my):
                        clicked = i
                        break
                if clicked is not None:
                    if selected_pos is None:
                        selected_pos = clicked
                    else:
                        if clicked != selected_pos:
                            order[selected_pos], order[clicked] = order[clicked], order[selected_pos]
                            swap_pair = (selected_pos, clicked)
                            swap_anim = 0.15
                            if swap_sfx:
                                try: swap_sfx.play()
                                except Exception: pass
                        selected_pos = None
                        if is_solved():
                            won = True
                            if win_sfx:
                                try: win_sfx.play()
                                except Exception: pass
                            confetti = make_confetti(160, WIN_W, WIN_H)

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    random.shuffle(order); selected_pos=None; won=False; confetti.clear()
                if ev.key == pygame.K_1:
                    diff_name="Easy"; rows=DIFFICULTIES[diff_name]
                    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
                    order=list(range(rows)); random.shuffle(order); selected_pos=None; won=False
                if ev.key == pygame.K_2:
                    diff_name="Medium"; rows=DIFFICULTIES[diff_name]
                    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
                    order=list(range(rows)); random.shuffle(order); selected_pos=None; won=False
                if ev.key == pygame.K_3:
                    diff_name="Hard"; rows=DIFFICULTIES[diff_name]
                    scaled_img, scaled_rect, strips, dest_rects, strip_h = rebuild_assets(rows)
                    order=list(range(rows)); random.shuffle(order); selected_pos=None; won=False
                if ev.key == pygame.K_m:
                    if pygame.mixer.get_init():
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.pause(); btns["Mute"].label="Unmute"
                        else:
                            pygame.mixer.music.unpause(); btns["Mute"].label="Mute"

        # Update animations
        if swap_anim > 0:
            swap_anim -= dt
            if swap_anim < 0: swap_anim = 0
        if won:
            for p in confetti:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                if p["y"] > WIN_H + 20:
                    p["y"] = random.uniform(-200, -20)
                    p["x"] = random.uniform(0, WIN_W)

        # --------------- DRAW ----------------
        screen.fill(BG)

        # Top bar
        draw_shadow_panel(screen, pygame.Rect(12, 10, WIN_W-24, TOPBAR_H-16), radius=16)
        title = title_font.render("Make the Picture!", True, TEXT)
        subtitle = ui_font.render("Numbers are on the left. Click two strips to swap.", True, TEXT_SUB)
        screen.blit(title, (MARGIN+6, 14))
        screen.blit(subtitle, (MARGIN+8, 14 + title.get_height()))

        # Board
        draw_shadow_panel(screen, board_rect, radius=18)
        rounded_rect(screen, inner_board, (244, 247, 255), 14)

        # Ghost lanes
        for r in dest_rects:
            pygame.draw.rect(screen, GHOST, r, border_radius=10)

        # Draw strips
        for pos, r in enumerate(dest_rects):
            idx = order[pos]
            surf = strips[idx].render(r.width, r.height, strip_font)

            rounded_rect(screen, r, PANEL, 12)
            pygame.draw.rect(screen, (230, 235, 255), r, 0, border_radius=12)
            pygame.draw.rect(screen, (205, 215, 245), r, 2, border_radius=12)

            if swap_anim > 0 and swap_pair and (pos in swap_pair):
                scale = 1.0 + 0.06 * (swap_anim / 0.15)
                sw = int(surf.get_width()*scale)
                sh = int(surf.get_height()*scale)
                pop = pygame.transform.smoothscale(surf, (sw, sh))
                screen.blit(pop, (r.centerx - sw//2, r.centery - sh//2))
            else:
                screen.blit(surf, (r.x, r.y))

            if selected_pos == pos:
                pygame.draw.rect(screen, HILITE, r.inflate(10,10), 6, border_radius=14)

        # Win overlay
        if won:
            overlay = inner_board.inflate(-BOARD_PAD*2, -BOARD_PAD*2)
            full_only, full_rect = fit_image_to_rect(full_img, overlay)
            ov_panel = full_rect.inflate(20, 20)
            rounded_rect(screen, ov_panel, PANEL, 18)
            pygame.draw.rect(screen, PANEL_BORDER, ov_panel, 2, border_radius=18)
            screen.blit(full_only, full_rect.topleft)

            win_text = win_font.render("You did it!", True, GOOD)
            screen.blit(win_text, (WIN_W//2 - win_text.get_width()//2, inner_board.y - 10))

            for p in confetti:
                pygame.draw.rect(screen, p["color"], (p["x"], p["y"], p["size"], p["size"]))

        # Bottom bar + buttons
        draw_shadow_panel(screen, bottombar, radius=16)
        for name in ["Easy", "Medium", "Hard"]:
            btns[name].active = (name == diff_name)
        for b in btns.values():
            b.draw(screen, ui_font)

        help1 = ui_font.render("R: Reshuffle   1/2/3: Difficulty   M: Mute", True, TEXT_SUB)
        screen.blit(help1, (WIN_W - MARGIN - help1.get_width() - 20, WIN_H - BOTTOMBAR_H + 14))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

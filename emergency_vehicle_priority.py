"""
Emergency Vehicle Priority System Using Computer Graphics Animation
====================================================================
CGIP Algorithms Used:
  1. DDA Line Drawing Algorithm   - for all straight lines (roads, vehicles, buildings)
  2. Midpoint Circle Drawing      - for wheels and traffic-signal lights
  3. 2D Translation Transformation- for frame-based vehicle movement
  4. Frame-Based Animation        - 60 FPS game loop with double buffering
  5. State Machine                - traffic signal + emergency override logic
"""

import pygame
import sys
import math
import random

# ──────────────────────────────────────────────────────────────────────────────
# WINDOW CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 650
FPS = 60

# Colours (R, G, B)
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GRAY       = (100, 100, 100)
DARK_GRAY  = ( 50,  50,  50)
ROAD_COLOR = ( 60,  60,  60)
ROAD_LINE  = (220, 220,   0)   # yellow road markings
RED        = (220,   0,   0)
GREEN      = (  0, 200,   0)
YELLOW     = (220, 220,   0)
DARK_RED   = (180,   0,   0)
ORANGE     = (255, 140,   0)
BLUE       = ( 30, 144, 255)
LIGHT_BLUE = (135, 206, 235)
CAR_BLUE   = ( 30, 100, 200)
CAR_GREEN  = ( 30, 150,  80)
AMBU_WHITE = (240, 240, 240)
SIGNAL_BOX = ( 30,  30,  30)
SKY_TOP    = ( 30,  90, 180)
SKY_BOT    = (100, 160, 220)
GRASS      = ( 60, 120,  40)

# Road geometry
ROAD_W = 90          # half-width of each arm
CX, CY = WIDTH // 2, HEIGHT // 2   # intersection centre

# ──────────────────────────────────────────────────────────────────────────────
# PART 1 – PIXEL PLOTTING & DDA LINE ALGORITHM
# ──────────────────────────────────────────────────────────────────────────────

def put_pixel(surface, x, y, color):
    """Plot a single pixel at (x, y) with the given colour."""
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        surface.set_at((int(x), int(y)), color)

def DDA_line(surface, x1, y1, x2, y2, color):
    """DDA (Digital Differential Analyzer) Line Drawing Algorithm."""
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        put_pixel(surface, x1, y1, color)
        return
    x_inc = dx / steps
    y_inc = dy / steps
    x, y = float(x1), float(y1)
    for _ in range(int(steps) + 1):
        put_pixel(surface, round(x), round(y), color)
        x += x_inc
        y += y_inc

def DDA_thick_line(surface, x1, y1, x2, y2, color, thickness=1):
    """Draw a thick line by stacking multiple DDA lines."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0: return
    px = -dy / length
    py =  dx / length
    half = thickness / 2
    for t in range(-int(half), int(half) + 1):
        ox, oy = round(px * t), round(py * t)
        DDA_line(surface, x1 + ox, y1 + oy, x2 + ox, y2 + oy, color)

# ──────────────────────────────────────────────────────────────────────────────
# PART 2 – MIDPOINT CIRCLE DRAWING ALGORITHM
# ──────────────────────────────────────────────────────────────────────────────

def midpoint_circle(surface, xc, yc, r, color):
    """Midpoint Circle Drawing Algorithm (8-way symmetry)."""
    x, y = 0, r
    p = 1 - r
    def _plot8(cx, cy, px, py):
        for sx, sy in [(cx+px,cy+py),(cx-px,cy+py),(cx+px,cy-py),(cx-px,cy-py),
                       (cx+py,cy+px),(cx-py,cy+px),(cx+py,cy-px),(cx-py,cy-px)]:
            put_pixel(surface, sx, sy, color)
    _plot8(xc, yc, x, y)
    while x < y:
        x += 1
        if p < 0: p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1
        _plot8(xc, yc, x, y)

def filled_midpoint_circle(surface, xc, yc, r, color):
    """Fill a circle derived from the midpoint algo."""
    x, y = 0, r
    p = 1 - r
    def _hline(cx, cy, px, py):
        DDA_line(surface, cx - px, cy + py, cx + px, cy + py, color)
        DDA_line(surface, cx - px, cy - py, cx + px, cy - py, color)
        DDA_line(surface, cx - py, cy + px, cx + py, cy + px, color)
        DDA_line(surface, cx - py, cy - px, cx + py, cy - px, color)
    _hline(xc, yc, x, y)
    while x < y:
        x += 1
        if p < 0: p += 2 * x + 1
        else:
            y -= 1
            p += 2 * (x - y) + 1
        _hline(xc, yc, x, y)

# ──────────────────────────────────────────────────────────────────────────────
# BACKGROUND & ROADS
# ──────────────────────────────────────────────────────────────────────────────

def create_static_background():
    """Pre-render sky, grass, and roads once to save thousands of DDA calls per frame."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    
    # Sky (Gradient)
    sky_height = CY - ROAD_W
    for row in range(sky_height):
        t = row / max(sky_height - 1, 1)
        r = int(SKY_TOP[0] + t * (SKY_BOT[0] - SKY_TOP[0]))
        g = int(SKY_TOP[1] + t * (SKY_BOT[1] - SKY_TOP[1]))
        b = int(SKY_TOP[2] + t * (SKY_BOT[2] - SKY_TOP[2]))
        DDA_line(bg, 0, row, WIDTH - 1, row, (r, g, b))
    
    # Grass (Large blocks use Surface.fill for speed)
    bg.fill(GRASS, (0, sky_height, WIDTH, HEIGHT - sky_height))
    
    # Roads
    # Horizontal road fill
    bg.fill(ROAD_COLOR, (0, CY - ROAD_W, WIDTH, ROAD_W * 2))
    # Vertical road fill
    bg.fill(ROAD_COLOR, (CX - ROAD_W, 0, ROAD_W * 2, HEIGHT))

    # Road Borders (DDA Thick)
    DDA_thick_line(bg, 0, CY - ROAD_W, WIDTH - 1, CY - ROAD_W, WHITE, 2)
    DDA_thick_line(bg, 0, CY + ROAD_W, WIDTH - 1, CY + ROAD_W, WHITE, 2)
    DDA_thick_line(bg, CX - ROAD_W, 0, CX - ROAD_W, HEIGHT - 1, WHITE, 2)
    DDA_thick_line(bg, CX + ROAD_W, 0, CX + ROAD_W, HEIGHT - 1, WHITE, 2)

    # Centre dashes
    dash, gap = 20, 15
    # H
    x = 0
    while x < WIDTH:
        if x < CX - ROAD_W or x > CX + ROAD_W:
            DDA_thick_line(bg, x, CY, x + dash, CY, ROAD_LINE, 2)
        x += dash + gap
    # V
    y = 0
    while y < HEIGHT:
        if y < CY - ROAD_W or y > CY + ROAD_W:
            DDA_thick_line(bg, CX, y, CX, y + dash, ROAD_LINE, 2)
        y += dash + gap
        
    return bg

# ──────────────────────────────────────────────────────────────────────────────
# SIGNAL CONTROLLER
# ──────────────────────────────────────────────────────────────────────────────

RED_STATE, YELLOW_STATE, GREEN_STATE = 0, 1, 2
CYCLE_TIMES = {RED_STATE: 150, YELLOW_STATE: 40, GREEN_STATE: 150} # Slightly faster cycles

class SignalController:
    def __init__(self):
        self.mode = "NORMAL"
        self.h_state = GREEN_STATE
        self.v_state = RED_STATE
        self.h_timer = CYCLE_TIMES[GREEN_STATE]
        self.v_timer = CYCLE_TIMES[RED_STATE]

    def set_emergency(self):
        self.mode = "EMERGENCY"
        self.h_state = GREEN_STATE
        self.v_state = RED_STATE
        self.h_timer = 999
        self.v_timer = 999

    def restore_normal(self):
        self.mode = "NORMAL"
        self.h_state = GREEN_STATE
        self.v_state = RED_STATE
        self.h_timer = CYCLE_TIMES[GREEN_STATE]
        self.v_timer = CYCLE_TIMES[RED_STATE]

    def update(self):
        if self.mode == "EMERGENCY": return
        self.h_timer -= 1
        if self.h_timer <= 0:
            self.h_state = (self.h_state + 1) % 3
            self.h_timer = CYCLE_TIMES[self.h_state]
        self.v_timer -= 1
        if self.v_timer <= 0:
            self.v_state = (self.v_state + 1) % 3
            self.v_timer = CYCLE_TIMES[self.v_state]

    def draw(self, surface):
        box_w, box_h = 28, 70
        # 4 Signal Positions: Top-Left, Top-Right, Bottom-Left, Bottom-Right
        # Each direction checks its "near right" light.
        positions = [
            (CX - ROAD_W - 40, CY - ROAD_W - 80, self.h_state, self.h_timer, "H_TL"), # Top-Left (for Right-bound)
            (CX + ROAD_W + 10, CY - ROAD_W - 80, self.v_state, self.v_timer, "V_TR"), # Top-Right (for Down-bound)
            (CX - ROAD_W - 40, CY + ROAD_W + 10, self.v_state, self.v_timer, "V_BL"), # Bottom-Left (for Up-bound)
            (CX + ROAD_W + 10, CY + ROAD_W + 10, self.h_state, self.h_timer, "H_BR")  # Bottom-Right (for Left-bound)
        ]
        for sx, sy, state, timer, label_id in positions:
            DDA_thick_line(surface, sx + box_w // 2, sy + box_h, sx + box_w // 2, sy + box_h + 20, DARK_GRAY, 4)
            surface.fill(SIGNAL_BOX, (sx, sy, box_w, box_h))
            
            r_col = RED if state == RED_STATE else (80, 0, 0)
            y_col = YELLOW if state == YELLOW_STATE else (80, 80, 0)
            g_col = GREEN if state == GREEN_STATE else (0, 80, 0)
            
            filled_midpoint_circle(surface, sx + box_w // 2, sy + 14, 8, r_col)
            filled_midpoint_circle(surface, sx + box_w // 2, sy + 35, 8, y_col)
            filled_midpoint_circle(surface, sx + box_w // 2, sy + 56, 8, g_col)
            
            font = pygame.font.SysFont("monospace", 14, bold=True)
            label = "EM" if self.mode == "EMERGENCY" else str(timer // 60 + 1)
            txt = font.render(label, True, WHITE)
            surface.blit(txt, (sx + 5, sy - 18))

# ──────────────────────────────────────────────────────────────────────────────
# VEHICLE CLASS
# ──────────────────────────────────────────────────────────────────────────────

class Vehicle:
    def __init__(self, x, y, direction, is_ambulance=False):
        self.x = float(x)
        self.y = float(y)
        self.direction = direction
        self.is_ambulance = is_ambulance
        # REDUCED NORMAL SPEED (from 6.0 to 4.5)
        self.speed = 10.0 if is_ambulance else 4.5
        self.color = WHITE if is_ambulance else BLUE
        self.active = True
        self.entered_junction = False

    def update(self, signal_ctrl, all_vehicles):
        # Determine the appropriate light state based on direction ("near right")
        can_move = False
        if self.direction == "right":
            can_move = (signal_ctrl.h_state == GREEN_STATE)
        elif self.direction == "left":
            can_move = (signal_ctrl.h_state == GREEN_STATE)
        elif self.direction == "down":
            can_move = (signal_ctrl.v_state == GREEN_STATE)
        elif self.direction == "up":
            can_move = (signal_ctrl.v_state == GREEN_STATE)

        # JUNCTION CLEARING: If already in junction, ignore light
        if self.entered_junction:
            can_move = True

        # Determine stop condition (signal or queuing)
        stop = False
        buffer = self.speed + 2
        
        # 1. Signal Stop Check
        if not (can_move or self.is_ambulance):
            if self.direction == "right" and self.x + 60 >= CX - ROAD_W - buffer and self.x < CX - ROAD_W: stop = True
            if self.direction == "left" and self.x <= CX + ROAD_W + buffer and self.x > CX + ROAD_W: stop = True
            if self.direction == "down" and self.y + 60 >= CY - ROAD_W - buffer and self.y < CY - ROAD_W: stop = True
            if self.direction == "up" and self.y <= CY + ROAD_W + buffer and self.y > CY + ROAD_W: stop = True

        # 2. Queuing Stop Check (Don't hit car in front)
        if not stop:
            safe_dist = 20  # Minimal gap between vehicles
            for other in all_vehicles:
                if other is self or not other.active: continue
                if other.direction != self.direction: continue
                
                if self.direction == "right":
                    if 0 < (other.x - (self.x + 60)) < safe_dist: stop = True
                elif self.direction == "left":
                    if 0 < (self.x - (other.x + 60)) < safe_dist: stop = True
                elif self.direction == "down":
                    if 0 < (other.y - (self.y + 60)) < safe_dist: stop = True
                elif self.direction == "up":
                    if 0 < (self.y - (other.y + 60)) < safe_dist: stop = True
                if stop: break

        # Mark as entered junction once past the stop line
        if not self.entered_junction:
            if self.direction == "right" and self.x > CX - ROAD_W: self.entered_junction = True
            elif self.direction == "left" and self.x + 60 < CX + ROAD_W: self.entered_junction = True
            elif self.direction == "down" and self.y > CY - ROAD_W: self.entered_junction = True
            elif self.direction == "up" and self.y + 60 < CY + ROAD_W: self.entered_junction = True

        if not stop:
            if self.direction == "right": self.x += self.speed
            elif self.direction == "left": self.x -= self.speed
            elif self.direction == "down": self.y += self.speed
            elif self.direction == "up": self.y -= self.speed

        if self.x > WIDTH + 100 or self.x < -100 or self.y > HEIGHT + 100 or self.y < -100:
            self.active = False

    def draw(self, surface, siren_on=False):
        ox, oy = int(self.x), int(self.y)
        if self.direction in ("right", "left"):
            w, h = 60, 30
            surface.fill(self.color, (ox, oy, w, h))
            pygame.draw.rect(surface, BLACK, (ox, oy, w, h), 1)
            filled_midpoint_circle(surface, ox + 15, oy + h, 8, DARK_GRAY)
            filled_midpoint_circle(surface, ox + 45, oy + h, 8, DARK_GRAY)
            if self.is_ambulance:
                DDA_thick_line(surface, ox + w // 2, oy + 5, ox + w // 2, oy + h - 5, RED, 4)
                DDA_thick_line(surface, ox + 10, oy + h // 2, ox + w - 10, oy + h // 2, RED, 4)
                s_col = RED if siren_on else BLUE
                filled_midpoint_circle(surface, ox + w // 2, oy - 5, 5, s_col)
        else:
            w, h = 30, 60
            surface.fill(self.color, (ox, oy, w, h))
            pygame.draw.rect(surface, BLACK, (ox, oy, w, h), 1)
            filled_midpoint_circle(surface, ox, oy + 15, 8, DARK_GRAY)
            filled_midpoint_circle(surface, ox, oy + 45, 8, DARK_GRAY)
            if self.is_ambulance:
                DDA_thick_line(surface, ox + w // 2, oy + 10, ox + w // 2, oy + h - 10, RED, 4)
                DDA_thick_line(surface, ox + 5, oy + h // 2, ox + w - 5, oy + h // 2, RED, 4)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Emergency Vehicle Priority System - CGIP Implementation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16, bold=True)

    vehicles = []
    signal = SignalController()
    frame = 0
    siren_on = False
    
    # Pre-render background
    static_bg = create_static_background()

    running = True
    while running:
        clock.tick(FPS)
        frame += 1
        if frame % 15 == 0: siren_on = not siren_on

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: running = False
                # Manual spawning
                if event.key == pygame.K_h: vehicles.append(Vehicle(-60, CY - 40, "right"))
                if event.key == pygame.K_j: vehicles.append(Vehicle(WIDTH, CY + 10, "left"))
                if event.key == pygame.K_v: vehicles.append(Vehicle(CX + 10, -60, "down"))
                if event.key == pygame.K_b: vehicles.append(Vehicle(CX - 40, HEIGHT, "up"))
                # Emergency spawning
                if event.key == pygame.K_e:
                    vehicles.append(Vehicle(-80, CY - 40, "right", True))
                    signal.set_emergency()
                # Reset
                if event.key == pygame.K_r:
                    vehicles.clear()
                    signal.restore_normal()

        signal.update()
        
        # Check if ambulance passed intersection to clear emergency
        has_ambulance = any(v.is_ambulance and v.active for v in vehicles)
        if signal.mode == "EMERGENCY" and not has_ambulance:
            signal.restore_normal()
        elif signal.mode == "EMERGENCY":
            # Extra check: if ambulance is well past the crossing, can restore early
            for v in vehicles:
                if v.is_ambulance and v.x > CX + ROAD_W:
                    signal.restore_normal()
                    break

        # Move vehicles
        for v in vehicles:
            v.update(signal, vehicles)

        # Draw
        screen.blit(static_bg, (0, 0)) # Use cached background
        signal.draw(screen)
        for v in vehicles:
            v.draw(screen, siren_on)

        # HUD
        pygame.draw.rect(screen, (50, 50, 50), (10, 10, 420, 100))
        screen.blit(font.render(f"SYSTEM MODE: {signal.mode}", True, RED if signal.mode == "EMERGENCY" else GREEN), (20, 20))
        screen.blit(font.render("H: Spawn Right  J: Spawn Left", True, WHITE), (20, 45))
        screen.blit(font.render("V: Spawn Down   B: Spawn Up", True, WHITE), (20, 65))
        screen.blit(font.render("E: Emergency    R: Reset    Q: Quit", True, YELLOW), (20, 85))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

import pygame
import os
import sys
import json
import time
import requests

# ====== 設定路徑 ======
ASSET_DIR = "assets"
BG_DIR = os.path.join(ASSET_DIR, "bg")
CHAR_DIR = os.path.join(ASSET_DIR, "characters")
SFX_DIR = os.path.join(ASSET_DIR, "sfx")
TEXTBOX_IMG = pygame.image.load(os.path.join(ASSET_DIR, "textbox.png"))
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SCRIPT_PATH = os.path.join(ASSET_DIR, "story.json")
PI_IP = "192.168.1.100"

# ====== 初始化 ======
pygame.init()
screen = pygame.display.set_mode((540, 360))
font = pygame.font.Font(FONT_PATH, 20)
clock = pygame.time.Clock()

# ====== 劇情資料 ======
def load_script(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

script = load_script(SCRIPT_PATH)

# ====== 狀態 ======
current_id = "start"
choosing = False
choice_buttons = []
typed_text = ""
char_index = 0
type_timer = 0
type_delay = 30
image_cache = {}

# ====== 戰鬥狀態 ======
player_hp = 100
enemy_hp = -233
battle_options = [("攻擊", "attack"), ("魔法", "magic")]
selected_battle_action = None

# ====== 工具函式 ======
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    return lines

def draw_character(img_name, pos):
    if img_name:
        if img_name not in image_cache:
            image_cache[img_name] = pygame.image.load(os.path.join(CHAR_DIR, img_name))
        img = image_cache[img_name]
        rect = img.get_rect()
        if pos == "left":
            rect.midbottom = (140, 300)
        else:
            rect.midbottom = (400, 300)
        screen.blit(img, rect)

def draw_textbox(speaker, full_text):
    global typed_text, char_index, type_timer

    screen.blit(TEXTBOX_IMG, (0, 240))
    speaker_text = font.render(f"{speaker}：", True, (255, 255, 0))
    screen.blit(speaker_text, (30, 220))

    now = pygame.time.get_ticks()
    if char_index < len(full_text) and now - type_timer > type_delay:
        typed_text += full_text[char_index]
        char_index += 1
        type_timer = now

    wrapped = wrap_text(typed_text, font, 460)
    for i, line in enumerate(wrapped):
        surface = font.render(line, True, (255, 255, 255))
        screen.blit(surface, (30, 255 + i * 24))

def draw_choices(choices_dict):
    global choice_buttons
    choice_buttons = []
    y = 260
    mouse_pos = pygame.mouse.get_pos()

    for text, target_id in choices_dict.items():
        rect = pygame.Rect(40, y, 460, 30)
        is_hovered = rect.collidepoint(mouse_pos)
        bg_color = (100, 100, 180) if is_hovered else (70, 70, 130)
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=6)
        line = font.render(text, True, (255, 255, 255))
        screen.blit(line, (rect.x + 10, rect.y + 5))
        choice_buttons.append((rect, target_id))
        y += 40

def draw_battle():
    global choice_buttons
    choice_buttons = []
    screen.blit(TEXTBOX_IMG, (0, 240))
    hp_text = font.render(f"凱恩 HP: {player_hp}    巨龍 HP: {enemy_hp}", True, (255, 255, 255))
    screen.blit(hp_text, (30, 220))

    y = 270
    mouse_pos = pygame.mouse.get_pos()
    for label, action in battle_options:
        rect = pygame.Rect(40, y, 460, 30)
        is_hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (100, 0, 0) if is_hovered else (70, 0, 0), rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=6)
        text_surface = font.render(label, True, (255, 255, 255))
        screen.blit(text_surface, (rect.x + 10, rect.y + 5))
        choice_buttons.append((rect, action))
        y += 40

def player_turn(action):
    global enemy_hp
    dmg = 0
    if action == "attack":
        response = requests.get(f"http://{PI_IP}:5000/slash")
        dmg = float(response.text)
        enemy_hp -= dmg
    elif action == "magic":
        response = requests.get(f"http://{PI_IP}:5000/magic")
        dmg = float(response.text)
        enemy_hp -= dmg

def dragon_turn():
    global player_hp
    player_hp -= 25

# ====== 主迴圈 ======
running = True
while running:
    screen.fill((0, 0, 0))

    # 判斷離開
    if current_id == 'quit':
        running = False

    # 遊戲開始
    if current_id == 'start':
        player_hp = 100

    
    # 取得現在 id 的 json
    node = script[current_id]

    # 畫背景
    bg_img = node.get("bg")
    if bg_img:
        if bg_img not in image_cache:
            image_cache[bg_img] = pygame.image.load(os.path.join(BG_DIR, bg_img))
        screen.blit(image_cache[bg_img], (0, 0))
    
    # 畫人物
    draw_character(node.get("left"), "left")
    draw_character(node.get("right"), "right")

    if node.get("battle"):
        enemy_hp = float(node.get("enemy_hp")) if (enemy_hp == -233) else enemy_hp
        draw_battle()
        if enemy_hp <= 0:
            current_id = node.get("victory")
            enemy_hp = -233
        elif player_hp <= 0:
            current_id = node.get("defeat")
            enemy_hp = -233
    else:
        if "choice" in node:
            choosing = True
            screen.blit(TEXTBOX_IMG, (0, 240))
            draw_choices(node["choice"])
        else:
            choosing = False
            draw_textbox(node["speaker"], node["text"])

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if choosing:
                for rect, target_id in choice_buttons:
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        current_id = target_id
                        typed_text = ""
                        char_index = 0
                        choosing = False
                        break
            elif node.get("battle"):
                for rect, action in choice_buttons:
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        player_turn(action)
                        if enemy_hp > 0:
                            pygame.time.delay(500)
                            dragon_turn()
                        break
            else:
                if "text" in script[current_id] and char_index < len(script[current_id]["text"]):
                    typed_text = script[current_id]["text"]
                    char_index = len(typed_text)
                elif "next" in script[current_id]:
                    current_id = script[current_id]["next"]
                    typed_text = ""
                    char_index = 0

    clock.tick(60)

pygame.quit()
sys.exit()

import pygame
import os
import sys
import json
import requests

# ====== 設定路徑 ======
ASSET_DIR = "assets"
BG_DIR = os.path.join(ASSET_DIR, "bg")
CHAR_DIR = os.path.join(ASSET_DIR, "characters")
SFX_DIR = os.path.join(ASSET_DIR, "sfx")
TEXTBOX_IMG = pygame.image.load(os.path.join(ASSET_DIR, "textbox.png"))
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SCRIPT_PATH = os.path.join(ASSET_DIR, "main.json")
PI_IP = "192.168.137.46"

# ====== 初始化 ======
pygame.init()
pygame.mixer.init()
pygame.mixer.music.set_volume(1)
voice_channel = pygame.mixer.Channel(0)
screen = pygame.display.set_mode((1280, 720))
# font = pygame.font.Font(FONT_PATH, 36)
font = pygame.font.SysFont("Microsoft JhengHei", 36, True)
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
voice_active = True

# ====== 戰鬥狀態 ======
player_hp = 100
enemy_name = ""
enemy_hp = -233
enemy_dmg = -233
battle_options = [("攻擊", "attack"), ("魔法", "magic")]
selected_battle_action = None

# ====== Scanning 狀態 ======
scan_active = False
scan_success = False
scan_attempt = False
scan_next_id = ""

# ====== Lock Picking 狀態 ======
lock_picking_active = False
lock_attempts = 0
lock_success = False
lock_max_attempts = 5
lock_next_id = ""
lock_fail_id = ""

# ====== 工具函式 ======
def play_voice(filename):
    sound = pygame.mixer.Sound(os.path.join(SFX_DIR, filename))
    voice_channel.stop()  # 先停止之前的語音
    voice_channel.play(sound)

def wrap_text(text, font, max_width):
    lines = []
    paragraphs = text.split("\n")
    for paragraph in paragraphs:
        words = paragraph
        current_line = ""
        for word in words:
            test_line = current_line + word
            if font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word
        lines.append(current_line.strip())
    return lines

def draw_character(img_name, x=0, y=0):
    if img_name:
        if img_name not in image_cache:
            image_cache[img_name] = pygame.image.load(os.path.join(CHAR_DIR, img_name))
        img = image_cache[img_name]
        rect = img.get_rect()
        rect.midbottom = (x, y)
        screen.blit(img, rect)

def draw_textbox(speaker, full_text):
    global typed_text, char_index, type_timer

    screen.blit(TEXTBOX_IMG, (0, 520))
    speaker_text = font.render(f"{speaker}：", True, (255, 255, 0))
    screen.blit(speaker_text, (40, 480))

    now = pygame.time.get_ticks()
    if char_index < len(full_text) and now - type_timer > type_delay:
        typed_text += full_text[char_index]
        char_index += 1
        type_timer = now

    wrapped = wrap_text(typed_text, font, 1160)
    for i, line in enumerate(wrapped):
        surface = font.render(line, True, (255, 255, 255))
        screen.blit(surface, (40, 560 + i * 40))

def draw_choices(choices_dict):
    global choice_buttons
    choice_buttons = []
    y = 560
    mouse_pos = pygame.mouse.get_pos()

    for text, target_id in choices_dict.items():
        rect = pygame.Rect(60, y, 1160, 50)
        is_hovered = rect.collidepoint(mouse_pos)
        bg_color = (100, 100, 180) if is_hovered else (70, 70, 130)
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        line = font.render(text, True, (255, 255, 255))
        screen.blit(line, (rect.x + 10, rect.y + 8))
        choice_buttons.append((rect, target_id))
        y += 60

def draw_battle():
    global choice_buttons
    choice_buttons = []
    screen.blit(TEXTBOX_IMG, (0, 520))
    hp_text = font.render(f"庫柏 HP: {player_hp}    {enemy_name} HP: {enemy_hp}", True, (255, 255, 255))
    screen.blit(hp_text, (40, 480))

    y = 560
    mouse_pos = pygame.mouse.get_pos()
    for label, action in battle_options:
        rect = pygame.Rect(60, y, 1160, 50)
        is_hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (100, 0, 0) if is_hovered else (70, 0, 0), rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        text_surface = font.render(label, True, (255, 255, 255))
        screen.blit(text_surface, (rect.x + 20, rect.y + 8))
        choice_buttons.append((rect, action))
        y += 60

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

def enemy_turn():
    global player_hp
    player_hp -= enemy_dmg

def reset_battle():
    global enemy_hp, enemy_dmg
    enemy_hp = -233
    enemy_dmg = -233

def start_lock_picking(success_target, fail_target):
    global lock_picking_active, lock_attempts, lock_success, lock_next_id, lock_fail_id
    lock_picking_active = True
    lock_attempts = 0
    lock_success = False
    lock_next_id = success_target
    lock_fail_id = fail_target

def draw_lock_picking():
    global lock_attempts
    screen.blit(TEXTBOX_IMG, (0, 520))
    status = "開鎖成功！" if lock_success else f"開鎖中...（{lock_attempts}/{lock_max_attempts}）"
    text_surface = font.render(status, True, (255, 255, 255))
    screen.blit(text_surface, (40, 560))
    button_rect = pygame.Rect(460, 610, 360, 50)
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = button_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (100, 100, 0) if is_hovered else (70, 70, 0), button_rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2, border_radius=8)
    btn_text = font.render("嘗試開鎖", True, (255, 255, 255))
    screen.blit(btn_text, (button_rect.x + 100, button_rect.y + 8))
    return button_rect

def start_scanning(success_target):
    global scan_active, scan_success, scan_next_id
    scan_active = True
    scan_success = False
    scan_next_id = success_target


def draw_scanning():
    screen.blit(TEXTBOX_IMG, (0, 520))
    status = "(請靠近一點)" if scan_attempt else "(請將手放在感應器上)"
    text_surface = font.render(status, True, (255, 255, 255))
    screen.blit(text_surface, (40, 560))
    button_rect = pygame.Rect(460, 610, 360, 50)
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = button_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (100, 100, 0) if is_hovered else (70, 70, 0), button_rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2, border_radius=8)
    btn_text = font.render("掃描", True, (255, 255, 255))
    screen.blit(btn_text, (button_rect.x + 100, button_rect.y + 8))
    return button_rect

# ====== 主迴圈 ======
running = True
while running:
    screen.fill((0, 0, 0))

    # 判斷離開
    if current_id == 'quit':
        running = False
        break

    # 遊戲開始
    if current_id == 'start':
        player_hp = 100

    
    # 取得現在 id 的 json
    node = script[current_id]

    # 開鎖
    if "lock_event" in node and not lock_picking_active:
            success = node["lock_event"]["success"]
            fail = node["lock_event"]["fail"]
            start_lock_picking(success, fail)
    
    # 掃描
    if "scan_event" in node and not scan_active:
        success = node["scan_event"]["next"]
        start_scanning(success)


    # 畫背景
    bg_img = node.get("bg")
    if bg_img:
        if bg_img not in image_cache:
            image_cache[bg_img] = pygame.image.load(os.path.join(BG_DIR, bg_img))
        screen.blit(image_cache[bg_img], (0, 0))
    
    # 畫人物
    draw_character(node.get("left"), node.get("lx"), node.get("ly"))
    draw_character(node.get("right"), node.get("rx"), node.get("ry"))

    # 播聲音
    voice = script[current_id].get("voice")
    if voice and voice_active:
        voice_active = False
        play_voice(voice)

    if battle := node.get("battle"):
        enemy_name = battle["enemy_name"]
        enemy_hp = float(battle["enemy_hp"]) if (enemy_hp == -233) else enemy_hp
        enemy_dmg = float(battle["enemy_dmg"]) if (enemy_dmg == -233) else enemy_dmg
        battle_options = battle["options"]
        draw_battle()
        if enemy_hp <= 0:
            current_id = battle["victory"]
            voice_active = True
            reset_battle()
        elif player_hp <= 0:
            current_id = battle["defeat"]
            voice_active = True
            reset_battle()
    elif lock_picking_active:
        lock_button = draw_lock_picking()
        if lock_success:
            pygame.time.delay(1000)
            current_id = lock_next_id
            lock_picking_active = False
            voice_active = True
        elif lock_attempts >= lock_max_attempts:
            pygame.time.delay(1000)
            current_id = lock_fail_id
            lock_picking_active = False
            voice_active = True
    elif scan_active:
        scan_button = draw_scanning()
        if scan_success:
            pygame.time.delay(1000)
            current_id = scan_next_id
            scan_active = False
            scan_attempt = False
            voice_active = True
    else:
        if "choice" in node:
            choosing = True
            screen.blit(TEXTBOX_IMG, (0, 520))
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
                        voice_active = True
                        break
            elif node.get("battle"):
                for rect, action in choice_buttons:
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        player_turn(action)
                        if enemy_hp > 0:
                            pygame.time.delay(500)
                            enemy_turn()
                        break
            elif lock_picking_active:
                if lock_button.collidepoint(pygame.mouse.get_pos()) and lock_attempts < lock_max_attempts:
                    lock_attempts += 1
                    try:
                        response = requests.get(f"http://{PI_IP}:5000/lockpick")
                        if response.status_code == 200 and response.text.strip() == "1":
                            lock_success = True
                    except:
                        print("無法連線到伺服器")
            elif scan_active:
                if scan_button.collidepoint(pygame.mouse.get_pos()):
                    try:
                        response = requests.get(f"http://{PI_IP}:5000/scan")
                        if response.status_code == 200 and response.text.strip() == "1":
                            scan_success = True
                        else:
                            scan_attempt = True
                    except:
                        print("無法連線到伺服器")
            else:
                if "text" in script[current_id] and char_index < len(script[current_id]["text"]):
                    typed_text = script[current_id]["text"]
                    char_index = len(typed_text)
                elif "next" in script[current_id]:
                    current_id = script[current_id]["next"]
                    typed_text = ""
                    char_index = 0
                    voice_active = True

    clock.tick(60)

pygame.quit()
sys.exit()

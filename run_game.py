import pgzrun
import math
import random
from pygame.rect import Rect

# --- Configurações da Janela ---
WIDTH = 800
HEIGHT = 600
TITLE = "Jumper"

# --- Constantes do Jogo e Física ---
WORLD_WIDTH = 4500 
# AJUSTE DE FÍSICA PARA PULO CLÁSSICO
GRAVITY = 0.8        
JUMP_STRENGTH = -18  
PLAYER_SPEED = 5
MAX_FALL_SPEED = 15
ENEMY_SPEED = 2.5 
BAT_Y_SPEED = 0.05 
CHASE_RADIUS = 500 

# --- CONSTANTES DE DIMENSÃO ---
GROUND_THICKNESS = 50 
PLATFORM_THICKNESS = 20 
BLOCK_WIDTH = 50        
# Variáveis GLOBAIS DO CASTELO
CASTLE_WIDTH = 4 * BLOCK_WIDTH
CASTLE_HEIGHT = 3 * BLOCK_WIDTH

# --- Configurações da Câmera ---
SCROLL_SPEED = PLAYER_SPEED 
SCROLL_THRESHOLD = 200 

# --- Cores (RGB) ---
GROUND_COLOR = (34, 139, 34) 
ELEVATED_PLATFORM_COLOR = (139, 69, 19) 
PIPE_COLOR = (0, 150, 0) 
WIN_ZONE_COLOR = (255, 255, 0) 
SKY_COLOR = (135, 206, 235) 
MENU_COLOR = (20, 20, 50) 
WIN_COLOR = (34, 139, 34) 
BUTTON_COLOR = (50, 50, 80)
HIGHLIGHT_COLOR = (100, 100, 150)
TEXT_COLOR = (255, 255, 255) 

# --- Variáveis do Jogo ---
player = None
platforms = [] 
enemies = [] 
win_zone = None 
player_y_velocity = 0
is_jumping = False
on_ground = False
score = 0
world_offset_x = 0
CASTLE_BASE_X = 0 
CASTLE_BASE_Y = 0 

# --- Variáveis de Som (Carregamento Corrigido) ---
jump_sound = None
kill_sound = None 
death_sound = None 
tap_sound = None 
victory_sound = None 

# --- Variáveis de Animação ---
player_animation_state = 'idle' 
player_frame_index = 0
player_animation_timer = 0
ANIMATION_SPEED = 0.15 
PLAYER_ANIMATIONS = {
    'idle': ['player_idle1', 'player_idle2', 'player_idle3', 'player_idle4'],
    'walk': ['player_walk1', 'player_walk2', 'player_walk3', 'player_walk4', 'player_walk5'], 
    'jump': ['player_jump']
}

# --- Variáveis do Menu/Estado ---
game_state = 'MENU' 
sound_on = True 
MUSIC_FILE = 'time_for_adventure.mp3'

# --- Botões do Menu (Rects para detecção de clique) ---
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_Y_START = HEIGHT // 2 - 150
BUTTON_GAP = 70 
BUTTONS = {
    'JOGAR': Rect(WIDTH // 2 - BUTTON_WIDTH // 2, BUTTON_Y_START + BUTTON_GAP * 0, BUTTON_WIDTH, BUTTON_HEIGHT),
    'TUTORIAL': Rect(WIDTH // 2 - BUTTON_WIDTH // 2, BUTTON_Y_START + BUTTON_GAP * 1, BUTTON_WIDTH, BUTTON_HEIGHT),
    'SOM': Rect(WIDTH // 2 - BUTTON_WIDTH // 2, BUTTON_Y_START + BUTTON_GAP * 2, BUTTON_WIDTH, BUTTON_HEIGHT),
    'SAIR': Rect(WIDTH // 2 - BUTTON_WIDTH // 2, BUTTON_Y_START + BUTTON_GAP * 3, BUTTON_WIDTH, BUTTON_HEIGHT),
}

# --- Classe Inimigo (Morcego Corrigido) ---
class Enemy(Actor):
    def __init__(self, x, y, speed, image_prefix='enemy_an', num_frames=4):
        super().__init__(f'{image_prefix}1') 
        self.x = x
        self.y = y
        self.speed = speed
        self.x_velocity = 0 
        self.y_velocity = 0 
        self.on_ground = False 
        self.old_x = x # Adicionado para rastrear a posição anterior para colisão
        
        self.walk_frames = [f'{image_prefix}{i}' for i in range(1, num_frames + 1)]
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.15 
        self.facing_right = True
        
        self.initial_y = y 

    def pursue_player(self, player_actor, world_offset):
        """
        Faz o morcego perseguir o player, simplificando a direção Y 
        para que ele respeite melhor as plataformas.
        """
        
        enemy_world_x = self.x
        enemy_screen_y = self.y 
        
        player_world_x = player_actor.x + world_offset
        player_screen_y = player_actor.y
        
        delta_x = player_world_x - enemy_world_x
        delta_y = player_screen_y - enemy_screen_y
        
        distance = math.sqrt(delta_x**2 + delta_y**2)
        
        if distance < CHASE_RADIUS:
            if distance > 1: 
                # Movimento X (Completamente horizontal)
                self.x_velocity = (delta_x / distance) * self.speed
                
                # Movimento Y (Apenas flutuar e tentar se aproximar verticalmente)
                if abs(delta_y) > 10: # Se o player estiver significativamente mais alto/baixo
                     self.y_velocity = (delta_y / distance) * self.speed * 0.5 
                else:
                     self.y_velocity = 0 
                
                self.facing_right = self.x_velocity > 0
            
            elif distance > 0:
                 self.x_velocity = 0
                 self.y_velocity = 0
                 
        else:
            self.x_velocity = 0
            self.y_velocity = 0
        
    def update_movement(self):
        """Atualiza a posição do inimigo e animação, guardando a posição X anterior."""
        self.old_x = self.x 
        
        self.x += self.x_velocity
        self.y += self.y_velocity 
        
        # Limita o voo vertical
        self.y = max(min(self.y, HEIGHT - 50), 50) 

        self.animation_timer += 0.05 
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.walk_frames)
        
        self.image = self.walk_frames[self.frame_index]
        self.image_flip = not self.facing_right

    def update_collision(self, platforms_rects):
        """
        Implementa colisão vertical e horizontal básica para impedir o morcego de atravessar plataformas.
        """
        
        # O Rect do inimigo (em coordenadas do mundo)
        enemy_rect_world = Rect(self.x - self.width / 2, self.y - self.height / 2, self.width, self.height)
        
        for p_world in platforms_rects:
            
            if enemy_rect_world.colliderect(p_world):
                
                # --- Colisão Vertical (Atingindo por Cima ou por Baixo) ---
                
                # Bateu por baixo e está subindo (voando para cima)
                if self.y_velocity < 0 and enemy_rect_world.top < p_world.bottom and self.y > p_world.centery:
                    self.y_velocity = 0
                    self.y = p_world.bottom + self.height / 2 
                    
                # Bateu por cima e está descendo (voando para baixo / pousando)
                elif self.y_velocity > 0 and enemy_rect_world.bottom > p_world.top and self.y < p_world.centery:
                    self.y_velocity = 0
                    self.y = p_world.top - self.height / 2
                    
                
                # --- Colisão Horizontal (Atingindo por Lados) ---
                # Verifica a colisão horizontal apenas se não for uma colisão de topo/fundo muito agressiva.
                if self.y_velocity == 0 or (enemy_rect_world.centery > p_world.top + 5 and enemy_rect_world.centery < p_world.bottom - 5):
                    
                    # Bateu pela direita e está indo para a esquerda
                    if self.x < self.old_x and enemy_rect_world.left < p_world.right and enemy_rect_world.right > p_world.right:
                        self.x = p_world.right + self.width / 2 
                        self.x_velocity = 0
                        
                    # Bateu pela esquerda e está indo para a direita
                    elif self.x > self.old_x and enemy_rect_world.right > p_world.left and enemy_rect_world.left < p_world.left:
                        self.x = p_world.left - self.width / 2 
                        self.x_velocity = 0
        

# --- Funções de Áudio (Mantidas) ---

def play_music():
    """Toca a música de fundo se o som estiver ligado."""
    if sound_on:
        music.play(MUSIC_FILE) 
    else:
        music.stop()

def play_sound(s):
    """Toca um som se o som estiver ligado e o som existir."""
    if sound_on and s:
        s.play()

# --- Inicialização do Jogo (Corrigida e Limpa) ---

def init_game():
    """Inicializa o jogador, plataformas, inimigos e carrega os sons."""
    global player, player_y_velocity, is_jumping, score, platforms, world_offset_x, player_animation_state, player_frame_index, player_animation_timer, win_zone, enemies
    global jump_sound, kill_sound, death_sound, tap_sound, victory_sound
    global CASTLE_BASE_X, CASTLE_BASE_Y 
    
    world_offset_x = 0

    try:
    
        jump_sound = sounds.jump
        kill_sound = sounds.kill 
        death_sound = sounds.death 
        tap_sound = sounds.tap 
        victory_sound = sounds.victory 
        
        print("Todos os sons (.wav) carregados com sucesso! Verifique a pasta 'sounds'.")
    
    except AttributeError as e:
        print(f"ERRO CRÍTICO DE SOM: Falha ao encontrar um ou mais sons. Verifique se os arquivos SÃO EXATAMENTE: jump.wav, kill.wav, death.wav, tap.wav, victory.wav. Erro: {e}")
        # Desliga todos os sons como fallback
        jump_sound, kill_sound, death_sound, tap_sound, victory_sound = (None,) * 5
    
    # 1. Jogador
    player = Actor(PLAYER_ANIMATIONS['idle'][0]) 
    player.left = 50 
    player.y = HEIGHT - 100
    player_y_velocity = 0
    is_jumping = False
    score = 0
    player_animation_state = 'idle' 
    player_frame_index = 0
    player_animation_timer = 0

    # 2. Plataformas (Coordenadas no MUNDO/Nível - MANTIDAS)
    platforms = []
    GROUND_Y = HEIGHT - 50
    HEIGHT_ADJUSTMENT = 2 
    
    current_x = -50 
    
    platforms.append(Rect(current_x, GROUND_Y, 20 * BLOCK_WIDTH, GROUND_THICKNESS)) 
    PIPE_HEIGHT_1 = 2 * BLOCK_WIDTH 
    PIPE_Y_1 = GROUND_Y - PIPE_HEIGHT_1 + HEIGHT_ADJUSTMENT
    platforms.append(Rect(10 * BLOCK_WIDTH, PIPE_Y_1, 2 * BLOCK_WIDTH, PIPE_HEIGHT_1 - HEIGHT_ADJUSTMENT)) 
    PIPE_HEIGHT_2 = 3 * BLOCK_WIDTH
    PIPE_Y_2 = GROUND_Y - PIPE_HEIGHT_2 + HEIGHT_ADJUSTMENT
    platforms.append(Rect(16 * BLOCK_WIDTH, PIPE_Y_2, 2 * BLOCK_WIDTH, PIPE_HEIGHT_2 - HEIGHT_ADJUSTMENT)) 
    current_x += 20 * BLOCK_WIDTH 
    
    gap1_width = 3 * BLOCK_WIDTH 
    current_x += gap1_width 
    platforms.append(Rect(current_x, GROUND_Y, 18 * BLOCK_WIDTH, GROUND_THICKNESS)) 
    PIPE_HEIGHT_3 = 4 * BLOCK_WIDTH
    PIPE_Y_3 = GROUND_Y - PIPE_HEIGHT_3 + HEIGHT_ADJUSTMENT
    platforms.append(Rect(current_x + 8 * BLOCK_WIDTH, PIPE_Y_3, 2 * BLOCK_WIDTH, PIPE_HEIGHT_3 - HEIGHT_ADJUSTMENT)) 
    platforms.append(Rect(current_x + 15 * BLOCK_WIDTH, PIPE_Y_3, 2 * BLOCK_WIDTH, PIPE_HEIGHT_3 - HEIGHT_ADJUSTMENT)) 
    current_x += 18 * BLOCK_WIDTH 
    
    PLATFORM_Y = GROUND_Y - 4 * BLOCK_WIDTH
    platforms.extend([
        Rect(current_x + 2 * BLOCK_WIDTH, PLATFORM_Y, 3 * BLOCK_WIDTH, PLATFORM_THICKNESS), 
        Rect(current_x + 6 * BLOCK_WIDTH, PLATFORM_Y, 1 * BLOCK_WIDTH, PLATFORM_THICKNESS), 
        Rect(current_x + 10 * BLOCK_WIDTH, PLATFORM_Y, 1 * BLOCK_WIDTH, PLATFORM_THICKNESS), 
        Rect(current_x + 14 * BLOCK_WIDTH, PLATFORM_Y, 3 * BLOCK_WIDTH, PLATFORM_THICKNESS), 
    ])
    current_x += 20 * BLOCK_WIDTH 
    gap2_width = 1 * BLOCK_WIDTH 
    current_x += gap2_width 
    platforms.append(Rect(current_x, GROUND_Y, 20 * BLOCK_WIDTH, GROUND_THICKNESS))
    
    STAIR_START_X = current_x + 12 * BLOCK_WIDTH
    for i in range(1, 5): 
        platforms.append(Rect(
            STAIR_START_X + (i-1) * BLOCK_WIDTH, 
            GROUND_Y - i * BLOCK_WIDTH, 
            BLOCK_WIDTH, 
            i * BLOCK_WIDTH + GROUND_THICKNESS 
        ))
        
    current_x += 20 * BLOCK_WIDTH 

    platforms.append(Rect(current_x, GROUND_Y, WORLD_WIDTH - current_x + 50, GROUND_THICKNESS))
    
    CASTLE_BASE_X = WORLD_WIDTH - (8 * BLOCK_WIDTH) 
    CASTLE_BASE_Y = GROUND_Y - (3 * BLOCK_WIDTH)
    
    globals()['CASTLE_BASE_X'] = CASTLE_BASE_X
    globals()['CASTLE_BASE_Y'] = CASTLE_BASE_Y
    
    platforms.append(Rect(CASTLE_BASE_X, CASTLE_BASE_Y, CASTLE_WIDTH, CASTLE_HEIGHT)) 
    platforms.append(Rect(CASTLE_BASE_X + CASTLE_WIDTH - BLOCK_WIDTH, CASTLE_BASE_Y - 2*BLOCK_WIDTH, BLOCK_WIDTH, 2*BLOCK_WIDTH)) 
    
    win_zone = Rect(CASTLE_BASE_X + CASTLE_WIDTH / 2 - BLOCK_WIDTH / 2, CASTLE_BASE_Y - 4*BLOCK_WIDTH, BLOCK_WIDTH, BLOCK_WIDTH)
    platforms.append(win_zone) 

    # 3. Inimigos (5 inimigos, primeiro removido)
    enemies = []
    
    
    # [2] Morcego sobre o Cano 1 (x=550)
    enemies.append(Enemy(x=11 * BLOCK_WIDTH, y=PIPE_Y_1 - 50, speed=ENEMY_SPEED * 1.2, image_prefix='enemy_an')) 
    
    # [3] Morcego sobre Buraco 1 (x=1175)
    enemies.append(Enemy(x=20 * BLOCK_WIDTH + gap1_width/2, y=GROUND_Y - 100, speed=ENEMY_SPEED * 1.1, image_prefix='enemy_an')) 
    
    # [4] Morcego sobre o Cano 3 (mais alto) (x=1900)
    enemies.append(Enemy(x=current_x - (20 * BLOCK_WIDTH) + 9 * BLOCK_WIDTH, y=PIPE_Y_3 - 50, speed=ENEMY_SPEED * 1.5, image_prefix='enemy_an')) 
    
    # [5] Morcego na Plataforma Flutuante (x=2450)
    enemies.append(Enemy(x=current_x - 150, y=PLATFORM_Y - 50, speed=ENEMY_SPEED * 1.3, image_prefix='enemy_an'))
    
    # [6] Morcego perto do Castelo (x=WORLD_WIDTH - 550)
    enemies.append(Enemy(x=CASTLE_BASE_X - 150, y=GROUND_Y - 100, speed=ENEMY_SPEED * 1.2, image_prefix='enemy_an'))


# --- Funções de Áudio (Mantidas) ---

def play_music():
    """Toca a música de fundo se o som estiver ligado."""
    if sound_on:
        music.play(MUSIC_FILE) 
    else:
        music.stop()

def play_sound(s):
    """Toca um som se o som estiver ligado e o som existir."""
    if sound_on and s:
        s.play()

# --- Funções do Pygame Zero (Draw/Update) ---

def draw():
    if game_state == 'MENU':
        menu_draw()
    elif game_state == 'TUTORIAL':
        tutorial_draw()
    elif game_state == 'PLAYING':
        game_draw()
    elif game_state == 'WIN': 
        win_draw() 

def update():
    if game_state == 'PLAYING':
        handle_movement() 
        handle_gravity() 
        handle_collision()
        handle_camera() 
        update_enemies() 
        handle_enemy_collisions() 
        check_death()
        check_win() 
        animate_player() 

def on_mouse_down(pos):
    global game_state, sound_on
    
    if game_state == 'MENU':
        if BUTTONS['JOGAR'].collidepoint(pos):
            init_game() 
            game_state = 'PLAYING'
        elif BUTTONS['TUTORIAL'].collidepoint(pos):
            game_state = 'TUTORIAL'
        elif BUTTONS['SOM'].collidepoint(pos):
            sound_on = not sound_on 
            if sound_on:
                play_music() 
            else:
                music.stop()
        elif BUTTONS['SAIR'].collidepoint(pos):
            exit() 

    elif game_state == 'TUTORIAL' or game_state == 'WIN': 
        game_state = 'MENU'
        
def on_key_down(key):
    global on_ground, player_y_velocity, game_state
    
    if game_state == 'PLAYING':
        if key == keys.ESCAPE:
            game_state = 'MENU'

        
        if key == keys.SPACE and on_ground:
            player_y_velocity = JUMP_STRENGTH
            play_sound(jump_sound)

# --- Funções de Lógica do Jogo (Movimento, Colisão, Inimigos) ---

def handle_movement():
    global player
    
    old_x = player.x

    is_moving = False
    if keyboard.left:
        player.x -= PLAYER_SPEED
        is_moving = True
    elif keyboard.right:
        player.x += PLAYER_SPEED
        is_moving = True
        
    if world_offset_x == 0 and player.left < 0:
        player.left = 0
        
    for p in platforms:
        p_screen = Rect(p.left - world_offset_x, p.top, p.width, p.height)

        if player.colliderect(p_screen):
            # Correção de Colisão Horizontal
            if player.bottom > p_screen.top + 5 and player.top < p_screen.bottom - 5: 
                if player.x > old_x: 
                    player.right = p_screen.left
                elif player.x < old_x: 
                    player.left = p_screen.right

def handle_gravity():
    global player_y_velocity

    player_y_velocity += GRAVITY
    if player_y_velocity > MAX_FALL_SPEED:
        player_y_velocity = MAX_FALL_SPEED

    player.y += player_y_velocity

def handle_collision():
    global on_ground, player_y_velocity
    
    was_on_ground = on_ground
    on_ground = False
    
    for p in platforms:
        p_screen = Rect(p.left - world_offset_x, p.top, p.width, p.height)
        
        if player.colliderect(p_screen):
            # Colisão por Cima (Pouso)
            if player_y_velocity >= 0 and player.bottom <= p_screen.bottom: 
                player_y_velocity = 0
                player.bottom = p_screen.top 
                on_ground = True
            # Colisão por Baixo (Bater a cabeça)
            elif player_y_velocity < 0 and player.top >= p_screen.top:
                player_y_velocity = 0
                player.top = p_screen.bottom 

def update_enemies():
    """Atualiza o movimento e colisão de todos os inimigos."""
    for enemy in enemies:
        enemy.pursue_player(player, world_offset_x) 
        enemy.update_movement()
        enemy.update_collision(platforms) # Passa as plataformas em coordenadas do mundo
        
def handle_enemy_collisions():
    global enemies, game_state, player_y_velocity
    
    enemies_to_remove = []
    
    for enemy in enemies:
        enemy_screen_rect = Rect(enemy.left - world_offset_x, enemy.top, enemy.width, enemy.height)
        
        if player.colliderect(enemy_screen_rect):
            # 1. Pulo em Cima (Matar Inimigo)
            if player_y_velocity > 0 and player.bottom < enemy_screen_rect.centery + 10: 
                play_sound(kill_sound) 
                enemies_to_remove.append(enemy)
                
                player_y_velocity = JUMP_STRENGTH / 2 
                
            # 2. Colisão Lateral ou por Baixo (Morte Instantânea)
            else:
                play_sound(death_sound) 
                game_state = 'MENU' 
                return 

    for enemy in enemies_to_remove:
        enemies.remove(enemy)


def handle_camera():
    global world_offset_x
    
    max_offset = WORLD_WIDTH - WIDTH
    
    if keyboard.right:
        if player.right > WIDTH - SCROLL_THRESHOLD and world_offset_x < max_offset:
            world_offset_x += SCROLL_SPEED
            
            if world_offset_x > max_offset:
                world_offset_x = max_offset
            
            player.x -= SCROLL_SPEED
            
            if player.right > WIDTH - SCROLL_THRESHOLD:
                 player.right = WIDTH - SCROLL_THRESHOLD
            
    elif keyboard.left:
        if world_offset_x > 0:
            world_offset_x -= SCROLL_SPEED
            
            if world_offset_x < 0:
                world_offset_x = 0
            
            player.x += SCROLL_SPEED
            
            if player.left < SCROLL_THRESHOLD:
                player.left = SCROLL_THRESHOLD
                
    if world_offset_x == max_offset and player.right > WIDTH:
        player.right = WIDTH
            
def check_death():
    global game_state
    if player.top > HEIGHT:
        print("Game Over! Voltando ao Menu.")
        game_state = 'MENU'
        play_sound(death_sound) 

def check_win():
    global game_state
    
    player_screen_rect = Rect(player.left, player.top, player.width, player.height)
    win_zone_screen_rect = Rect(win_zone.left - world_offset_x, win_zone.top, win_zone.width, win_zone.height)

    if player_screen_rect.colliderect(win_zone_screen_rect):
        if game_state != 'WIN': 
            print("Vitória! Fase completa.")
            music.stop()
            play_sound(victory_sound)
            game_state = 'WIN'
        return

def set_player_animation_state(state):
    global player_animation_state, player_frame_index, player_animation_timer
    if player_animation_state != state:
        player_animation_state = state
        player_frame_index = 0 
        player_animation_timer = 0 

def animate_player():
    global player_frame_index, player_animation_timer, player_animation_state
    
    is_walking = keyboard.left or keyboard.right

    if not on_ground:
        set_player_animation_state('jump')
    elif is_walking:
        set_player_animation_state('walk')
        # Lógica para som de passo
        if player_animation_state == 'walk' and player_frame_index in [0, 2] and player_animation_timer == 0:
             play_sound(tap_sound)
    else:
        set_player_animation_state('idle')

    if player_animation_state == 'jump':
        player.image = PLAYER_ANIMATIONS['jump'][0]
        return 

    player_animation_timer += 0.05 / 3 

    if player_animation_timer >= ANIMATION_SPEED:
        player_animation_timer = 0
        player_frame_index = (player_frame_index + 1) % len(PLAYER_ANIMATIONS[player_animation_state])
    
    current_frame_name = PLAYER_ANIMATIONS[player_animation_state][player_frame_index]
    player.image = current_frame_name

    if keyboard.left:
        player.image_flip = True
    elif keyboard.right:
        player.image_flip = False

# --- Funções de Desenho ---

def menu_draw():
    screen.fill(MENU_COLOR)
    
    screen.draw.text("JUMPER", center=(WIDTH // 2, HEIGHT // 5),
                     fontsize=100, 
                     color=TEXT_COLOR)
    
    for label, rect in BUTTONS.items():
        screen.draw.filled_rect(rect, BUTTON_COLOR)
        
        text_label = label
        if label == 'SOM':
            text_label = f"SOM: {'LIGADO' if sound_on else 'DESLIGADO'}"
            
        screen.draw.text(text_label, center=rect.center, 
                         fontsize=30, 
                         color=TEXT_COLOR) 

def tutorial_draw():
    screen.fill(MENU_COLOR)
    
    screen.draw.text("TUTORIAL", center=(WIDTH // 2, HEIGHT // 8), 
                     fontsize=80, color=TEXT_COLOR)
                     
    tutorial_text = (
        "Mova-se com as setas esquerda e direita.\n"
        "Pule com a barra de espaço.\n"
        "Aperte a tecla ESC para acessar o Menu de pausa.\n\n"
        "Seu objetivo é chegar ao final da fase.\n"
        "Pule em cima dos inimigos para matá-los."
    )
    
    screen.draw.text(tutorial_text, center=(WIDTH // 2, HEIGHT // 2), 
                     fontsize=35, color=TEXT_COLOR, align='center')

def win_draw():
    screen.fill(WIN_COLOR)
    
    screen.draw.text("VITÓRIA!", center=(WIDTH // 2, HEIGHT // 3), 
                     fontsize=100, color=TEXT_COLOR)
                     
    screen.draw.text("Você alcançou o fim da fase!", center=(WIDTH // 2, HEIGHT // 2), 
                     fontsize=40, color=TEXT_COLOR)
                     
    screen.draw.text("Clique para voltar ao Menu", center=(WIDTH // 2, HEIGHT - 100), 
                     fontsize=30, color=(200, 200, 200))

def game_draw():
    screen.fill(SKY_COLOR)
    
    # 1. Desenha as plataformas de chão
    for p in platforms: 
        if p.height == GROUND_THICKNESS: 
            p_screen = Rect(p.left - world_offset_x, p.top, p.width, p.height)
            screen.draw.filled_rect(p_screen, GROUND_COLOR)
    
    # 2. Desenha as plataformas elevadas, canos e blocos finais
    for i, p in enumerate(platforms):
        # Filtra apenas as plataformas que NÃO são o chão principal ou a win_zone
        if p.height != GROUND_THICKNESS and p != win_zone: 
            p_screen = Rect(p.left - world_offset_x, p.top, p.width, p.height)
            
            # Canos são verdes
            if p.width == (2 * BLOCK_WIDTH) and p.height > (2 * PLATFORM_THICKNESS): 
                screen.draw.filled_rect(p_screen, PIPE_COLOR)
                screen.draw.filled_rect(Rect(p_screen.left, p_screen.top, p_screen.width, PLATFORM_THICKNESS), (0, 180, 0)) # Parte superior do cano
            # Plataformas flutuantes (Marrom fino)
            elif p.height == PLATFORM_THICKNESS:
                 screen.draw.filled_rect(p_screen, ELEVATED_PLATFORM_COLOR)
            # Escadas e Castelo são Marrom (mais espessos)
            else: 
                screen.draw.filled_rect(p_screen, ELEVATED_PLATFORM_COLOR)

    # A win_zone (Castelo) sempre desenhada por cima e em amarelo
    if win_zone:
        win_zone_screen = Rect(win_zone.left - world_offset_x, win_zone.top, win_zone.width, win_zone.height)
        screen.draw.filled_rect(win_zone_screen, WIN_ZONE_COLOR)

    # Desenha as partes do castelo separadamente para garantir a sobreposição
    for p in platforms:
        if p.x == CASTLE_BASE_X and p.y == CASTLE_BASE_Y: # Base do castelo
            p_screen = Rect(p.left - world_offset_x, p.top, p.width, p.height)
            screen.draw.filled_rect(p_screen, ELEVATED_PLATFORM_COLOR) 
        elif p.x == CASTLE_BASE_X + CASTLE_WIDTH - BLOCK_WIDTH and p.height == 2*BLOCK_WIDTH: # Torre do castelo
             p_screen = Rect(p.left - world_offset_x, p.top, p.width, p.height)
             screen.draw.filled_rect(p_screen, ELEVATED_PLATFORM_COLOR) 

    # 3. Desenha os inimigos
    for enemy in enemies:
        enemy.x_orig = enemy.x 
        enemy.x = enemy.x - world_offset_x 
        enemy.draw()
        enemy.x = enemy.x_orig 
        
    # 4. Desenha o jogador 
    if player: 
        player.draw()

# --- Inicialização da Música na Inicialização do Pygame Zero ---
play_music()
# --- Execução do PgZero ---
pgzrun.go()
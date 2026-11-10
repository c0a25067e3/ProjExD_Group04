import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
FPS = 50      # フレームレート
MAX_LIFESPAN_SEC = 15 * 60  # 寿命：15分（900秒）

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：Rect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん初期化
        引数 xy：初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)
        
        # --- 体力と寿命パラメータ ---
        self.hp: int = 200        # 初期体力
        self.max_hp: int = 300   # 最大体力
        self.is_alive: bool = True

        # --- 行動パラメータ ---
        self.state: str = "WALK" # "WALK" または "FLY"
        self.state_timer: int = 0
        self.move_vec: list[int] = [0, 0]
        self.change_dir_interval: int = 50  # 方向転換の間隔（フレーム数）

    def change_img(self, num: int, screen: pg.Surface):
        """こうかとん画像を切り替え，画面に転送する"""
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update_behavior(self):
        """ランダムな歩行と時々行う飛行の挙動制御"""
        self.state_timer += 1

        # 一定確率で飛行モードと歩行モードの切り替え
        if self.state == "WALK":
            if random.random() < 0.005:  # 約0.5%の確率で飛行開始
                self.state = "FLY"
                self.state_timer = 0
        elif self.state == "FLY":
            if self.state_timer > 150:   # 3秒間（150フレーム）飛んだら歩行に戻る
                self.state = "WALK"
                self.state_timer = 0

        # ランダム移動の方向切り替え
        if self.state_timer % self.change_dir_interval == 0:
            speed = 8 if self.state == "FLY" else 4
            move_opts = [-speed, 0, speed]
            self.move_vec = [random.choice(move_opts), random.choice(move_opts)]

    def consume_hp(self):
        """1秒ごとに実行される体力減少処理"""
        if not self.is_alive:
            return

        # 飛行時は2減少、歩行時は1減少
        loss = 2 if self.state == "FLY" else 1
        self.hp = max(0, self.hp - loss)

        if self.hp <= 0:
            self.is_alive = False

    def update(self, screen: pg.Surface):
        """位置更新・描画"""
        self.update_behavior()

        # 移動適用
        self.rct.move_ip(self.move_vec)

        # 画面外制御
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.rct.move_ip(-self.move_vec[0], 0)
            self.move_vec[0] *= -1
        if not tate:
            self.rct.move_ip(0, -self.move_vec[1])
            self.move_vec[1] *= -1

        # 移動方向に応じた画像の更新
        if self.move_vec != [0, 0]:
            # 方向ベクトルを正負(-5, 0, +5)に正規化して画像取得
            vx = 5 if self.move_vec[0] > 0 else (-5 if self.move_vec[0] < 0 else 0)
            vy = 5 if self.move_vec[1] > 0 else (-5 if self.move_vec[1] < 0 else 0)
            if (vx, vy) in __class__.imgs:
                self.img = __class__.imgs[(vx, vy)]

        # 飛行時は少し拡大・浮上表現のエフェクト
        draw_img = self.img
        draw_rct = self.rct.copy()
        if self.state == "FLY":
            draw_img = pg.transform.rotozoom(self.img, 0, 1.1)
            draw_rct.centery -= 10  # 少し浮かす

        screen.blit(draw_img, draw_rct)


class StatusDisplay:
    """
    体力バー、残り寿命、ステータス描画クラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 36)

    def update(self, screen: pg.Surface, bird: Bird, elapsed_sec: float):
        # 1. 体力バー描画
        bar_x, bar_y = 20, 20
        bar_width, bar_height = 300, 25
        hp_ratio = bird.hp / bird.max_hp
        current_width = int(bar_width * hp_ratio)

        # 枠線と背景
        pg.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # HP（緑〜赤）
        bar_color = (0, 255, 0) if hp_ratio > 0.3 else (255, 0, 0)
        pg.draw.rect(screen, bar_color, (bar_x, bar_y, current_width, bar_height))
        pg.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

        # HPテキスト
        hp_text = self.font.render(f"HP: {bird.hp} / {bird.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + 10, bar_y + 2))

        # 2. 状態（歩行/飛行）表示
        state_color = (255, 255, 0) if bird.state == "FLY" else (255, 255, 255)
        state_text = self.font.render(f"State: {bird.state}", True, state_color)
        screen.blit(state_text, (bar_x, bar_y + 35))

        # 3. 寿命（15分カウントダウン）表示
        remaining_sec = max(0, int(MAX_LIFESPAN_SEC - elapsed_sec))
        minutes = remaining_sec // 60
        seconds = remaining_sec % 60
        life_text = self.font.render(f"Lifespan: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(life_text, (WIDTH - 220, 20))


def main():
    pg.display.set_caption("こうかとん育成ゲーム（基本機能）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    #脱走したときの背景
    bg_aozora = pg.image.load("fig/aozora.jpg")
    bg_evening = pg.image.load("fig/GAMEOVER.jpg")

    bird = Bird((WIDTH // 2, HEIGHT // 2))
    status_disp = StatusDisplay()
    clock = pg.time.Clock()

    start_time = time.time()
    last_hp_decay_time = time.time()

    #脱走変数
    now_escaping=False #脱走中
    escaped_already=False #既に脱走したか
    escaped_start_time=0 #脱走した時間


    while True:
        current_time = time.time()
        elapsed_sec = current_time - start_time

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        # 脱走中にクリックされたら捕獲判定
        if now_escaping and event.type == pg.MOUSEBUTTONDOWN:
            if bird.rct.collidepoint(event.pos):
                now_escaping = False
                bird.state = "WALK"
                bird.hp = max(0, bird.hp - 50)

        #体力が半分以下になったら脱走
        if bird.hp <= bird.max_hp // 2 and not escaped_already and not now_escaping:
            now_escaping = True
            escaped_already = True
            escaped_start_time = time.time()

        #脱走中の移動、制限時間
        if now_escaping:
            bird.state = "FLY"
            fly_speed = 8
            #止まらないで移動
            if bird.state_timer % bird.change_dir_interval == 0:
                move_opts = [-fly_speed,fly_speed]
                bird.move_vec = [random.choice(move_opts), random.choice(move_opts)]
            # 10秒過ぎても捕まえられない場合
            if current_time - escaped_start_time >= 10.0:
                screen.blit(bg_evening, [0, 0]) 
                font_big = pg.font.Font(None, 80)
                txt = font_big.render("Kokaton Escaped...", True, (255, 0, 0))
                screen.blit(txt, (WIDTH // 2 - 150, HEIGHT // 2))
                pg.display.update()
                time.sleep(2)
                return
            
        # --- 1秒ごとに体力を減算 ---
        if current_time - last_hp_decay_time >= 1.0:
            bird.consume_hp()
            last_hp_decay_time = current_time

        # --- ゲームオーバー・寿命判定 ---
        if not bird.is_alive or elapsed_sec >= MAX_LIFESPAN_SEC:
            font_big = pg.font.Font(None, 80)
            reason = "Died of Exhaustion..." if not bird.is_alive else "Reached Lifespan End"
            txt = font_big.render(f"GAME OVER({reason})", True, (255, 0, 0))
            screen.blit(txt, (WIDTH // 2 - 350, HEIGHT // 2))
            pg.display.update()
            time.sleep(2)
            return

        # 画面の切り替え
        if now_escaping:
            screen.blit(bg_aozora, [0, 0])  #脱走中は上空
        else:
            screen.blit(bg_img, [0, 0])     #通常時は通常背景

        bird.update(screen)
        status_disp.update(screen, bird, elapsed_sec)

        #捕まえろ！表示
        if now_escaping and (current_time - escaped_start_time <= 2.0):
                font_big = pg.font.Font(None, 80)
                warn_txt = font_big.render("Capture Kokaton!", True, (255, 0, 0))
                screen.blit(warn_txt, (WIDTH // 2 - warn_txt.get_width() // 2, 80))     
        pg.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
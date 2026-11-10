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

def birth_kokaton(screen: pg.Surface, bg_img: pg.Surface):
    """
    こうかとんが生まれる！
    """
    bg_black = pg.Surface((WIDTH, HEIGHT))
    pg.draw.rect(bg_black,(0,0,0),bg_black.get_rect())
    for i in range(0,100,1):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        screen.blit(bg_img,[0,0])
        bg_black.set_alpha(i)
        screen.blit(bg_black,[0,0])
        pg.display.update()
        pg.time.delay(20)
    fonto = pg.font.Font(None,100)
    txt = fonto.render("Kokaton was born!",True,(255,255,255))
    random_egg = random.randint(1,6)
    egg_img = pg.transform.rotozoom(pg.image.load(f"fig/egg{random_egg}.png"), 0, 0.4)
    egg_rct = egg_img.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.4)))
    bg_black.blit(txt,[screen.get_rect().centerx-txt.get_width()//2,HEIGHT*1/2])
    light = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
    for i in range(0,255,5):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        screen.blit(bg_img,[0,0])
        bg_black.set_alpha(100)
        screen.blit(egg_img,egg_rct)
        screen.blit(bg_black,[0,0])
        pg.display.update()
        pg.time.delay(10)
    for i in range(150):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        screen.blit(bg_img, [0, 0])
        bg_black.set_alpha(100)
        screen.blit(bg_black, [0, 0])

        angle = math.sin(i * 0.2) * 15

        wobble_egg = pg.transform.rotozoom(egg_img, angle, 1.0)
        wobble_rct = wobble_egg.get_rect(center=egg_rct.center)

        screen.blit(wobble_egg, wobble_rct)
        pg.display.update()
        pg.time.delay(20)

    for i in range(0, WIDTH, 25):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        screen.blit(bg_img, [0, 0])
        bg_black.set_alpha(100)
        screen.blit(bg_black, [0, 0])
        screen.blit(egg_img, egg_img.get_rect(center=egg_rct.center))

        # 卵の中心に光の白い円を描画
        light.fill((0, 0, 0, 0))
        
        # 半径が広がるにつれて光を強くする
        alpha = min(250, int(100 + (i / WIDTH) * 150))
        pg.draw.circle(light, (255, 255, 255, alpha), egg_rct.center, i)

        screen.blit(light, [0, 0])
        pg.display.update()
        pg.time.delay(15)

    pg.display.update()
    


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    # Walkの時
    img0 = pg.transform.rotozoom(pg.image.load("fig/10.png"), 0, 0.3)
    
    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん初期化
        引数 xy：初期位置座標タプル
        """
        # --- 行動パラメータ ---
        self.state: str = "WALK" # "WALK" または "FLY"
        self.state_timer: int = 0
        self.move_vec: list[int] = [0, 0]
        self.change_dir_interval: int = 50  # 方向転換の間隔（フレーム数）
        self.age_state = "Child"  # 成長三段階

        self.img = pg.transform.flip(self.img0, True, False)  # 初期画像（右向き）
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)
        
        # --- 体力と寿命パラメータ ---
        self.hp: int = 5        # 初期体力
        self.max_hp: int = 300   # 最大体力
        self.is_alive: bool = True

    def grow(self, lifespan: int):
        """こうかとんの成長段階に応じて画像を変化させる"""
        if lifespan == 0 and self.age_state != "Child":  # 5分未満
            self.age_state = "Child"
        elif lifespan == 1 and self.age_state != "Adult":  # 5分以上10分未満
            self.change_img(5)
            self.age_state = "Adult"
        elif lifespan == 2 and self.age_state != "Senior":  # 10分以上
            self.change_img(13)
            self.age_state = "Senior"

    def change_img(self, num: int):
        """こうかとん画像を切り替え，画面に転送する"""
        if num == 10 or num == 11:
            self.img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.2)
        elif num == 12 or num == 13:
            self.img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.3)
        else:
            self.img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 1.0)

        self.img = pg.transform.flip(self.img0, True, False)

    def update_behavior(self, screen: pg.Surface):
        """ランダムな歩行と時々行う飛行の挙動制御"""
        self.state_timer += 1

        # 一定確率で飛行モードと歩行モードの切り替え
        if self.state == "WALK":
            if random.random() < 0.001:  # 約0.1%の確率で飛行開始
                if self.age_state == "Child":
                    self.change_img(11)
                elif self.age_state == "Adult":
                    self.change_img(3)
                elif self.age_state == "Senior":
                    self.change_img(12)
                self.state = "FLY"
                self.state_timer = 0
        elif self.state == "FLY":
            if self.state_timer > 150:   # 3秒間（150フレーム）飛んだら歩行に戻る
                if self.age_state == "Child":
                    self.change_img(10)
                elif self.age_state == "Adult":
                    self.change_img(5)
                elif self.age_state == "Senior":
                    self.change_img(13)
                self.state = "WALK"
                self.state_timer = 0

        # ランダム移動の方向切り替え
        if self.state_timer % self.change_dir_interval == 0:
            speed = 8 if self.state == "FLY" else 4
            move_opts = [-speed, 0, speed]
            if random.randint(1,3) == 1 or self.state == "FLY":
                self.move_vec = [random.choice(move_opts), random.choice(move_opts)]
            else:
                self.move_vec = [0, 0]

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
        self.update_behavior(screen)

        img0 = self.img0
        img = pg.transform.flip(img0, True, False)
        imgs = {
            (+1, 0): img,  # 右
            (0, -1): img,  # 上
            (+1, -1): img,  # 右上
            (-1, -1): img0,  # 左上
            (-1, 0): img0,  # 左
            (0, +1): img,  # 下
            (-1, +1): img0,  # 左下
            (+1, +1): img,  # 右下
        }


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
            vx = 1 if self.move_vec[0] > 0 else (-1 if self.move_vec[0] < 0 else 0)
            vy = 1 if self.move_vec[1] > 0 else (-1 if self.move_vec[1] < 0 else 0)
            if (vx, vy) in imgs:
                self.img = imgs[(vx, vy)]

        screen.blit(self.img, self.rct)


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
    
    bird = Bird((WIDTH // 2, HEIGHT // 2))
    status_disp = StatusDisplay()
    clock = pg.time.Clock()

    spawn_egg = 1  # こうかとんの再生成回数
    game_scene = "Main"

    start_time = time.time()
    last_hp_decay_time = time.time()

    while True:
        current_time = time.time()
        elapsed_sec = current_time - start_time

        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return


        # --- 1秒ごとに体力を減算 ---
        if current_time - last_hp_decay_time >= 1.0:
            bird.consume_hp()
            last_hp_decay_time = current_time

        if elapsed_sec // 300 == 1:
            bird.grow(1)
        elif elapsed_sec  // 300 == 2:
            bird.grow(2)
        # --- ゲームオーバー・寿命判定 ---
        if not bird.is_alive or elapsed_sec >= MAX_LIFESPAN_SEC:
            # 死亡後の調理
            # cook.is_confirm = True
            
            if spawn_egg > 0:  # こうかとんを再生成する
                birth_kokaton(screen, bg_img)
                pg.display.update()
                bird = Bird((WIDTH // 2, HEIGHT // 2))  # 新しいこうかとんを生成
                time.sleep(2)
                start_time = time.time()  # 寿命リセット
                spawn_egg -= 1
            else:
                font_big = pg.font.Font(None, 80)
                reason = "Died of Exhaustion..." if not bird.is_alive else "Reached Lifespan End"
                txt = font_big.render(f"Game Over ({reason})", True, (255, 0, 0))
                screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))
                pg.display.update()
                time.sleep(2)
                return


        # 描画更新
        screen.blit(bg_img, [0, 0])
        status_disp.update(screen, bird, elapsed_sec)
        bird.update(screen)
        
        pg.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
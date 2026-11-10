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
        self.hp: int = 80        # 初期体力
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

class Sleep:
    
    def sleep(self, screen: pg.Surface, bird: Bird):  #背景を変更し睡眠をとる
        back_image = pg.image.load("back_sleepfig/eveningsky.png")  #背景を夕方に変更する
        screen.blit(back_image, (0, 0))
        fonto = pg.font.Font(None,80)
        txt = fonto.render("Koukaton is sleeping.", True, (255, 255, 255))
        screen.blit(txt, [250, 250])
        pg.display.update()
        time.sleep(3)
            
        back_image = pg.image.load("back_sleepfig/nightsky.png")  #背景を夜に変更する
        screen.blit(back_image, (0, 0))
        fonto = pg.font.Font(None,80)
        txt = fonto.render("Koukaton is sleeping...", True, (255, 255, 255))
        screen.blit(txt, [250, 250])
        pg.display.update()
        time.sleep(4)
        
        back_image = pg.image.load("back_sleepfig/morningsky.png")  #背景を朝に変更する
        screen.blit(back_image, (0, 0))
        fonto = pg.font.Font(None,80)
        txt = fonto.render("Koukaton woke up ...", True, (255, 255, 255))
        screen.blit(txt, [250, 250])
        pg.display.update()
        time.sleep(3)  #各背景時間を合わせて10秒

        if bird.hp >= 270:
            bird.hp = 300
        else:
            bird.hp += 30  #hpに30秒加える

    def update(self, screen : pg.Surface, sleep_check, sleep_select):  #画面表示をする
        if sleep_check == True:
            fonto = pg.font.Font(None,70)
            txt_Question = fonto.render("Do you want to get some sleep?", True, (0, 191, 255))
            txt1 = txt_Question.get_rect(center = (WIDTH/2, 150))
            txt_Decision = fonto.render("up_key/douwn_key/enter_key", True, (0, 191, 255))
            txt2 = txt_Decision.get_rect(center = (WIDTH/2, 200))
            screen.blit(txt_Question, txt1)
            screen.blit(txt_Decision, txt2)

            if sleep_select == 0:  #"Yes"が選択されている場合
                txt_Answer1 = fonto.render("Yes", True, (128, 128, 128))
                txt_Answer2 = fonto.render(" No", True, (255, 255, 255))
                
            elif sleep_select == 1:  #"No"が選択されている場合
                txt_Answer1 = fonto.render("Yes", True, (255, 255, 255))
                txt_Answer2 = fonto.render(" No", True, (128, 128, 128))
            txt3 = txt_Answer1.get_rect(center = (WIDTH/2, 350))
            txt4 = txt_Answer1.get_rect(center = (WIDTH/2, 450))
            screen.blit(txt_Answer1, txt3)
            screen.blit(txt_Answer2, txt4)

def main():
    pg.display.set_caption("こうかとん育成ゲーム（基本機能）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    
    bird = Bird((WIDTH // 2, HEIGHT // 2))
    status_disp = StatusDisplay()
    sleep_choice = Sleep()  #Sleepクラスの呼び出し
    clock = pg.time.Clock()

    start_time = time.time()
    last_hp_decay_time = time.time()
    three_time = 180 #3分経過を計る
    sleep_check = False  #sキーが押されたかどうか
    sleep_select = 0  #0：”Yse”ボタンを選択

    while True:
        current_time = time.time()
        elapsed_sec = current_time - start_time

        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            #sキーが押されたとき選択画面を表示
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s and elapsed_sec >= three_time:  #sキーが押されたかつ既定の時間を超えたとき
                    sleep_check = True
                    sleep_select = 0
                elif sleep_check == True and event.key == pg.K_UP:  #sキーが押されてかつ上キーが押されたとき
                    sleep_select = 0
                elif sleep_check == True and event.key == pg.K_DOWN:  #sキーが押されてかつ下キーが押されたとき
                    sleep_select = 1
                elif sleep_check == True and event.key == pg.K_RETURN:  #sキーが押されてかつenterキーが押されたとき
                    if sleep_select == 0:
                        sleep_choice.sleep(screen, bird)  #睡眠プログラムを動かす
                        three_time = elapsed_sec + 180
                    sleep_check = False
                    

        # --- 1秒ごとに体力を減算 ---
        if current_time - last_hp_decay_time >= 1.0:
            bird.consume_hp()
            last_hp_decay_time = current_time

        # --- ゲームオーバー・寿命判定 ---
        if not bird.is_alive or elapsed_sec >= MAX_LIFESPAN_SEC:
            font_big = pg.font.Font(None, 80)
            reason = "Died of Exhaustion..." if not bird.is_alive else "Reached Lifespan End"
            txt = font_big.render(f"Game Over ({reason})", True, (255, 0, 0))
            screen.blit(txt, (WIDTH // 2 - 350, HEIGHT // 2))
            pg.display.update()
            time.sleep(2)
            return

        # 描画更新
        screen.blit(bg_img, [0, 0])
        bird.update(screen)
        status_disp.update(screen, bird, elapsed_sec)
        sleep_choice.update(screen, sleep_check, sleep_select)

        pg.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
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

# ===== ↓ミニゲーム =====
EGG_TYPES = 6   # 卵の種類数
EGG_INTERVAL = 15   # 卵の出現頻度
EGG_LIFESPAN = 7   # 卵の消滅までの時間(GAMEOVER)
EGG_GOLD_PROBABILITY = 0.1   # 金の卵の出現確率
# ===== ↑ミニゲーム =====

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
        self.hp: int = 600        # 初期体力
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

# ===== ↓ミニゲーム =====
"""
卵の種類,画像,移動速度,出現時間の管理.
通常の卵と金の卵で異なる動きを設定.
"""
EGG_IMAGES = [   # 卵画像の読み込みと縮小
    pg.transform.rotozoom(pg.image.load(f"fig/egg_{color}.png"), 0, 0.1)
    for color in ["blue", "brown", "green", "orange", "purple", "red"]
]
GOLD_EGG_IMAGE = pg.transform.rotozoom(
    pg.image.load("fig/egg_gold.png"), 0, 0.1
)
class Egg:
    def __init__(self,egg_type:int,xy:tuple[int,int]):
        self.egg_type = egg_type   # 卵の種類を保存
        self.is_gold = egg_type == 7   # 卵の種類が7の場合は金の卵として判定
        self.has_entered_screen = False   # 卵が画像内に入ったかどうかの判定
        self.start_time = time.time()   # 卵の生成された時間を記録
        if self.is_gold:   # 読み込んだ画像の取得
            self.img = GOLD_EGG_IMAGE
        else:
            self.img = EGG_IMAGES[egg_type - 1]
        self.rct = self.img.get_rect(center=xy)
        self.direction = random.choice([-1, 1])   # 卵の移動方向設定(上下)
        if self.is_gold:   # 金の卵の移動速度設定
            self.speed = 15
        else:
            self.speed = random.randint(2,5)   # 通常の卵の移動速度設定

    def update(self,screen:pg.Surface):
        if self.direction == 1:
            self.rct.y += self.speed   # 下に移動
        else:
            self.rct.y -= self.speed   # 上に移動
        screen.blit(self.img,self.rct)
    def is_rotten(self) -> bool:   # 卵の生成から指定秒数経過でTrueを返し腐敗判定
        return time.time()-self.start_time >= EGG_LIFESPAN
# ===== ↑ミニゲーム =====

# ===== ↓ミニゲーム =====
"""
ミニゲームの管理.卵の生成,移動と描画,マウス操作など.
卵と巣の種類が同じなら獲得,不一致や時間経過で終了.
金の卵の獲得判定,卵の獲得数管理.
"""
class EggMiniGame:
    def __init__(self):
        """
        初期設定
        """
        self.bg_img = pg.image.load("fig/background_minigame.jpg")   # 背景画像の読み込みとサイズ調整
        self.bg_img = pg.transform.scale(self.bg_img,(WIDTH,HEIGHT))
        self.gold_icon = pg.image.load("fig/egg_gold.png")   # 金の卵を所持した際の画像配置
        self.gold_icon = pg.transform.rotozoom(self.gold_icon,0,0.07)
        self.gold_icon_rect = self.gold_icon.get_rect(bottomright=(WIDTH-20,HEIGHT-20))
        nest_images = [
            "nest_blue.png",
            "nest_brown.png",
            "nest_green.png",
            "nest_orange.png",
            "nest_purple.png",
            "nest_red.png"
        ]
        self.basket_imgs = []   # 画像の読み込みと縮小
        for img_name in nest_images:
            img = pg.image.load(f"fig/{img_name}")
            img = pg.transform.rotozoom(img, 0, 0.85)
            self.basket_imgs.append(img)

        self.font = pg.font.Font(None, 32)   # 文字の大きさ設定
        self.big_font = pg.font.Font(None, 60)
        self.count_font = pg.font.Font(None, 48)
        self.eggs = []   # 画面上の卵リスト
        self.baskets = []   # 画面上の巣のリスト
        self.egg_counts = [0]*EGG_TYPES   # 種類ごとの卵の獲得数
        self.new_eggs = 0   # 今回のプレイでの新規卵獲得数
        self.total_eggs = 0   # 全ゲームでの卵獲得数
        self.has_gold = False   # 金の卵所持判定
        self.active_types = 1   # 現在の出現種類数
        self.start_time = time.time()   # ゲーム開始時刻と卵の生成時刻の記録
        self.last_spawn_time = time.time()
        self.game_over = False   # GAMEOVERかどうか
        self.dragging_egg = None   # ドラッグ中の卵管理
        self.drag_offset = (0, 0)
        self.create_baskets()

    def create_baskets(self):
        """
        巣の配置
        """
        self.baskets = []
        positions = [
            (300, 110),
            (150, 325),
            (300, 540),
            (800, 110),
            (950, 325),
            (800, 540),
        ]
        for i, pos in enumerate(positions):   # 巣の画像,位置,獲得数,種類をリストに追加
            img = self.basket_imgs[i]
            rect = img.get_rect(center=pos)
            self.baskets.append({
                "image": img,   # 巣の画像
                "rect": rect,   # 巣の位置と大きさ
                "count": 0,   # 入れた卵の数
                "type": i   # 巣の種類を判別
            })

    def restart(self):
        """
        リスタート(前回の結果をリセット)
        """
        self.eggs = []   # 画面上の卵削除
        self.egg_counts = [0]*EGG_TYPES   # 獲得数りセット
        self.new_eggs = 0   # 今回の獲得数リセット
        self.active_types = 1   # 種類数を1に戻す
        self.start_time = time.time()   #時刻の更新
        self.last_spawn_time = time.time()
        self.game_over = False   #GAMEOVERを解除
        self.dragging_egg = None
        self.drag_offset = (0, 0)
        self.create_baskets()   # 初期状態に戻して再配置
    
    def spawn_egg(self):
        """
        卵の生成
        """
        if random.random() < EGG_GOLD_PROBABILITY and not self.has_gold:   # 設定確率で金の卵を出現&既に持っていないか確認
            egg_type = 7   # 種類を7に設定
        else:
            egg_type = random.randint(1,self.active_types)   # 通常の卵を生成
        x = random.randint(50,WIDTH-50)   # 出現させる横方向を決定

        if random.choice([True, False]):   # 卵が上か下に出現するように設定
            y = -50
            direction = 1   # 下に移動
        else:
            y = HEIGHT + 50
            direction = -1   # 上に移動
        egg = Egg(egg_type, (x, y))   # 決まった種類,座標で生成し移動方向を設定
        egg.direction = direction
        self.eggs.append(egg)   # 生成した卵をリストに追加

    def update(self, screen: pg.Surface):
        """    
        ゲーム画面の更新
        """
        screen.blit(self.bg_img, (0, 0))   # 背景描画
        elapsed = time.time()-self.start_time   # 経過時間の計算
        self.active_types = min(EGG_TYPES,1+int(elapsed//EGG_INTERVAL))   # 指定時間で種類数の追加
        if time.time()-self.last_spawn_time >= 1:   # 前回の生成から1秒経過で生成
            self.spawn_egg()
            self.last_spawn_time = time.time()
        
        for basket in self.baskets:   # 巣の画像,入れた個数を表示
            screen.blit(basket["image"], basket["rect"])
            text = self.count_font.render(
                str(basket["count"]),True,(255,255,255)
            )
            text_rect = text.get_rect(
                midtop=(basket["rect"].centerx, basket["rect"].bottom -30)
            )
            screen.blit(text, text_rect)

        for egg in self.eggs[:]:   # 画面上の卵を更新
            egg.update(screen)
            if egg.rct.bottom >= 0 and egg.rct.top <= HEIGHT:   # 画面内に入ったことを記録
                egg.has_entered_screen = True
            if egg.has_entered_screen:   # 1度画面に入った卵が画面外に出たらリストから削除
                if egg.rct.bottom < 0 or egg.rct.top > HEIGHT:
                    self.eggs.remove(egg)
                    continue
            if egg.has_entered_screen and egg.is_rotten():   # 画面内の卵が腐ったらGAMEOVER
                self.game_over = True
                return
        if self.has_gold:   # 金の卵を所持してたら右下に画像表示
            screen.blit(self.gold_icon, self.gold_icon_rect)

    def handle_click(self, pos: tuple[int, int]):
        """
        クリック処理
        """
        if self.game_over:
            return
        for egg in self.eggs:   # クリック箇所に卵が存在するかどうか確認
            if egg.rct.collidepoint(pos):
                if egg.is_gold:   # 金の卵の場合クリックで獲得&画面から削除
                    self.has_gold = True
                    self.eggs.remove(egg)
                    return
                self.dragging_egg = egg   # 通常の卵をドラッグできるように設定
                self.drag_offset = (
                    egg.rct.x-pos[0],
                    egg.rct.y-pos[1]
                )
                return

    def drag_egg(self, pos: tuple[int, int]):
        """
        卵が選択されてるときマウスに合わせて卵も移動
        """
        if self.dragging_egg is not None:
            self.dragging_egg.rct.x = pos[0]+self.drag_offset[0]
            self.dragging_egg.rct.y = pos[1]+self.drag_offset[1]

    def handle_drop(self, pos: tuple[int, int]):
        """
        ドラッグ処理
        """
        if self.dragging_egg is None:
            return
        egg = self.dragging_egg
        self.dragging_egg = None
        for i, basket in enumerate(self.baskets):   # 卵を話した場所に巣があるか確認
            if basket["rect"].collidepoint(pos):
                if egg.is_gold:
                    self.has_gold = True
                    self.eggs.remove(egg)
                    return
                if egg.egg_type == i + 1:   # 卵の種類と巣の種類が一致してるか判定
                    basket["count"] += 1   # 巣に入れた卵の個数追加
                    self.egg_counts[i] += 1   # 種類ごとの個数追加
                    self.new_eggs += 1   # 今回の獲得数追加
                    self.total_eggs += 1   # 合計獲得数追加
                    self.eggs.remove(egg)   # 仕分けた卵を削除
                else:
                    self.game_over = True   # 間違えたらGAMEOVER
                return
# ===== ↑ミニゲーム =====

def main():
    pg.display.set_caption("こうかとん育成ゲーム（基本機能）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    
    bird = Bird((WIDTH // 2, HEIGHT // 2))
    status_disp = StatusDisplay()
    clock = pg.time.Clock()

    start_time = time.time()
    last_hp_decay_time = time.time()

# ===== ↓ミニゲーム =====
    """
    インスタンス作成,画面切り替えに必要な変数の初期化(ボタンなど)
    """
    mini_game = EggMiniGame()
    in_minigame = False
    button_font = pg.font.Font(None,32)
    button_rect = pg.Rect(WIDTH-170,80,150,50)
    restart_rect = pg.Rect(WIDTH-170,140,150,50)
# ===== ↑ミニゲーム =====

    while True:
        current_time = time.time()
        elapsed_sec = current_time - start_time

        # イベント処理
# ===== ↓ミニゲーム =====
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return   # ウィンドウが閉じられたらゲーム終了
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:   # 左クリックを検出
                    if button_rect.collidepoint(event.pos):
                        in_minigame = not in_minigame   # ミニゲーム画面の表示非表示切り替え
                    elif in_minigame and mini_game.game_over and restart_rect.collidepoint(event.pos):
                        mini_game.restart()   # リスタートボタンで初期化
                    elif in_minigame:
                        mini_game.handle_click(event.pos)   # クリック位置を判定
            elif event.type == pg.MOUSEMOTION:
                if in_minigame and mini_game.dragging_egg is not None:
                    mini_game.drag_egg(event.pos)   # 卵選択中ならマウスと移動
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1 and in_minigame:
                    mini_game.handle_drop(event.pos)   # 左クリックを離した位置で仕分け
# ===== ↑ミニゲーム =====

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
# ===== ↓ミニゲーム =====
        screen.blit(bg_img, [0, 0])   # 背景描画
        if in_minigame:
            mini_game.update(screen)   #ミニゲーム画面更新
            if mini_game.game_over:   # 画面中央に結果の表示
                txt = button_font.render("GAME OVER", True, (255, 0, 0))
                screen.blit(txt, (WIDTH // 2 - 100, HEIGHT // 2 - 400))
                result_font = pg.font.Font(None, 55)
                total_text = result_font.render(   # 新規獲得数の表示
                    f"New Eggs: {mini_game.new_eggs}",
                    True, (255, 255, 255)
                )
                screen.blit(
                    total_text,
                    (WIDTH // 2 - total_text.get_width() // 2,HEIGHT // 2-40)
                )
                
                all_total_text = result_font.render(   # 合計獲得数の表示
                    f"Total Eggs: {mini_game.total_eggs}",
                    True, (255, 215, 0)
                )
                screen.blit(
                    all_total_text,
                    (WIDTH // 2 - all_total_text.get_width() // 2,HEIGHT // 2+10)
                )
        else:   # ミニゲーム非表示のときは元画面を更新
            screen.blit(bg_img,[0,0])
            bird.update(screen)
            status_disp.update(screen,bird,elapsed_sec)
            
        pg.draw.rect(screen,(50,100,200),button_rect)   #画面切り替えボタンを描画
        button_text = button_font.render("Return" if in_minigame else "Egg hunt",True,(255,255,255))
        if in_minigame and mini_game.game_over:   # GAMEOVARでリスタートボタン表示
            pg.draw.rect(screen, (50, 150, 50), restart_rect)
            restart_text = button_font.render("Restart", True, (255, 255, 255))
            screen.blit(
                restart_text,
                (
                    restart_rect.centerx - restart_text.get_width() // 2,
                    restart_rect.centery - restart_text.get_height() // 2
                )
            )
        screen.blit(button_text,(   # ボタンの中央に文字を配置
            button_rect.centerx - button_text.get_width() // 2,
            button_rect.centery - button_text.get_height() // 2))
# ===== ↑ミニゲーム =====
        
        pg.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
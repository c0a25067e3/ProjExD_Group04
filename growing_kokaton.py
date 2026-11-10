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
pg.mixer.init()  # 音声の初期化


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

        # --- 調理機能で追加 ---
        self.is_cooked_once = False  # 一度調理されたか
        self.is_grabbed = False  # マウスで掴まれているか
        self.is_inho = False  # フライパンか油に入れられたか
        self.is_kona = False  # 粉がぶつかったか
        self.is_baku = False  # 爆発したか
        self.konakou_img = pg.transform.rotozoom(pg.image.load("fig/粉まみれこうかとん.png"), 0, 0.9)  # 表示する粉まみれこうかとん
        self.grab_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)  # 表示する泣いてるこうかとん
        self.yakikou_img = pg.transform.rotozoom(pg.image.load("fig/爆発こうかとん.png"), 0, 0.9)  # 表示する丸焼きになったこうかとん


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

        # 調理機能で追加
        if self.is_grabbed or self.is_inho or self.is_kona or self.is_baku:  # 掴んでる・フライパン/油に入っている・粉まみれ・爆発したのいずれかの場合
            if self.is_kona:  # 粉まみれになった場合
                draw_rct = self.konakou_img.get_rect(center=self.rct.center)  # 描画画像の中心が動いているこうかとんの中心と同じ位置になるように設定
                screen.blit(self.konakou_img, draw_rct)  # 粉まみれこうかとんの描画
            elif self.is_baku:  # 爆発した場合
                draw_rct = self.yakikou_img.get_rect(center=self.rct.center)
                screen.blit(self.yakikou_img, draw_rct)  # 爆発したこうかとんの描画
            else:  # 掴んでいるか調理中の場合
                draw_rct = self.grab_img.get_rect(center=self.rct.center)
                screen.blit(self.grab_img, draw_rct)  # 泣いているこうかとんの描画
            return  # 特殊状態がそのまま引き継がれるようreturn

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


class Cook():
    """
    料理クラス.こうかとんを料理します
    """
    def __init__(self, screen: pg.surface):
        self.is_confirm = False  # 料理するかどうかの確認画面を表示しているか？
        self.confirm_select = 0  # yes,noのどちらを選択しているか管理 0:Yes(料理する) 1:No(料理しない)
        self.is_cooking = False  # 実際に調理しているか？
        self.is_select = True  # 料理の種類を選択しているか？
        self.is_select_egg = False  # 卵の種類を選択しているか？
        self.is_confirm_nxegg = False  # 次世代卵を使用するか確認画面を表示しているか？
        self.is_confirm_nxegg_select = 0  # yes,noのどちらを選択しているか管理 0:Yes(使用する) 1:No(使用しない)
        self.no_egg_messe = ""  # 卵がない時に画面に表示するメッセージ
        self.is_exp = False  # 爆発したか？
        self.is_hit = False  # こうかとんと爆弾が衝突したか？
        self.exp_time = 0  # 爆弾を設置してからの経過時間を管理
        self.font = pg.font.Font(None, 50)  # 文字表示
        self.bg_img = pg.image.load("fig/キッチン.jpg")  # 背景画像をロード
        self.bg_rct = self.bg_img.get_rect()  # 背景画像のrectを取得

        self.select = 0  # 選択中の料理番号を管理
        self.k_step = 0  # 料理工程数の管理
        self.type_egg = 0  # 親子丼に使用する卵の種類(0:通常の卵を使用　1:次世代卵を使用する)
        self.egg = 100  # 通常卵の仮置き
        self.next_egg = 1  # 次世代卵の仮置き

        self.recip = ["Kara-age", "Oyako-Don", "Maru-yaki"]  # 料理リスト
        self.li_egg = ["Normal egg", "Next Generation egg"]  # 卵のリスト
        self.cook_img = [pg.image.load("fig/8.png"),  # 0:泣いてるこうかとん
                         pg.image.load("fig/小麦粉.png"),   # 1:小麦粉
                         pg.image.load("fig/油.png"),   # 2:油
                         pg.image.load("fig/からあげ.png"),  # 3:からあげ
                         pg.image.load("fig/フライパン.png"),  # 4:フライパン
                         pg.image.load("fig/卵.png"),  # 5:通常の卵
                         pg.image.load("fig/卵(次世代).png"),  # 6:次世代の卵
                         pg.image.load("fig/ごはん.png"),  # 7:白米
                         pg.image.load("fig/親子丼.png"),  # 8:親子丼
                         pg.image.load("fig/explosion.gif"),  # 9:爆発
                         pg.image.load("fig/丸焼き.png"),  # 10:丸焼き
                         pg.image.load("fig/卵つきこうかとん.png"),  # 11:卵のついたこうかとん
                         pg.image.load("fig/粉まみれこうかとん.png"),  # 12:粉のついたこうかとん
                         pg.image.load("fig/爆発こうかとん.png")]  # 13:爆発したこうかとん
        self.img_k = pg.transform.scale(self.cook_img[0], (300, 300))  # こうかとんのサイズ変更
        self.img_k = pg.transform.flip(self.img_k, True, False)  # こうかとんの向き変更
        self.img_h = pg.transform.scale(self.cook_img[4], (350, 350))  # フライパンのサイズ変更
        self.img_e = pg.transform.scale(self.cook_img[9], (100, 100))  # explosionのサイズ変更

        self.is_mouse = False  # マウスで画像を掴んでいるか？
        self.item = None  # 掴んでいる画像の種類

        self.fin_sound = pg.mixer.Sound("mp/きらきら輝く3.mp3")
        self.st_sound = pg.mixer.Sound("mp/「どう料理してやろうかのう」.mp3")
        self.cook_sound = "mp/3分クッキング.mp3"

        # ---当たり判定の取得---
        self.rct_kona = self.cook_img[1].get_rect(center=(WIDTH//2, HEIGHT//2))  # 小麦粉の中心座標を指定して位置決定
        self.rct_oil = self.cook_img[2].get_rect(center=(WIDTH//2, HEIGHT//2))  # 油の中心座標を指定して位置決定
        self.rct_egg = self.cook_img[5].get_rect(center=(200, 250))  # 通常卵の中心座標を指定して位置決定
        self.rct_next_egg = self.cook_img[6].get_rect(center=(200, 250))  # 次世代卵の中心座標を指定して位置決定
        self.rct_h = self.img_h.get_rect(center=(WIDTH//2, 450))  # フライパンの中心座標を指定して位置決定
        self.rct_exp = self.img_e.get_rect()  # 爆発の位置取得

    def cook_start(self, screen: pg.surface, bird: Bird):
        """
        こうかとんを調理する処理
        """
        screen.blit(self.bg_img, self.bg_rct)  # 背景画像をスクリーンに貼り付け
        # ---卵がないメッセージを表示するための処理---
        if self.no_egg_messe != "":
            text = self.font.render(self.no_egg_messe, True, (255, 0, 0))
            text_rct = text.get_rect(center=(WIDTH//2, HEIGHT-80))
            screen.blit(text, text_rct)

        # ---料理を選択させる処理---
        if self.is_select:
            text = self.font.render("Please select (k_up, k_down, enter)", True, (255, 255, 255))  # 選択を促す文字
            text_rct = text.get_rect(center=(WIDTH//2, 100))
            screen.blit(text, text_rct)

            for i, menu in enumerate(self.recip):
                if i == self.select:  # 現在の選択番号iと料理番号が一致しているか
                    color = (255, 255, 0)  # 一致してたら黄色
                else:
                    color = (255, 255, 255)  # 違ってたら白
                text = self.font.render(menu, True, color)
                text_rct = text.get_rect(center=(WIDTH//2, 200 + i * 100))
                screen.blit(text, text_rct)
            return

        # ---使用する卵を選択させる処理---
        elif self.is_select_egg:
            text = self.font.render("Please select (k_up, k_down, enter)", True, (255, 255, 255))  # 洗濯を促す文字
            text_rct = text.get_rect(center=(WIDTH//2, 100))
            screen.blit(text, text_rct)

            for i, e in enumerate(self.li_egg):  # 選択されている選択肢だけ色を変える処理
                if i == self.type_egg:
                    color = (255, 255, 0)
                else:
                    color = (255, 255, 255)
                # 選択肢の描画
                text = self.font.render(e, True, color)
                text_rct = text.get_rect(center=(WIDTH//2, 200 + i * 100))
                screen.blit(text, text_rct)
            return

        # ---次世代卵を使用するか確認する処理---
        elif self.is_confirm_nxegg:  # 次世代卵を使用するか確認画面の場合(料理機能で追加)
            text = self.font.render("Hontou ni tukau?", True, (255, 255, 255))
            text_rct = text.get_rect(center=(WIDTH//2, 150))
            screen.blit(text, text_rct)

            confirm_list = ["Yes", "No"]  # 確認するためのリスト

            for i, ans in enumerate(confirm_list):  # 色変えるための処理
                if i == self.is_confirm_nxegg_select:
                    color = (255, 255, 0)
                else:
                    color = (255, 255, 255)

                text = self.font.render(ans, True, color)
                text_rct = text.get_rect(center=(WIDTH//2, 300 + i * 100))
                screen.blit(text, text_rct)
            
            return

        # ---からあげが選ばれた時の処理---
        if self.select == 0:
            if self.k_step == 0:  # 粉をまぶす
                bird.update(screen)  # 動き回るこうかとんの描画
                screen.blit(self.cook_img[1], self.rct_kona)  # 小麦粉の描画
                self.draw_step(screen, "step1.Kona wo mabusou (click & drag)")  # ステップ1描画

            elif self.k_step == 1:  # 油に入れる
                screen.blit(self.cook_img[2], self.rct_oil)  # 油の描画
                bird.update(screen)  # 粉まみれこうかとんの描画
                self.draw_step(screen, "step2.Abura ni ireyou (click & drag)")  # ステップ2描画

            elif self.k_step == 2:  # 完成
                img_rct3 = self.cook_img[3].get_rect(center=(WIDTH//2, HEIGHT//2))  # からあげの位置調整
                screen.blit(self.cook_img[3], img_rct3)  # からあげの描画
                self.draw_step(screen, "kansei! (enter)")  # ステップ3描画

        # ---親子丼が選ばれた時の処理---
        elif self.select == 1:
            if self.k_step == 0:  # フライパンにこうかとんを入れる
                screen.blit(self.img_h, self.rct_h)  # フライパンの描画
                bird.update(screen)  # 移動するこうかとんを描画
                self.draw_step(screen, "step1.Koukaton wo Huraipan ni ireyou (click & drag)")  # ステップ1描画

            elif self.k_step == 1:  # こうかとんに卵をかける
                screen.blit(self.img_h, self.rct_h)  # フライパンの描画
                bird.update(screen)  # こうかとんの描画

                if self.type_egg == 0:  # 通常の卵を使用した場合
                    screen.blit(self.cook_img[5], self.rct_egg)
                elif self.type_egg == 1:  # 次世代卵を使用した場合
                    screen.blit(self.cook_img[6], self.rct_next_egg)

                self.draw_step(screen, "step2.Tamago wo ireyou (click & drag)")  # ステップ2描画

            elif self.k_step == 2:  # ご飯に乗せる
                screen.blit(self.img_h, self.rct_h)  # フライパンの描画
                rct_eggbird = self.cook_img[11].get_rect(center=bird.rct.center)  # 卵付きこうかとんの中心位置をこうかとんの位置に調整
                screen.blit(self.cook_img[11], rct_eggbird)  # 卵つきこうかとんの描画
    
                self.draw_step(screen, "step3.Gohan ni noseyou (next:enter)")  # ステップ3描画

            elif self.k_step == 3:  # 完成
                img_rct8 = self.cook_img[8].get_rect(center=(WIDTH//2, HEIGHT//2))  # 親子丼の位置調整
                screen.blit(self.cook_img[8], img_rct8)  # 親子丼の描画
                self.draw_step(screen, "Kansei! (enter)")  # ステップ4描画

        # ---丸焼きが選ばれた時の処理---
        elif self.select == 2:
            if self.k_step == 0:  # 爆発させる
                bird.update(screen)  # 動き回るこうかとんの描画
                if self.is_exp:
                    if time.time() - self.exp_time <= 0.5:  # 現在の時刻-爆発開始時間が0.5秒以下なら描画
                        if self.rct_exp.colliderect(bird.rct):  # こうかとんと爆発が重なったら
                            self.k_step = 1
                            bird.is_baku = True  # こうかとんが爆発した状態に
                            self.is_exp = False  # 爆発しているかどうかの判定を終了
                        else:
                            screen.blit(self.img_e, self.rct_exp)  # ぶつかっていないならexp画像表示
                    else:
                        self.is_exp = False  # 0.5秒を超えたら爆発を終了
                self.draw_step(screen, "Bakuhatu saseru (click)")  # ステップ1描画

            elif self.k_step == 1:  # ぶつかった表示
                screen.blit(self.img_e, self.rct_exp)  # exp画像を表示
                bird.update(screen)  # ぶつかった場所で泣いているこうかとんを表示
                self.draw_step(screen, "(enter)")  # ステップ2描画

            elif self.k_step == 2:  # 完成
                img_rct10 = self.cook_img[10].get_rect(center=(WIDTH//2, HEIGHT//2))  # 丸焼きの位置調整
                screen.blit(self.cook_img[10], img_rct10)  # 丸焼きの描画
                self.draw_step(screen, "Kansei! (enter)")  # ステップ4描画

    def mouse(self, event, bird: Bird):
        """
        マウスを使ってアイテムをぶつけたり動かしたりするための処理
        """
        if not self.is_cooking or self.is_select or self.is_select_egg:  # 調理中ではない、料理を選択している、卵を選択している場合
            return  # マウス操作を行わない

        # ---クリックしたときの処理---
        if event.type == pg.MOUSEBUTTONDOWN:  # マウスのボタンが押された場合
            if event.button == 1:  # それが左クリックだった場合

                # ---からあげの場合---
                if self.select == 0:
                    if self.k_step == 0:  # 工程1だった場合：小麦粉をぶつける
                        if self.rct_kona.collidepoint(event.pos):  # クリックした座標が小麦粉.pngのrectの判定内にあった場合
                            self.is_mouse = True  # マウスで掴んでいる状態
                            self.item = "kona"  # 所持アイテム名をkonaに設定
                    elif self.k_step == 1:  # 工程2だった場合
                        if bird.rct.collidepoint(event.pos):  # クリックした座標がこうかとんのrect内にあった場合
                            self.is_mouse = True
                            self.item = "bird"
                            bird.is_grabbed = True  # こうかとんが通常のランダム移動をしないように設定

                # ---親子丼の場合---
                elif self.select == 1:
                    if self.k_step == 0:  # 工程1だった場合：こうかとんを掴む
                        if bird.rct.collidepoint(event.pos):  # クリックされた座標がこうかとんのrect内にあった場合
                            self.is_mouse = True
                            self.item = "bird"
                            bird.is_grabbed = True  # こうかとんがランダム移動しないように設定
                    elif self.k_step == 1:  # 工程2だった場合：卵をぶつける
                        if self.type_egg == 0:  # 通常卵
                            if self.rct_egg.collidepoint(event.pos):  # クリックされた座標が卵のrect内だった場合
                                self.is_mouse = True
                                self.item = "egg"
                        if self.type_egg == 1:  # 次世代卵
                            if self.rct_next_egg.collidepoint(event.pos):
                                self.is_mouse = True
                                self.item = "next_egg"

                # ---丸焼きの場合---
                elif self.select == 2:
                    if self.k_step == 0:  # 工程1の場合：爆発させる
                        if not self.is_exp:  # まだ爆発していない場合
                            self.is_exp = True  # 爆発処理を開始
                            self.exp_time = time.time()  # 爆発開始時刻を取得
                            self.rct_exp = self.img_e.get_rect(center=event.pos)  # exp画像の中心位置をクリックした場所に設定

        # ---マウスを動かしたときの処理---
        elif event.type == pg.MOUSEMOTION:  # マウスが動いた場合
            if self.is_mouse:  # 何かが掴まれている場合
                if self.item == "kona":
                    self.rct_kona.center = event.pos  # 小麦粉の中心位置をマウスの位置に
                elif self.item == "bird":
                    bird.rct.center = event.pos  # こうかとんの中心位置をマウスの位置に
                elif self.item == "egg":
                    self.rct_egg.center = event.pos  # 卵の中心位置をマウスの位置に
                elif self.item == "next_egg":
                    self.rct_next_egg.center = event.pos  # 次世代卵の中心位置をマウスの位置に

        # ---ボタンが離されたときの処理---
        elif event.type == pg.MOUSEBUTTONUP:  # ボタンが離された場合
            if event.button == 1 and self.is_mouse:  # 離されたのがマウスの左ボタンand画像を掴んでいる場合

                if self.item == "kona":
                    if self.rct_kona.colliderect(bird.rct):  # 小麦粉とこうかとんが重なっていた場合
                        self.k_step = 1
                        bird.is_kona = True  # こうかとんを粉まみれの状態に
    
                elif self.item == "bird":
                    if self.select == 0:  # からあげの時
                        if bird.rct.colliderect(self.rct_oil):  # こうかとんと油が重なっていた場合
                            self.k_step = 2
                            bird.rct.center = self.rct_oil.center  # こうかとんの中心座標を油の中心座標に変更
                            bird.is_inho = True  # こうかとんがフライパンに入っている状態に変更
                            self.fin_sound.play()  # 完成した時の音を流す
                            pg.mixer.music.stop()  # BGMを止める
                    if self.select == 1:  # 親子丼のとき
                        if bird.rct.colliderect(self.rct_h):  # こうかとんとフライパンが重なっていた場合
                            self.k_step = 1
                            bird.rct.center = self.rct_h.center  # こうかとんの中心座標をフライパンの中心座標に変更
                            bird.is_inho = True  # こうかとんふが油に入っている状態に変更

                elif self.item == "egg":
                    if self.rct_egg.colliderect(bird.rct):  # 卵と鳥が重なっていた場合
                        self.k_step = 2

                elif self.item == "next_egg":
                    if self.rct_next_egg.colliderect(bird.rct):  # 次世代卵と鳥が重なっていた場合
                        self.k_step = 2

                self.is_mouse = False  # マウスで掴んでいる判定をfalseに
                bird.is_grabbed = False  # こうかとんがランダム移動できるように戻す
                self.item = None  # 所持アイテム情報をリセット

    def next_step(self):
        """
        次の工程へ進ませる処理
        """
        # ---からあげor丸焼きの場合---
        if self.select == 0 or self.select == 2:
            if self.k_step < 2:
                self.k_step += 1

        # ---親子丼の場合---
        elif self.select == 1:
            if self.k_step < 3:
                self.k_step += 1

    def draw_step(self, screen: pg.surface, step_num: str):
        """
        工程を画面中央上部に表示する処理
        """
        text = self.font.render(step_num, True, (255, 255, 255))
        text_rct = text.get_rect(center=(WIDTH//2, 50))
        screen.blit(text, text_rct)


def main():
    pg.display.set_caption("こうかとん育成ゲーム（基本機能）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    cook_icon = pg.image.load("fig/cookアイコン.png")  # 料理アイコン(料理機能で追加)
    sleep_icon = pg.image.load("fig/sleepアイコン.png")  # 睡眠アイコン
    food_icon = pg.image.load("fig/エサやりアイコン.png")  # エサやりアイコン
 
    bird = Bird((WIDTH // 2, HEIGHT // 2))
    status_disp = StatusDisplay()
    clock = pg.time.Clock()

    start_time = time.time()
    last_hp_decay_time = time.time()

    cook = Cook(screen)  # Cookクラスを呼び出してインスタンス化(料理機能で追加)

    while True:
        current_time = time.time()
        if not bird.is_cooked_once:  # 一度調理されたら寿命を停止する(料理機能で追加)
            elapsed_sec = current_time - start_time

        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

            # --- 料理を開始するための処理(料理機能) ---
            if event.type == pg.KEYDOWN:
                # ---卵がないよメッセージを初期化する処理---
                if cook.no_egg_messe != "":  # 卵がないよメッセージが入っている時
                    cook.no_egg_messe = ""  # 卵がないよメッセージをなくす
                
                # ---料理するか確認画面を表示する処理---
                if event.key == pg.K_c and not cook.is_confirm:  # cキーが押されたand確認画面が表示されていない場合
                    cook.is_confirm = True  # 確認画面を表示する
                    cook.confirm_select = 0  # 料理の選択番号を0に(初期値yesに設定)

                # ---料理するか確認する処理---
                elif cook.is_confirm:  # 確認画面が表示されている場合
                    # ---料理するか選択する処理---
                    if event.key == pg.K_UP or event.key == pg.K_DOWN:  # 上下キーで選択
                        if cook.confirm_select == 0:  # 現在yesの場合
                            cook.confirm_select = 1  # キーを押したらnoに
                        else:  # 現在noの場合
                            cook.confirm_select = 0  # キーを押したらyesに変更

                    # ---料理するか選択後の処理---
                    elif event.key == pg.K_RETURN:  # enterが押された場合
                        if cook.confirm_select == 0:  # 料理する(yesだった)場合
                            cook.st_sound.play()  # 「どう料理してやろうかのう.mp3」を流す
                            bird.is_cooked_once = True  # こうかとんが一度料理されたことを記録
                            cook.is_confirm = False  # 確認画面を終了
                            cook.is_cooking = True  # 料理モードを開始する
                            cook.is_select = True  # 料理の選択画面を表示
                            cook.is_select_egg = False  # 卵の選択画面を表示しない
                            cook.select = 0  # 選択肢の初期値をからあげに設定
                            cook.type_egg = 0  # どっちの卵を持っているか判定をリセット
                            cook.k_step = 0  # 調理工程数をリセット
                        else:  # noだった場合
                            cook.is_confirm = False  # そのまま確認画面を閉じる

                # ---卵を選択する処理---
                elif cook.is_cooking and cook.is_select_egg:  # 料理モードand卵の選択画面が表示されている場合
                    # ---卵を選択する処理---
                    if event.key == pg.K_UP or event.key == pg.K_DOWN:  # 上下キーで選択
                        if cook.type_egg == 0:  # 現在が普通卵の場合
                            cook.type_egg = 1  # 次世代卵に
                        else:  # 現在が次世代卵の場合
                            cook.type_egg = 0  # 普通卵に

                    # ---卵選択後の処理---
                    elif event.key == pg.K_RETURN:  # enterが押された場合
                        if cook.type_egg == 0:
                            cook.egg -= 50  # 通常卵の所次数を50減らす
                            pg.mixer.music.load(cook.cook_sound)
                            pg.mixer.music.play(loops=-1)
                        else:
                            cook.is_confirm_nxegg = True  # 本当に使用するか確認する画面表示
                            cook.is_confirm_nxegg_select = 0  # 初期設定をyesに設定
                    
                        cook.is_select_egg = False  # 卵選択画面を閉じる

                # ---次世代卵を使用するか確認する処理---
                elif cook.is_confirm_nxegg:  # 次世代卵を使用するか確認する画面が表示されている場合
                    # ---選択する処理---
                    if event.key == pg.K_UP or event.key == pg.K_DOWN:
                        if cook.is_confirm_nxegg_select == 0:
                            cook.is_confirm_nxegg_select = 1
                        else:
                            cook.is_confirm_nxegg_select = 0

                    # ---選択後の処理---
                    if event.key == pg.K_RETURN:
                        if cook.is_confirm_nxegg_select == 0:
                            cook.next_egg -= 1
                            pg.mixer.music.load(cook.cook_sound)
                            pg.mixer.music.play(loops=-1)
                        else:
                            cook.is_select = True
                        cook.is_select_egg = False  # 卵の選択終了
                        cook.is_confirm_nxegg = False  # 選択する画面を終了

                # ---料理を選択する処理---
                elif cook.is_cooking and cook.is_select:  # 料理モードand料理選択画面が表示されている場合
                    # ---料理を選択する処理---
                    if event.key == pg.K_UP:  # ↑を押して選択肢移動
                        cook.select = (cook.select -1) % 3
                    elif event.key == pg.K_DOWN:  # ↓を押して選択肢移動
                        cook.select = (cook.select + 1) %3

                    # ---料理を選択した後の処理---
                    elif event.key == pg.K_RETURN:  # enterを押した場合
                        # ---からあげの時---
                        if cook.select == 0:
                            cook.rct_kona.center = (WIDTH//2, HEIGHT//2)  # 粉の初期位置をリセット
                            bird.is_kona = False  # こうかとんが粉まみれになっている状態の解除
                            bird.is_inho = False  # こうかとんがフライパンに入っている状態の解除
                            bird.is_grabbed = False  # こうかとんが自由に動き回るようにする
                            cook.is_select = False  # 料理選択画面の終了

                            pg.mixer.music.load(cook.cook_sound)  # 3分クッキングの音源取得
                            pg.mixer.music.play(loops=-1)  # ループ再生


                        # ---親子丼のとき---
                        elif cook.select == 1:
                            cook.rct_egg.center = (200, 250)  # 普通の卵の初期位置リセット
                            cook.rct_next_egg.center = (200, 250)  # 次世代卵の初期位置リセット

                            if cook.egg >= 50 and cook.next_egg >= 1:  # どちらの卵も持っていた場合
                                cook.is_select = False  # 料理選択画面の終了
                                cook.is_select_egg = True  # 卵選択画面を表示
                            elif cook.egg >= 50:  # 通常卵だけ50個もっていた場合
                                cook.type_egg = 0
                                cook.egg -= 50
                                cook.is_select = False  # 卵選択画面を終了
                            elif cook.next_egg >= 1:  # 次世代卵だけもっていた場合
                                cook.type_egg = 1
                                cook.next_egg -= 1
                                cook.is_select = False  # 卵選択画面を終了
                            else:  # 卵の数が足りていなかった場合
                                cook.no_egg_messe = "Tamago ga tarinai!"

                        # ---丸焼きのとき---
                        elif cook.select == 2:
                            bird.is_baku = False  # こうかとんが爆発した状態の解除
                            cook.is_exp = False  # expの表示を解除
                            cook.is_select = False  # 料理選択画面の終了
                            pg.mixer.music.load(cook.cook_sound)  # 3分クッキングの音源取得
                            pg.mixer.music.play(loops=-1)  # ループ再生

                # ---次の工程へ進む処理---
                elif cook.is_cooking and not cook.is_select:  # 料理中かつ選択が終了している場合
                    if event.key == pg.K_RETURN:  # enterを押した場合
                        # ---からあげの時---
                        if cook.select == 0:
                            if cook.k_step == 2:
                                cook.is_cooking = False  # 料理を終了

                        # ---親子丼の時---
                        elif cook.select == 1:
                            if cook.k_step == 2:  # 工程3の場合
                                cook.next_step()  # 次の工程へ進む
                                cook.fin_sound.play()  # 完成した時の音楽を流す
                                pg.mixer.music.stop()  # BGMを止める
                            elif cook.k_step == 3:
                                cook.is_cooking = False  # 料理を終了

                        # ---丸焼きの時---
                        elif cook.select == 2:
                            if cook.k_step == 1:  # 工程2の場合
                                cook.next_step()  # 次の工程へ進む
                                cook.fin_sound.play()  # 完成した時の音楽を流す
                                pg.mixer.music.stop()  # BGMを止める
                            elif cook.k_step == 2:
                                cook.is_cooking = False  # 料理を終了

                        if not cook.is_cooking:  # 料理が終了した場合
                            bird.is_inho = False  # フライパン/油から出ている状態に変更
                            bird.is_grabbed = False  # こうかとんが自由に動き回るようにリセット
                            bird.is_kona = False  # 粉がぶつかっていない状態に変更
                            bird.is_baku = False  # 爆発していない状態に変更

            if event.type == pg.MOUSEBUTTONUP or event.type == pg.MOUSEBUTTONDOWN or event.type == pg.MOUSEMOTION:  # マウス操作がされた場合
                if cook.is_cooking:  # 調理中の場合
                    cook.mouse(event, bird)  # mouseを呼び出して実行

        # --- 1秒ごとに体力を減算 ---
        if not bird.is_cooked_once:  # こうかとんが一度も調理されたことがなかったら体力減算(調理機能で追加)
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
        if cook.is_cooking:  # 料理中の場合(料理機能で追加)
            cook.cook_start(screen, bird)  # cook_startを呼び出す
        else:
            screen.blit(bg_img, [0, 0])
            bird.update(screen)
            screen.blit(cook_icon, (WIDTH-100, HEIGHT-100))
            screen.blit(sleep_icon, (WIDTH-200, HEIGHT-100))
            screen.blit(food_icon, (WIDTH-300, HEIGHT-100))

            if cook.is_confirm:  # 本当に料理するか確認画面の場合(料理機能で追加)
                text = cook.font.render("Hontou ni suru?", True, (255, 255, 255))
                text_rct = text.get_rect(center=(WIDTH//2, 150))
                screen.blit(text, text_rct)

                confirm_list = ["Yes", "No"]  # 確認するためのリスト

                for i, ans in enumerate(confirm_list):  # 色変えるための処理
                    if i == cook.confirm_select:
                        color = (255, 255, 0)
                    else:
                        color = (255, 255, 255)

                    text = cook.font.render(ans, True, color)
                    text_rct = text.get_rect(center=(WIDTH//2, 300 + i * 100))
                    screen.blit(text, text_rct)

        if not bird.is_cooked_once:  # こうかとんが一度も料理されていない場合(料理機能で追加)
            status_disp.update(screen, bird, elapsed_sec)

        pg.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
#!/usr/bin/env python3
"""
GoodNotes用 デジタルプランナー生成スクリプト
================================================
- 年 → 月 → 週 → 日 の階層構造をハイパーリンクで接続
- 日本の祝日対応 (jpholiday)
- フォントファイル不要 (reportlab組み込みCIDフォント使用)

カスタマイズ可能ポイント:
- YEAR        : 対象年
- 配色        : COLOR_* 定数
- ページサイズ : PAGE_SIZE
- タイムライン : draw_day_page() 内の hours レンジ
"""

import calendar
from datetime import date, timedelta
from reportlab.lib.pagesizes import letter, A4, A5
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import jpholiday

# ===== 設定 =====
YEAR = 2026
OUTPUT_FILE = f"goodnotes_planner_{YEAR}.pdf"

# ページサイズ: letter / A4 / A5 から選択
PAGE_SIZE = letter
PAGE_W, PAGE_H = PAGE_SIZE
MARGIN = 30

# カラーパレット (上品な配色)
COLOR_BG      = HexColor("#FAFAF7")
COLOR_TEXT    = HexColor("#2A2A2A")
COLOR_MUTED   = HexColor("#9A9A9A")
COLOR_ACCENT  = HexColor("#3A6EA5")  # 土曜日・リンク
COLOR_HOLIDAY = HexColor("#C73E3E")  # 日曜日・祝日
COLOR_LINE    = HexColor("#D8D8D5")
COLOR_LINE_LT = HexColor("#EEEEEE")

# 日本語フォント (CID, ファイル不要)
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
F_JP  = 'HeiseiKakuGo-W5'   # 見出し用
F_JPM = 'HeiseiMin-W3'      # 本文用

WEEKDAY_JP = ['月', '火', '水', '木', '金', '土', '日']
MONTH_EN = ['January','February','March','April','May','June',
            'July','August','September','October','November','December']

# ===== ブックマークキー =====
def k_year():        return f"year_{YEAR}"
def k_month(m):      return f"month_{YEAR}_{m:02d}"
def k_week(monday):  return f"week_{monday.isoformat()}"
def k_day(d):        return f"day_{d.isoformat()}"

# ===== ヘルパー =====
def link(c, x, y, w, h, dest):
    """指定範囲を内部リンクにする (枠線非表示)"""
    c.linkRect("", dest, (x, y, x+w, y+h), relative=0, thickness=0)

def hol_name(d):
    return jpholiday.is_holiday_name(d)

def fill_for_day(d, weekday_idx):
    """日付の文字色を返す (祝日/日曜→赤、土曜→青、平日→黒)"""
    if hol_name(d) or weekday_idx == 6:
        return COLOR_HOLIDAY
    if weekday_idx == 5:
        return COLOR_ACCENT
    return COLOR_TEXT

# ===== 年ページ =====
def draw_year_page(c):
    c.bookmarkPage(k_year())
    c.setFillColor(COLOR_BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # ヘッダー
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 42)
    c.drawCentredString(PAGE_W/2, PAGE_H - 70, f"{YEAR}")
    c.setFont(F_JPM, 12)
    c.setFillColor(COLOR_MUTED)
    c.drawCentredString(PAGE_W/2, PAGE_H - 90, "Yearly Calendar")

    # 12ヶ月を 3列×4行 で配置
    grid_top = PAGE_H - 120
    grid_h = grid_top - MARGIN - 20
    cols, rows = 3, 4
    cell_w = (PAGE_W - 2*MARGIN) / cols
    cell_h = grid_h / rows

    for m in range(1, 13):
        row = (m-1) // cols
        col = (m-1) % cols
        x = MARGIN + col * cell_w
        y = grid_top - (row+1) * cell_h
        _draw_mini_month(c, m, x, y, cell_w, cell_h)
        link(c, x+4, y+4, cell_w-8, cell_h-8, k_month(m))

def _draw_mini_month(c, month, x, y, w, h):
    pad = 10
    # 月見出し
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 13)
    c.drawString(x + pad, y + h - 18, f"{month}")
    c.setFont(F_JPM, 9)
    c.setFillColor(COLOR_MUTED)
    c.drawString(x + pad + 22, y + h - 18, MONTH_EN[month-1])

    cal = calendar.Calendar(firstweekday=0)  # 月曜始まり
    cell_size = (w - 2*pad) / 7
    header_y = y + h - 36

    # 曜日ヘッダー
    c.setFont(F_JP, 7)
    for i, wd in enumerate(WEEKDAY_JP):
        if i == 5:   c.setFillColor(COLOR_ACCENT)
        elif i == 6: c.setFillColor(COLOR_HOLIDAY)
        else:        c.setFillColor(COLOR_MUTED)
        c.drawCentredString(x + pad + cell_size*(i+0.5), header_y, wd)

    # 日付
    weeks = cal.monthdayscalendar(YEAR, month)
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day == 0:
                continue
            cy = header_y - (wi+1) * 11 - 2
            d = date(YEAR, month, day)
            c.setFillColor(fill_for_day(d, di))
            c.setFont(F_JP, 7.5)
            c.drawCentredString(x + pad + cell_size*(di+0.5), cy, str(day))

    # 枠
    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(0.5)
    c.rect(x+4, y+4, w-8, h-8, fill=0, stroke=1)


# ===== 月ページ =====
def draw_month_page(c, month):
    c.bookmarkPage(k_month(month))
    c.setFillColor(COLOR_BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # ヘッダー
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 28)
    c.drawString(MARGIN, PAGE_H - 55, f"{YEAR}年 {month}月")
    c.setFont(F_JPM, 11)
    c.setFillColor(COLOR_MUTED)
    c.drawString(MARGIN, PAGE_H - 73, MONTH_EN[month-1])

    # 右上: 年へ戻る
    _nav_link(c, PAGE_W - MARGIN, PAGE_H - 55, f"← {YEAR}", k_year(), align='right')

    # 前月/次月
    if month > 1:
        _nav_link(c, MARGIN, PAGE_H - 95, f"← {month-1}月", k_month(month-1), align='left')
    if month < 12:
        _nav_link(c, PAGE_W - MARGIN, PAGE_H - 95, f"{month+1}月 →", k_month(month+1), align='right')

    # カレンダーグリッド
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(YEAR, month)

    grid_top = PAGE_H - 120
    grid_bottom = MARGIN + 100  # 下部ノートエリア用
    cell_w = (PAGE_W - 2*MARGIN) / 7

    # 曜日ヘッダー
    c.setFont(F_JP, 11)
    for i, wd in enumerate(WEEKDAY_JP):
        if i == 5:   c.setFillColor(COLOR_ACCENT)
        elif i == 6: c.setFillColor(COLOR_HOLIDAY)
        else:        c.setFillColor(COLOR_TEXT)
        c.drawCentredString(MARGIN + cell_w*(i+0.5), grid_top - 14, wd)

    grid_top -= 25
    cell_h = (grid_top - grid_bottom) / len(weeks)

    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(0.5)

    for wi, week in enumerate(weeks):
        for di, d in enumerate(week):
            x = MARGIN + di * cell_w
            y = grid_top - (wi+1) * cell_h

            # セル枠
            c.rect(x, y, cell_w, cell_h, fill=0, stroke=1)

            # 当月以外はミュート色
            if d.month != month:
                c.setFillColor(COLOR_MUTED)
            else:
                c.setFillColor(fill_for_day(d, di))

            c.setFont(F_JP, 13)
            c.drawString(x + 5, y + cell_h - 15, str(d.day))

            # 祝日名
            hn = hol_name(d)
            if hn and d.month == month:
                c.setFillColor(COLOR_HOLIDAY)
                c.setFont(F_JPM, 6.5)
                c.drawString(x + 5, y + cell_h - 26, hn[:9])

            # 当月の日のみクリックで日次へ
            if d.month == month:
                link(c, x, y, cell_w, cell_h, k_day(d))

    # 下部ノートエリア
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 11)
    c.drawString(MARGIN, grid_bottom - 25, "Monthly Notes")
    c.setStrokeColor(COLOR_LINE)
    for i in range(4):
        ly = grid_bottom - 40 - i*16
        c.line(MARGIN, ly, PAGE_W - MARGIN, ly)


def _nav_link(c, x, y, text, dest, align='left', size=10):
    c.setFont(F_JPM, size)
    c.setFillColor(COLOR_ACCENT)
    if align == 'right':
        c.drawRightString(x, y, text)
        tw = c.stringWidth(text, F_JPM, size)
        link(c, x - tw - 5, y - 5, tw + 10, size + 8, dest)
    else:
        c.drawString(x, y, text)
        tw = c.stringWidth(text, F_JPM, size)
        link(c, x - 3, y - 5, tw + 8, size + 8, dest)


# ===== 週ページ =====
def draw_week_page(c, monday):
    c.bookmarkPage(k_week(monday))
    c.setFillColor(COLOR_BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    week_num = monday.isocalendar()[1]
    sunday = monday + timedelta(days=6)

    # ヘッダー
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 22)
    c.drawString(MARGIN, PAGE_H - 50, f"Week {week_num}")
    c.setFont(F_JPM, 11)
    c.setFillColor(COLOR_MUTED)
    c.drawString(MARGIN, PAGE_H - 68, f"{monday.strftime('%m/%d')} – {sunday.strftime('%m/%d')}")

    # ナビ: 月へ
    _nav_link(c, PAGE_W - MARGIN, PAGE_H - 50, f"↑ {monday.month}月", k_month(monday.month), align='right')
    # 前週/次週
    prev_mon = monday - timedelta(days=7)
    next_mon = monday + timedelta(days=7)
    if prev_mon.year == YEAR or (prev_mon.year < YEAR and prev_mon + timedelta(days=6) >= date(YEAR,1,1)):
        _nav_link(c, MARGIN, PAGE_H - 88, "← 前週", k_week(prev_mon), align='left')
    if next_mon <= date(YEAR, 12, 31):
        _nav_link(c, PAGE_W - MARGIN, PAGE_H - 88, "次週 →", k_week(next_mon), align='right')

    # 7日 縦カラム (上半分)
    grid_top = PAGE_H - 110
    grid_bottom = MARGIN + 30
    grid_h = grid_top - grid_bottom
    summary_h = grid_h * 0.55
    col_w = (PAGE_W - 2*MARGIN) / 7

    c.setStrokeColor(COLOR_LINE)
    c.setLineWidth(0.5)

    for i in range(7):
        d = monday + timedelta(days=i)
        x = MARGIN + i * col_w
        y_top = grid_top
        y_bot = grid_top - summary_h

        c.setFillColor(fill_for_day(d, i))
        c.setFont(F_JP, 16)
        c.drawString(x + 6, y_top - 18, str(d.day))
        c.setFont(F_JPM, 9)
        c.drawString(x + 6, y_top - 32, f"{d.month}/{d.day} {WEEKDAY_JP[i]}")

        hn = hol_name(d)
        if hn:
            c.setFillColor(COLOR_HOLIDAY)
            c.setFont(F_JPM, 6.5)
            c.drawString(x + 6, y_top - 44, hn[:8])

        # 区切り線
        c.setStrokeColor(COLOR_LINE)
        c.line(x, y_bot, x + col_w, y_bot)
        if i < 6:
            c.line(x + col_w, y_top, x + col_w, y_bot)
        # メモ用うすい罫線
        c.setStrokeColor(COLOR_LINE_LT)
        for j in range(4):
            ly = y_top - 55 - j * 18
            if ly > y_bot + 5:
                c.line(x + 4, ly, x + col_w - 4, ly)

        # クリック → 日次 (年内の日のみ)
        if d.year == YEAR:
            link(c, x, y_bot, col_w, summary_h, k_day(d))

    # 下半分: ウィークリーフォーカス/メモ
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 11)
    c.drawString(MARGIN, grid_top - summary_h - 22, "Weekly Focus / Notes")

    line_top = grid_top - summary_h - 42
    n_lines = int((line_top - grid_bottom) / 18)
    c.setStrokeColor(COLOR_LINE)
    for i in range(n_lines):
        ly = line_top - i * 18
        c.line(MARGIN, ly, PAGE_W - MARGIN, ly)


# ===== 日ページ =====
def draw_day_page(c, d):
    c.bookmarkPage(k_day(d))
    c.setFillColor(COLOR_BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    wd_idx = d.weekday()

    # ヘッダー
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 26)
    c.drawString(MARGIN, PAGE_H - 50, f"{d.month}月{d.day}日")

    c.setFont(F_JPM, 11)
    c.setFillColor(fill_for_day(d, wd_idx))
    c.drawString(MARGIN, PAGE_H - 68, f"{WEEKDAY_JP[wd_idx]}曜日")
    hn = hol_name(d)
    if hn:
        c.setFillColor(COLOR_HOLIDAY)
        c.setFont(F_JPM, 10)
        c.drawString(MARGIN + 60, PAGE_H - 68, f"・{hn}")

    # ナビ: 月・週へ
    _nav_link(c, PAGE_W - MARGIN, PAGE_H - 50, f"↑ {d.month}月", k_month(d.month), align='right')
    monday = d - timedelta(days=d.weekday())
    _nav_link(c, PAGE_W - MARGIN, PAGE_H - 68, f"↑ Week {d.isocalendar()[1]}", k_week(monday), align='right')

    # 前日/翌日
    prev_d = d - timedelta(days=1)
    next_d = d + timedelta(days=1)
    if prev_d.year == YEAR:
        _nav_link(c, MARGIN, PAGE_H - 92, f"← {prev_d.month}/{prev_d.day}", k_day(prev_d), align='left')
    if next_d.year == YEAR:
        _nav_link(c, PAGE_W - MARGIN, PAGE_H - 92, f"{next_d.month}/{next_d.day} →", k_day(next_d), align='right')

    # ===== 左カラム: タイムライン (6:00 - 23:00) =====
    timeline_x = MARGIN
    timeline_top = PAGE_H - 120
    timeline_bottom = MARGIN + 30
    timeline_w = (PAGE_W - 2*MARGIN) * 0.45

    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 11)
    c.drawString(timeline_x, timeline_top + 5, "Schedule")

    hours = list(range(6, 24))
    n_hours = len(hours)
    line_h = (timeline_top - timeline_bottom) / n_hours

    c.setFont(F_JPM, 8)
    for i, h in enumerate(hours):
        y = timeline_top - i * line_h
        c.setFillColor(COLOR_MUTED)
        c.drawRightString(timeline_x + 22, y - 3, f"{h:02d}")
        # 整時線
        c.setStrokeColor(COLOR_LINE)
        c.setLineWidth(0.5)
        c.line(timeline_x + 28, y, timeline_x + timeline_w, y)
        # 30分線 (薄く)
        c.setStrokeColor(COLOR_LINE_LT)
        c.line(timeline_x + 28, y - line_h/2, timeline_x + timeline_w, y - line_h/2)

    # ===== 右カラム: To Do / Notes =====
    right_x = MARGIN + timeline_w + 25
    right_w = PAGE_W - right_x - MARGIN

    # To Do
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 11)
    c.drawString(right_x, timeline_top + 5, "To Do")

    todo_top = timeline_top - 10
    todo_bottom = timeline_top - (timeline_top - timeline_bottom) * 0.5
    n_todos = int((todo_top - todo_bottom) / 22)
    c.setStrokeColor(COLOR_LINE)
    for i in range(n_todos):
        ty = todo_top - i * 22
        c.rect(right_x, ty - 12, 10, 10, fill=0, stroke=1)
        c.line(right_x + 16, ty - 14, right_x + right_w, ty - 14)

    # Notes
    c.setFillColor(COLOR_TEXT)
    c.setFont(F_JP, 11)
    c.drawString(right_x, todo_bottom - 8, "Notes")

    note_top = todo_bottom - 25
    n_notes = int((note_top - timeline_bottom) / 18)
    c.setStrokeColor(COLOR_LINE)
    for i in range(n_notes):
        ny = note_top - i * 18
        c.line(right_x, ny, right_x + right_w, ny)


# ===== メイン =====
def main():
    c = canvas.Canvas(OUTPUT_FILE, pagesize=PAGE_SIZE)
    c.setTitle(f"{YEAR} Digital Planner")
    c.setAuthor("Yuhei Komiya")

    # 1. 年ページ
    draw_year_page(c)
    c.showPage()

    # 2. 月ページ × 12
    for m in range(1, 13):
        draw_month_page(c, m)
        c.showPage()

    # 3. 週ページ (年内に1日でも含まれる週すべて)
    start = date(YEAR, 1, 1)
    end = date(YEAR, 12, 31)
    monday = start - timedelta(days=start.weekday())
    week_count = 0
    while monday <= end:
        draw_week_page(c, monday)
        c.showPage()
        monday += timedelta(days=7)
        week_count += 1

    # 4. 日ページ × 365 (or 366)
    d = start
    day_count = 0
    while d <= end:
        draw_day_page(c, d)
        c.showPage()
        d += timedelta(days=1)
        day_count += 1

    c.save()
    total = 1 + 12 + week_count + day_count
    print(f"✓ Generated: {OUTPUT_FILE}")
    print(f"  Year: 1, Month: 12, Week: {week_count}, Day: {day_count}")
    print(f"  Total pages: {total}")

if __name__ == "__main__":
    main()

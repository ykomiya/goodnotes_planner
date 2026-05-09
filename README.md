# goodnotes-planner

A Python script that generates a hyperlinked digital planner PDF designed for GoodNotes (and any PDF reader that supports internal links).

## Features

- **4-level hierarchical navigation** via PDF internal links: Year → Month → Week → Day
- **365 daily pages** with hourly schedule, to-do checkboxes, and notes
- **53 weekly pages** with 7-day columns and weekly focus area
- **12 monthly pages** with full grid and monthly notes
- **1 yearly overview** with 12 mini-calendars
- **Japanese holidays** highlighted automatically (via `jpholiday`)
- **No font files required** — uses reportlab's built-in CID fonts

## Requirements

- Python 3.9+
- `reportlab`
- `jpholiday`

## Usage

```bash
pip install reportlab jpholiday
python goodnotes_planner.py
```

Outputs `goodnotes_planner_2026.pdf` (~430 pages). Import into GoodNotes as a **New Document**.

## Customization

Edit constants at the top of the script:
- `YEAR` — target year
- `PAGE_SIZE` — letter / A4 / A5
- `COLOR_*` — color palette
- Timeline hours in `draw_day_page()`

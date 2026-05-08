# Desktop1QC — ระบบประกันคุณภาพจอภาพทางการแพทย์ (TG-270 Monitor QC System)

โปรแกรม Desktop QC สำหรับประเมินคุณภาพจอภาพทางการแพทย์ตามมาตรฐาน **TG-270** รองรับ 3 ชนิดหน้าจอ ครอบคลุมทุกรอบการประเมิน บันทึกผลลงฐานข้อมูล และสร้างรายงาน PDF/Excel

---

## Tech Stack

| ส่วน | รายละเอียด |
|------|-----------|
| ภาษา | Python 3.11 |
| GUI | Tkinter (built-in) |
| รูปภาพ | Pillow (PIL) |
| PDF | ReportLab + THSarabunNew.ttf |
| Excel | openpyxl |
| ฐานข้อมูล | SQLite (`data/screenqc.db`) |
| Build | PyInstaller (onedir) — Windows EXE & macOS .app |
| CI/CD | GitHub Actions (push → main → build artifacts) |

---

## วิธีรันโปรแกรม

```bash
# ติดตั้ง dependencies
pip install pillow reportlab openpyxl

# รัน
python main.py
```

---

## โครงสร้างไฟล์

```
Desktop1QC/
├── main.py              # Entry point — ติดตั้งฟอนต์ไทย, สร้าง Tk window, ลงทะเบียน screens
├── config.py            # TEST_CONFIG, SCREEN_TYPES, PERIODS, PERIOD_LABELS
├── app.py               # มี TEST_CONFIG ชุดที่ 2 (คนละชุดกับ config.py — ระวังซ้ำซ้อน)
├── database.py          # SQLite ORM-like: init_db, users, evaluations, answers
├── patterns.py          # สร้าง test pattern image แบบ fallback ด้วย Pillow
│
├── screens/
│   ├── base.py          # BaseScreen, color constants, thai_font(), rich_label(), helpers
│   ├── home.py          # หน้าแรก (โลโก้ + ปุ่มนำทาง)
│   ├── select_type.py   # เลือกชนิดหน้าจอ
│   ├── select_period.py # เลือกรอบการประเมิน (พร้อม color bar แสดงสี period)
│   ├── login.py         # ล็อกอิน + แสดงข้อมูลโรงพยาบาล/หน้าจอ
│   ├── confirm.py       # ยืนยัน metadata ก่อนเริ่มทดสอบ
│   ├── instructions.py  # คำแนะนำก่อนทดสอบ (warm-up, ระยะดู, ทำความสะอาด)
│   ├── test_runner.py   # หน้าทำข้อสอบ — แสดงรูป, ตอบ yes/no, ระบุช่องที่ fail
│   ├── results.py       # ตารางผลการประเมิน (pass/fail รายข้อ) — Canvas-based
│   ├── after_save.py    # สรุปหลังบันทึก — ตั้ง baseline, พิมพ์, ดูเกณฑ์
│   ├── criteria.py      # ตารางเกณฑ์การประเมินและวิธีแก้ไข (กรองตามชนิดหน้าจอ)
│   ├── comparison.py    # เปรียบเทียบผลกับ baseline — export PDF
│   ├── history.py       # ค้นหาประวัติการประเมิน (filter วันที่)
│   ├── history_result.py# ดูผลการประเมินในอดีต (Canvas-based)
│   ├── register.py      # ตั้งค่าครั้งแรก (ชื่อโรงพยาบาล, รุ่นหน้าจอ, สร้าง user แรก)
│   └── user_list.py     # จัดการผู้ใช้ (เพิ่ม/แก้ไข/ลบ)
│
├── assets/
│   ├── fonts/THSarabunNew.ttf   # ฟอนต์ไทย (bundled)
│   ├── logo/                    # โลโก้แอป (.png, .icns, .ico)
│   └── test_patterns/           # รูปแบบทดสอบ ~30 ไฟล์ (PNG/TIFF)
│
├── reports/
│   └── pdf_export.py    # สร้าง PDF ด้วย ReportLab (landscape A4)
│
├── scripts/
│   └── create_ico.py    # แปลง PNG → ICO สำหรับ Windows
│
└── data/
    └── screenqc.db      # SQLite database (สร้างอัตโนมัติเมื่อรันครั้งแรก)
```

---

## config.py — โครงสร้างข้อมูลหลัก

### ชนิดหน้าจอ (`SCREEN_TYPES`)
| key | ความหมาย |
|-----|----------|
| `diagnostic` | หน้าจอชนิดใช้วินิจฉัยทางการแพทย์ (Diagnostic) |
| `modality` | หน้าจอชนิดใช้แสดงทางการแพทย์ (Modality) |
| `clinic` | หน้าจอตรวจทานทางการแพทย์ / EHR |

### รอบการประเมิน (`PERIODS`)
| ชนิดหน้าจอ | รอบที่รองรับ |
|-----------|------------|
| diagnostic | monthly, quarterly |
| modality | monthly, quarterly, annual |
| clinic | annual |

### `TEST_CONFIG` — โครงสร้างแต่ละ test item
```python
{
    "item_id":        "diag_lum_patches_m",      # unique ID สำหรับบันทึก DB
    "title":          "1.1) การประเมิน...",       # หัวข้อที่แสดงในหน้าทดสอบ
    "image_index":    1,                           # ชี้ไปยัง assets/test_patterns/
    "question_type":  "yes_no",                   # "yes_no" หรือ "yes_no_channels"
    "total_channels": 18,                          # (เฉพาะ yes_no_channels)
    "pass_criterion": "...",                       # เกณฑ์ผ่าน (รองรับ <u>text</u>)
    "fix_guide":      "...",                       # วิธีแก้ไขกรณีไม่ผ่าน
    "cmp_drift":      "A",                         # A หรือ B (ประเภทการเปรียบเทียบ)
}
```

**Markup รองรับใน `pass_criterion`:** `<u>ข้อความ</u>` → แสดงขีดเส้นใต้ในหน้า criteria

---

## Database Schema

```sql
-- ข้อมูลโรงพยาบาล/หน้าจอ (1 row)
CREATE TABLE settings (
    id            INTEGER PRIMARY KEY,
    hospital_name TEXT NOT NULL,
    screen_model  TEXT NOT NULL
);

-- ผู้ใช้งาน
CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    lastname TEXT NOT NULL DEFAULT '',
    password TEXT NOT NULL
);

-- บันทึกการประเมินแต่ละครั้ง
CREATE TABLE evaluations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name   TEXT    NOT NULL,
    evaluator_name  TEXT    NOT NULL,
    screen_model    TEXT    NOT NULL,
    screen_type     TEXT    NOT NULL,  -- diagnostic / modality / clinic
    period          TEXT    NOT NULL,  -- monthly / quarterly / annual
    eval_datetime   TEXT    NOT NULL,  -- "DD/MM/YYYY HH:MM"
    overall_pass    INTEGER NOT NULL,  -- 1=ผ่าน, 0=ไม่ผ่าน
    is_baseline     INTEGER NOT NULL DEFAULT 0  -- 1=กำหนดเป็น baseline
);

-- คำตอบรายข้อ
CREATE TABLE answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id   INTEGER NOT NULL REFERENCES evaluations(id),
    item_id         TEXT    NOT NULL,  -- ตรงกับ config item_id
    passed          INTEGER NOT NULL,  -- 1=ผ่าน, 0=ไม่ผ่าน
    failed_channels TEXT    NOT NULL DEFAULT '[]',  -- JSON array ช่องที่ไม่ผ่าน
    notes           TEXT    NOT NULL DEFAULT ''
);
```

**ตำแหน่ง DB:**
- Dev: `<project>/data/screenqc.db`
- macOS bundle: `~/Library/Application Support/DesktopQC/data/screenqc.db`
- Windows bundle: `%APPDATA%/DesktopQC/data/screenqc.db`

---

## Flow การทำงาน (User Journey)

```
home → select_type → select_period → login → confirm → instructions
  → test_runner → results → after_save
                               ↓
              [comparison / criteria / history / history_result]
```

1. **home** — เลือกเริ่มประเมิน หรือดูประวัติ หรือจัดการผู้ใช้
2. **select_type** — เลือกชนิดหน้าจอ (3 แบบ)
3. **select_period** — เลือกรอบ (แสดง color bar ตาม period)
4. **login** — ใส่รหัสผ่าน
5. **confirm** — ยืนยันข้อมูลก่อนเริ่ม
6. **instructions** — อ่านคำแนะนำ
7. **test_runner** — ทำข้อสอบทีละข้อ (แสดงรูป + ตอบคำถาม)
8. **results** — ดูผล pass/fail รายข้อ
9. **after_save** — บันทึก DB, เลือกตั้ง baseline, พิมพ์, ดูเกณฑ์

---

## ฟีเจอร์สำคัญ

| ฟีเจอร์ | รายละเอียด |
|---------|-----------|
| **Multi-user** | หลายผู้ใช้ มี password; จัดการผ่าน user_list screen |
| **Test runner** | แสดง test pattern PNG/TIFF, slider เลือก frame, ตอบ yes/no |
| **Channel tracking** | บันทึกช่องที่ fail (18 ช่อง) ด้วย JSON array ใน DB |
| **Baseline** | กำหนดผลการประเมินใดก็ได้เป็น baseline สำหรับเปรียบเทียบ |
| **Comparison** | เทียบผลปัจจุบัน vs baseline ทีละข้อ แยก drift A/B |
| **History** | ค้นหาประวัติด้วย date range filter |
| **PDF report** | สร้าง PDF landscape A4 ด้วย ReportLab + ฟอนต์ไทย |
| **Excel export** | export ผลเป็น .xlsx ด้วย openpyxl |
| **Rich text** | `<u>text</u>` ใน pass_criterion → ขีดเส้นใต้ในหน้า criteria |
| **Canvas table** | results & history_result ใช้ Canvas-based table (text wrap) |
| **Responsive UI** | scale ทุก font/size จาก reference 1920×1080 |

---

## screens/base.py — Utilities สำคัญ

| Function/Class | ใช้ทำอะไร |
|---------------|----------|
| `thai_font(size, weight)` | คืน tuple font ที่ถูกต้องตาม OS (macOS/Windows/Linux) |
| `rich_label(parent, text, ...)` | สร้าง Label ธรรมดา หรือ Text widget (กรณีมี `<u>`) |
| `strip_markup(text)` | ลบ `<u>` tags ออก (ใช้ใน test_runner ที่เป็น plain Label) |
| `bind_treeview_tooltip(tree)` | แสดง tooltip ข้อความเต็มเมื่อ hover Treeview |
| `BaseScreen.primary_btn()` | ปุ่มสีส้มมาตรฐาน |
| `BaseScreen.card_header()` | header แถบสีเข้มบน card |
| `BaseScreen.confirm_dialog()` | dialog ยืนยัน yes/no |

---

## การ Build

```bash
# Windows
pyinstaller --noconfirm --onedir --windowed --name "DesktopQC" \
  --add-data "assets;assets" --add-data "screens;screens" --add-data "reports;reports" \
  --hidden-import "PIL._tkinter_finder" main.py

# macOS
pyinstaller --noconfirm --onedir --windowed --name "DesktopQC" \
  --add-data "assets:assets" --add-data "screens:screens" --add-data "reports:reports" \
  --hidden-import "PIL._tkinter_finder" main.py
```

GitHub Actions build อัตโนมัติทุก push to main → สร้าง artifacts `DesktopQC-windows.zip` และ `DesktopQC-macos.zip`

---

## สิ่งที่เคยแก้ไขในโปรเจกต์นี้

| การเปลี่ยนแปลง | ไฟล์ที่เกี่ยวข้อง |
|---------------|----------------|
| เพิ่ม color bar ใน login screen และปุ่ม period มีสี | `screens/login.py`, `screens/select_period.py` |
| เปลี่ยน Treeview เป็น Canvas-based table (รองรับ text wrap) | `screens/results.py`, `screens/history_result.py` |
| เพิ่ม tooltip แสดงข้อความเต็มเมื่อ hover ใน Treeview | `screens/base.py` |
| รองรับ `<u>text</u>` markup ใน pass_criterion (ขีดเส้นใต้) | `screens/base.py`, `screens/criteria.py`, `screens/test_runner.py` |
| ขีดเส้นใต้คำว่า "เปิดไฟ" ใน item `diag_amb_lum_3m` | `config.py` line 87 |
| แก้ Windows build เป็น onedir (แก้ temp dir cleanup warning) | `.github/workflows/build.yml` |
| อัปเกรด GitHub Actions เป็น Node.js 24 compatible | `.github/workflows/build.yml` |

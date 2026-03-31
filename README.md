# D2R Item Database (D2R物品数据库)

A web-based item database and inventory management system for Diablo 2 Resurrected (暗黑破坏神2 重置版).

## Features

- **Item Query**: Search and browse weapons, armor, unique items, set items, runes, gems, and misc items
- **My Items**: Track your personal item inventory across multiple battle.net accounts
- **Account & Character Management**: Manage multiple battle.net accounts and their characters
- **OCR Support**: Extract item information from screenshots using EasyOCR or Google Gemini API
- **Bilingual UI**: Full support for Chinese (中文) and English

## Data Source

Item data is sourced from [ZHIQUANLIU/D2R-Excel](https://github.com/ZHIQUANLIU/D2R-Excel), a comprehensive Diablo 2 Resurrected data repository.

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **OCR**: EasyOCR / Google Gemini API

## Installation

1. Install dependencies:
```bash
pip install flask easyocr
```

2. (Optional) For Gemini OCR, get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

3. Initialize the database:
```bash
python import_db.py
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Open browser at `http://localhost:5000`

3. Configure OCR settings at `/settings` (optional)

4. Add accounts and characters at `/accounts`

5. Start tracking your items at `/my-items/add`

## Project Structure

```
D2RItemDB/
├── app.py              # Main Flask application
├── ocr_utils.py        # OCR utilities
├── import_db.py        # Database initialization script
├── settings.json       # User settings
├── d2r_items.db        # SQLite database
├── static/uploads/     # Uploaded item images
└── data/               # Game data files
```

## Database Tables

- `weapons` - Weapon items
- `armor` - Armor items  
- `unique_items` - Unique (暗金) items
- `set_items` - Set (套装) items
- `misc` - Miscellaneous items
- `gems` - Gems
- `runes` - Runes
- `accounts` - Battle.net accounts
- `characters` - Characters
- `my_items` - User's tracked items
- `item_images` - Uploaded item screenshots

## License

MIT License

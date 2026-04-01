<div align="center">
  <img src="images/banner.png" alt="D2R Item Database Banner" width="100%">
  
  # ⚔️ D2R Item Database (D2R物品数据库)
  
  *A comprehensive web-based item database and inventory management system for Diablo 2 Resurrected.*

  [![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-Web%20Framework-lightgrey.svg)](https://flask.palletsprojects.com/)
  [![SQLite](https://img.shields.io/badge/SQLite-Database-green.svg)](https://www.sqlite.org/)
  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
</div>

---

## 🎨 Theme System

Choose from 2 high-contrast themes optimized for readability:

- **🌙 Dark Mode** - Professional dark theme with high contrast for comfortable gaming sessions
- **☀️ Light Mode** - Clean bright theme with excellent readability for daytime use

**Theme Features:**
- 🎯 High-contrast color schemes for optimal readability
- 💾 Persistent theme preferences (saved locally)
- 🌐 Bilingual theme names (中文/English)
- 📱 Responsive design across all devices
- ⚡ Instant theme switching without page reload

## 📊 Data Source

All item data is meticulously sourced from [ZHIQUANLIU/D2R-Excel](https://github.com/ZHIQUANLIU/D2R-Excel), a comprehensive Diablo 2 Resurrected data repository.

## 🛠️ Tech Stack

- **Backend**: Python with Flask
- **Database**: SQLite with indexing and optimization
- **OCR Engine**: EasyOCR / Google Gemini API
- **Frontend**: Custom HTML/CSS with CSS Variables for theming
- **Authentication**: Werkzeug security for password hashing
- **Session Management**: Flask-Session with secure configuration

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### 1. Clone and Install
```bash
git clone <repository-url>
cd D2RItemDB
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Security (REQUIRED)
SECRET_KEY=your_secure_random_secret_key_here
ENVIRONMENT=development

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# OCR Settings
OCR_METHOD=gemini

# Database
DATABASE_URL=sqlite:///d2r_items.db

# Server
HOST=127.0.0.1
PORT=5000
```

### 3. Initialize Database
```bash
python import_db.py
```

### 4. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 🔒 Security Features

This application includes several security improvements:

- **User Authentication**: Secure login/registration system with password hashing using Werkzeug
- **SQL Injection Protection**: All database queries use parameterized statements
- **Input Validation**: Comprehensive validation of user inputs with sanitization
- **Session Security**: Secure session management with proper configuration and CSRF protection
- **File Upload Security**: Safe file handling with type validation and size limits
- **Rate Limiting**: Protection against abuse (configurable)
- **Environment Variables**: Sensitive data stored securely in environment files
- **Database Isolation**: User data properly isolated with foreign key constraints
- **Error Handling**: Secure error pages that don't leak sensitive information

---

## 🆕 Recent Optimizations

### Security Enhancements
- ✅ Fixed all SQL injection vulnerabilities
- ✅ Implemented user authentication and authorization
- ✅ Removed hardcoded API keys and secrets
- ✅ Added input validation and sanitization
- ✅ Secure session configuration

### Performance Improvements
- ✅ Added database indexes for better query performance
- ✅ Implemented parameterized queries to prevent SQL injection
- ✅ Added image caching to reduce duplicate OCR processing
- ✅ Optimized database connection handling

### Code Quality
- ✅ Modular code structure with proper separation of concerns
- ✅ Comprehensive error handling
- ✅ Type safety improvements
- ✅ Better logging and debugging support

### User Experience
- ✅ Bilingual interface (Chinese/English)
- ✅ Responsive design
- ✅ Improved navigation and user feedback
- ✅ Secure file upload with validation

---

## 📁 Project Structure

```
D2RItemDB/
├── app.py                 # Main Flask application
├── import_db.py          # Database initialization
├── ocr_utils.py          # OCR processing utilities
├── admin.py              # Admin interface
├── requirements.txt      # Python dependencies
├── .env.example          # Environment configuration template
├── .gitignore           # Git ignore rules
├── data/                # Game data files
├── templates/           # HTML templates
├── static/              # CSS, JS, images
└── images/              # Item images and assets
```

---

## 🔧 Configuration

### OCR Methods
- **EasyOCR**: Free, local OCR processing (default)
- **Gemini API**: Enhanced OCR with AI (requires API key)

### Database
- **SQLite**: Default lightweight database
- **PostgreSQL**: Production-ready (configurable)

### Security Settings
- **SECRET_KEY**: Flask session encryption key
- **SESSION_COOKIE_SECURE**: HTTPS-only cookies in production
- **Rate Limiting**: Configurable request limits

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [ZHIQUANLIU/D2R-Excel](https://github.com/ZHIQUANLIU/D2R-Excel) for comprehensive game data
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for OCR capabilities
- [Google Gemini API](https://ai.google.dev/) for enhanced AI processing

## 🎮 Usage Guide

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`
3. Check and configure OCR settings at `/settings` (optional, but recommended for automation).
4. Add your accounts and characters at `/accounts`.
5. Start tracking your valuable loot at `/my-items/add`!

---

## 📁 Project Structure

```text
D2RItemDB/
├── app.py              # Main Flask application & UI
├── ocr_utils.py        # OCR utilities
├── import_db.py        # Database initialization script
├── settings.json       # User settings configuration
├── d2r_items.db        # Primary SQLite database
├── static/uploads/     # Uploaded item images & screenshots
├── images/             # Documentation visuals & banners
└── data/               # Core game data files
```

## 🗄️ Database Schema

| Table Name | Description |
|---|---|
| `weapons` | Weapon items |
| `armor` | Armor items |
| `unique_items` | Unique (暗金) items |
| `set_items` | Set (套装) items |
| `misc` | Miscellaneous items |
| `gems` | Gems |
| `runes` | Runes |
| `accounts` | Battle.net accounts |
| `characters` | User Characters |
| `my_items` | User's tracked items |
| `item_images` | Uploaded item screenshots |

---

## 📜 License

This project is licensed under the **MIT License**.

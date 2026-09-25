<div align="center">

# ⚡ DX Task

**A high-performance, minimalist Telegram Task & Collection Manager engineered with Python and SQLite.**

[![Telegram Bot](https://img.shields.io/badge/Telegram-@DXtask__bot-24A1DE?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/DXtask_bot)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Library](https://img.shields.io/badge/pyTelegramBotAPI-4.x-green?style=for-the-badge)](https://github.com/eternnoir/pyTelegramBotAPI)
[![Database](https://img.shields.io/badge/Storage-SQLite3%20(WAL)-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Payments](https://img.shields.io/badge/Payments-Telegram%20Stars%20(XTR)-yellow?style=for-the-badge)](https://telegram.org/blog/telegram-stars)

<br/>

[**English**](README.md) • [**Русский**](README.ru.md)

</div>

---

## 🧭 Philosophy: The "Single Window" Interface

Most Telegram bots flood the chat with dozens of consecutive messages, creating cognitive clutter. 

**DX Task** operates on a **Single Window UI** paradigm:
* The bot dynamically mutates a single persistent interface message (`send_edit`) via Telegram's `edit_message_text`.
* Incoming user command messages and text inputs are deleted immediately upon processing (`delete_msg`).
* The result is a clean, app-like dashboard that behaves like a native desktop widget right inside Telegram.

---

## 🏛 Architecture

The project follows a strict **Three-Layer Decoupled Architecture**:

```
 ┌────────────────────────────────────────────────────────┐
 │                   INTERFACE LAYER                      │
 │                       bot.py                           │
 │  • Message Handlers & Routing  • Telegram Stars XTR    │
 │  • In-memory Flood Control     • Single-Window Control │
 └──────────────────────────┬─────────────────────────────┘
                            │ Calls UI / Business Logic
 ┌──────────────────────────▼─────────────────────────────┐
 │                     CORE LAYER                         │
 │                       core.py                          │
 │  • Input Sanitization          • Inline Markup Factory │
 │  • Tier Limit Validation       • View State Generators │
 └──────────────────────────┬─────────────────────────────┘
                            │ Read / Write Queries
 ┌──────────────────────────▼─────────────────────────────┐
 │                     DATA LAYER                         │
 │                       data.py                          │
 │  • Thread-safe Connection      • Automatic Schema Migrations│
 │  • Re-entrant Lock (@lock)     • WAL Mode SQLite Database  │
 └────────────────────────────────────────────────────────┘
```

### 1. Data Layer (`data.py`)
* **Thread Safety:** Implements a custom re-entrant lock decorator (`@connection_lock` using `threading.RLock`) ensuring atomic operations during concurrent requests.
* **Concurrency:** Runs SQLite in **WAL (Write-Ahead Logging)** mode for low-latency concurrent reads and writes.
* **Schema Evolution:** Automatic in-place column migrations (`prem_until`) for subscription expiry calculation.

### 2. Core Layer (`core.py`)
* **Logic Decoupling:** Completely detached from direct network/bot calls. Pure domain logic.
* **Security & Sanitization:** Custom entity parser (`check_str`) filtering dangerous HTML syntax `<>&` to prevent parsing breaks and injection into Telegram's HTML parse mode.
* **UI Factory:** Builds localized, state-aware inline keyboards for list switching, task completion, removal, and payment tiers.

### 3. Interface Layer (`bot.py`)
* **Flood Guard:** Thread-safe `TTLCache` rate limiter (1.0s TTL per user) preventing spam and callback abuse.
* **Native Payments:** Integrated with Telegram Stars (`currency="XTR"`), processing asynchronous invoice generation and `pre_checkout_query` validation.
* **Context Adaptation:** Automatically switches rendering mode between private chats (persistent menu keyboard + single-window edit) and group chats.

---

## 📁 Repository Structure

```text
├── config.example.py  # Configuration template with environment variables
├── bot.py             # Interface layer: handlers, dispatcher & Telegram Stars
├── core.py            # Business logic layer: tier limits, views & validation
├── data.py            # Data layer: SQLite manager, connection lock & migrations
├── requirements.txt   # Project dependencies and packages
├── README.md          # Project documentation in English
└── README.ru.md       # Project documentation in Russian
```

---

## ✨ Features

- **⚡ Zero-Friction Quick-Add:** Send plain text directly to the bot. It is instantly appended to the active collection without entering commands.
- **📂 Dynamic Collections:** Organize tasks into dedicated contexts (e.g., *Work, Inbox, Dev, Personal*).
- **🔄 Instant Switching:** Seamlessly switch active collections using inline callback triggers.
- **⭐️ Telegram Stars Monetization:** Built-in tiered Pro subscription engine (1 Month, 3 Months, Lifetime).
- **🛡 Anti-Flood Protection:** Thread-safe in-memory cache throttling rapid-fire user requests.
- **🛠 Admin Telemetry:** Integrated `/stats` command tracking registered users, active premium subscribers, and live database footprint.

---

## 📊 Plan Limits & Tiers

| Feature | Free Standard Core | DX Pro ⚡ |
| :--- | :---: | :---: |
| **Max Collections** | `3` | **`30`** |
| **Tasks per Collection** | `15` | **`30`** |
| **Max Title Length** | `30 chars` | `30 chars` |
| **Max Task Length** | `100 chars` | `100 chars` |
| **Pricing** | *Free* | `75 Stars` (1M) / `150 Stars` (3M) / `499 Stars` (Life) |

---

## ⌨️ Command Protocol

### Collections
* `/new` — Create a new collection (auto-sets as active)
* `/lists` — View all collections
* `/edit` — Open collection switcher UI
* `/rem` — Open collection deletion UI (with cascade task wipe)

### Tasks
* `/list` — Display tasks in current collection
* `/add` — Add a task manually (or just send text)
* `/done` — Toggle task completion status (`🔘` / `✅`)
* `/del` — Delete specific tasks from the list

### System & Interface
* `/on` — Restore the persistent main menu keyboard
* `/off` — Hide the reply keyboard
* `/fix` — Reset UI cache and re-anchor interface message
* `/donate` — Open the DX Pro upgrade menu
* `/help` — Display full command list

### Admin Controls
* `/stats` — View system monitor (Users, Premium, DB Size)
* `/get <user_id>` — Manually grant Lifetime DX Pro access

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
* Python 3.10+
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/dxtask.git
cd dxtask
```

### 3. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Credentials
Copy the example configuration file and fill in your details:
```bash
cp config.example.py config.py
```
Open `config.py` and provide your bot token and admin user ID:
```python
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789  # Your Telegram User ID (integer)
```

### 6. Run the Bot
```bash
python bot.py
```
*The database file `data.db` will be initialized automatically in WAL mode on the first launch.*

---

## 🗄 Database Schema

```sql
-- Users state & subscription tracking
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    active_list_id INTEGER,
    last_msg_id INTEGER,
    prem INTEGER DEFAULT 0,
    prem_until INTEGER DEFAULT 0
);

-- Collections
CREATE TABLE list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT
);

-- Tasks
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER,
    txt TEXT,
    done_val INTEGER DEFAULT 0
);
```

---

## 👨‍💻 Project Origin & Authorship

> *"I wrote every single line of this code manually."*

This is my first complete, production-grade software project. I chose to avoid pre-packaged templates and automatic code generators. 

Without a human mentor, I leveraged **Google AI Studio** strictly as an architectural sounding board and code-review consultant. The AI assisted in understanding advanced engineering concepts — such as Python decorators, database re-entrancy locks, WAL mode trade-offs, and state management — but every single module, database schema, algorithm, and debugging session was implemented and typed by hand.

This codebase marks my deliberate progression from writing one-off scripts to building reliable, layered, and maintainable software systems.

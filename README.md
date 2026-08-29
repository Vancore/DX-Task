# DX Task
A minimalist, high-performance Telegram Task Manager built with Python and SQLite.

**Try it live on Telegram:** [@DXtask_bot](https://t.me/DXtask_bot)

## Philosophy
Inspired by the "Single Window" UI concept, DX Task eliminates chat clutter. It seamlessly edits a single interface message instead of spamming the user with new ones. Everything in its place.

## Architecture
This system is built using a strict **Layered Architecture**:
* **Data Layer (`data.py`)**: A thread-safe SQLite wrapper using `threading.Lock()` to prevent database collisions under load.
* **Core Layer (`core.py`)**: The brain of the system. Handles business logic, limits (Free/Pro), and UI text generation.
* **Interface Layer (`bot.py`)**: The facade. Captures user inputs, handles callbacks, and safely manages the Telegram API.

## Features
* **Zero-Friction Input**: Type any text in the private chat, and it instantly becomes a task. No commands needed.
* **Pro Limits**: Free users get 3 collections / 15 tasks. Upgrading to DX Pro (via Telegram Stars) unlocks 30 collections / 30 tasks.
* **Deep Linking & Callbacks**: Fast navigation using inline callbacks and smart interface resets.

## Project Origin & Authorship
This is my first fully developed software project. 

**I wrote every single letter of this code manually.** I refused to use copy-paste solutions or auto-generators. Having no formal teacher, I used **Google AI Studio** strictly as an architectural consultant and mentor. The AI helped me understand complex engineering concepts (like decorators, database relations, and concurrency), but the implementation, debugging, and typing are 100% my own human effort. 

This repository reflects my transition from writing simple scripts to designing scalable software architecture.
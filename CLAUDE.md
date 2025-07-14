# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based web application for a wildlife camera trap identification game. Users view sequences of camera trap images and guess the wildlife species, earning points based on taxonomic accuracy.

## Core Architecture

- **Flask Application**: `app.py` - Main web server with session management
- **Database Models**: `models.py` - SQLite database operations for taxa, sequences, images, and high scores  
- **Game Logic**: `game_logic.py` - Scoring system, game sessions, and taxonomic matching
- **Data Processing**: `data_processor.py` - CSV to database conversion with memory optimization
- **Database Setup**: `db_setup.py` - Schema initialization

## Key Components

### Database Schema
- `taxa` - Unique taxonomic combinations with hierarchical taxonomy
- `sequences` - Groups of related camera trap images  
- `images` - Individual image metadata with cloud storage URLs
- `high_scores` - Game leaderboard

### Game Flow
1. Random taxa selection for game questions
2. Image sequence display with auto-play/manual navigation
3. Autocompletion-based guessing interface
4. Hierarchical scoring (species=10pts, genus=5pts, family=3pts, etc.)
5. High score tracking

### Scoring System
Located in `game_logic.py` - `SCORE_VALUES` dict maps taxonomic levels to point values. The `TAXONOMIC_HIERARCHY` list defines the specificity order.

## Common Development Commands

### Setup and Database
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database schema
python db_setup.py

# Process CSV data into database
python data_processor.py --csv-path /path/to/data.csv

# Verify database setup
python verify_setup.py
```

### Running the Application
```bash
# Development mode
python app.py

# Production mode with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Configuration
- Game parameters: `QUESTIONS_PER_GAME`, `SEQUENCES_PER_QUESTION` in `app.py`
- Scoring values: `SCORE_VALUES` in `game_logic.py`
- Database path: `DATABASE_PATH` in `models.py`
- Image cloud preference: `IMAGE_CLOUD_PREFERENCE` in `app.py`

## Development Notes

### Memory Optimization
The data processor uses a two-pass approach for large CSV files. Database connections use SQLite pragmas for performance optimization.

### Session Management
Game sessions are stored in-memory with cleanup logic to prevent memory leaks. Sessions use UUID generation.

### Error Handling
All major functions include try/catch blocks with fallback behaviors for robust operation.

### File Structure
```
templates/ - Jinja2 HTML templates
static/ - CSS and JavaScript assets
*.py - Python application modules
camera_trap_data.db - Generated SQLite database
```
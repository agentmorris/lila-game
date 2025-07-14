# Wildlife Camera Trap Game - Engineering Work Plan

## Project Overview
Build a web-based guessing game using wildlife camera trap images where users identify taxa from image sequences, with scoring based on taxonomic accuracy.

## Technology Stack
- **Backend**: Python Flask (simple, beginner-friendly)
- **Database**: SQLite (local, no additional costs)
- **Frontend**: HTML/CSS/JavaScript (vanilla, no frameworks)
- **Optional**: Gemini API for fun facts (environment variable: `GEMINI_API_KEY`)

## Database Schema

### 1. `taxa` table
```sql
CREATE TABLE taxa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kingdom TEXT,
    phylum TEXT,
    subphylum TEXT,
    superclass TEXT,
    class TEXT,
    subclass TEXT,
    infraclass TEXT,
    superorder TEXT,
    order_ TEXT,  -- 'order' is SQL keyword
    suborder TEXT,
    infraorder TEXT,
    superfamily TEXT,
    family TEXT,
    subfamily TEXT,
    tribe TEXT,
    genus TEXT,
    subgenus TEXT,
    species TEXT,
    subspecies TEXT,
    variety TEXT,
    common_name TEXT,
    most_specific_level TEXT,  -- e.g., 'species', 'genus', 'family'
    most_specific_name TEXT    -- the actual name at that level
);
```

### 2. `sequences` table
```sql
CREATE TABLE sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id TEXT UNIQUE,
    taxon_id INTEGER,
    location_id TEXT,
    datetime TEXT,
    FOREIGN KEY (taxon_id) REFERENCES taxa (id)
);
```

### 3. `images` table
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id TEXT UNIQUE,
    sequence_table_id INTEGER,
    frame_num INTEGER,
    url_gcp TEXT,
    url_aws TEXT,
    url_azure TEXT,
    FOREIGN KEY (sequence_table_id) REFERENCES sequences (id)
);
```

### 4. `high_scores` table
```sql
CREATE TABLE high_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT,
    score INTEGER,
    game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Processing Pipeline

### Phase 1: CSV Processing (`data_processor.py`)
1. **Load and filter CSV**: Remove rows where all taxonomy columns (kingdom through variety) are empty
2. **Create unique taxa**: 
   - For each unique combination of taxonomy columns, create one entry in `taxa` table
   - Determine `most_specific_level` by finding the deepest non-empty taxonomic level
   - Set `most_specific_name` to the value at that level
3. **Process sequences**:
   - Group images by `sequence_id` 
   - For sequences with multiple taxa (multiple rows with same sequence_id), create separate sequence entries for each taxon
4. **Populate images table**: Link each image to its corresponding sequence

### Phase 2: Database Setup (`db_setup.py`)
```python
# Create indexes for performance
CREATE INDEX idx_taxa_names ON taxa(most_specific_name, common_name);
CREATE INDEX idx_sequences_taxon ON sequences(taxon_id);
CREATE INDEX idx_images_sequence ON images(sequence_table_id);
```

## Application Structure

### Core Files:
- `app.py` - Main Flask application
- `models.py` - Database models and queries
- `game_logic.py` - Game mechanics and scoring
- `data_processor.py` - CSV to database conversion
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, images

### Flask Routes:

#### 1. `GET /` - Home page
- Game instructions
- Start new game button
- View high scores

#### 2. `POST /start_game` - Initialize new game
- Select M taxa randomly (default M=10)
- Initialize game session with score=0, current_question=0
- Return game session ID

#### 3. `GET /question/<session_id>/<question_num>` - Display question
- Select random taxon for current question
- Find N sequences (default N=4) containing that taxon
- Return all images from those sequences in order
- Include autoplay controls and manual navigation

#### 4. `GET /autocomplete?q=<query>` - Autocompletion endpoint
- Search both scientific names and common names
- Return matches with taxonomic level indication
- Format: `[{"name": "Felidae", "level": "Family", "taxon_id": 123}, ...]`

#### 5. `POST /submit_guess` - Process user guess
- Calculate score based on taxonomic accuracy
- Return correct answer, points earned, and fun fact (if Gemini API available)
- Update session score

#### 6. `GET /game_complete/<session_id>` - End game
- Show final score
- Check if score qualifies for high scores (top 10)
- If yes, prompt for name entry

#### 7. `POST /save_high_score` - Save high score
- Add to high_scores table
- Maintain only top 10 scores

## Scoring System

### Taxonomic Level Point Values:
```python
SCORE_VALUES = {
    'variety': 10,
    'subspecies': 10,
    'species': 10,
    'subgenus': 8,
    'genus': 5,
    'tribe': 4,
    'subfamily': 4,
    'family': 3,
    'superfamily': 2,
    'infraorder': 2,
    'suborder': 2,
    'order': 1,
    'superorder': 1,
    'infraclass': 1,
    'subclass': 1,
    'class': 1,
    'superclass': 1,
    'subphylum': 1,
    'phylum': 1,
    'kingdom': 1
}
```

### Scoring Logic:
1. Find the most specific taxonomic level for the correct answer
2. Find the taxonomic level of the user's guess
3. If guess matches at any level from the most specific up to kingdom, award points for the highest matching level
4. Handle common name matches by mapping to scientific names first

## Frontend Implementation

### Question Page (`templates/question.html`):
- Single image display area
- Auto-play toggle (default: on, ~1fps)
- Previous/Next buttons for manual control
- Progress indicator (e.g., "Image 5 of 23")
- Autocomplete input field for guessing
- Submit guess button
- Current score display

### JavaScript Requirements (`static/game.js`):
```javascript
// Image sequence management
- Auto-advance timer (1000ms intervals)
- Manual navigation controls
- Preload next images for smooth playback

// Autocomplete functionality
- Debounced search (300ms delay)
- Dropdown with taxonomic level indicators
- Keyboard navigation (arrow keys, enter)

// Game state management
- Track current image index
- Handle guess submission
- Display results modal
```

### CSS Styling (`static/style.css`):
- Responsive design for various screen sizes
- Clean, game-like interface
- Image display optimized for wildlife photos
- Clear typography for taxonomic names

## Deployment Steps

### 1. Environment Setup:
```bash
# Install dependencies
pip install flask sqlite3 pandas requests

# Optional: Set Gemini API key
export GEMINI_API_KEY="your-api-key-here"
```

### 2. Database Initialization:
```bash
python data_processor.py --csv-path /path/to/camera-trap-data.csv
```

### 3. Run Application:
```bash
python app.py
# Default: http://localhost:5000
```

### 4. Production Deployment:
```bash
# Install gunicorn for production serving
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Implementation Priority

### Phase 1 (Core Functionality):
1. Database schema and data processing
2. Basic Flask routes and templates
3. Simple image display and navigation
4. Basic autocomplete and scoring
5. Session management

### Phase 2 (Polish):
1. Improved UI/UX
2. Auto-play functionality
3. High score tracking
4. Error handling and validation

### Phase 3 (Stretch Goals):
1. Gemini API integration for fun facts
2. Performance optimizations
3. Additional game modes

## File Structure:
```
wildlife-game/
├── app.py
├── models.py
├── game_logic.py
├── data_processor.py
├── db_setup.py
├── requirements.txt
├── camera_trap_data.db  # Generated
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── question.html
│   ├── result.html
│   └── high_scores.html
└── static/
    ├── style.css
    ├── game.js
    └── images/
```

## Testing Strategy:
1. Test with small subset of CSV data first
2. Verify taxonomic scoring logic with known examples
3. Test autocomplete with various input patterns
4. Validate image sequence loading and display
5. Test high score functionality

This plan provides a complete roadmap for implementing the wildlife camera trap guessing game with all specified requirements and stretch goals.
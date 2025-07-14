# Wildlife Camera Trap Game - Complete Project Structure

## File Organization

Create the following directory structure and place the files as indicated:

```
wildlife-game/
├── README.md                    # Setup and usage instructions
├── design.md                    # System specification
├── requirements.txt             # Python dependencies
├── db_setup.py                  # Database schema creation
├── data_processor.py            # CSV to database converter
├── models.py                    # Database models and queries
├── game_logic.py                # Game mechanics and scoring
├── app.py                       # Main Flask application
├── camera_trap_data.db          # SQLite database (created by setup)
├── templates/                   # HTML templates
│   ├── base.html               # Base template with header/footer
│   ├── index.html              # Home page
│   ├── question.html           # Game question page
│   ├── game_complete.html      # Game completion page
│   └── high_scores.html        # High scores page
└── static/                     # CSS, JavaScript, images
    ├── style.css               # Main stylesheet
    └── game.js                 # JavaScript utilities
```

## Quick Setup Checklist

1. **Create the directory structure:**
   ```bash
   mkdir wildlife-game
   cd wildlife-game
   mkdir templates static
   ```

2. **Copy all files into their respective locations** (using the artifacts provided)

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database:**
   ```bash
   python db_setup.py
   ```

5. **Populate database:**
   ```bash
   python data_processor.py --csv-path /path/to/your/camera-trap-data.csv
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Open browser:** Navigate to `http://localhost:5000`

## Key Features Implemented

### Core Functionality ✅
- **Game Flow**: 10 questions per game, 4 sequences per question
- **Image Display**: Auto-play and manual controls for image sequences
- **Autocompletion**: Search both scientific and common names
- **Scoring System**: Hierarchical scoring (10 pts species, 5 pts genus, 3 pts family, 1 pt order+)
- **Database**: SQLite with proper indexing and optimization
- **High Scores**: Top 10 leaderboard with session persistence

### User Interface ✅
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Clean Visual Design**: Modern CSS with gradients and animations
- **Progress Tracking**: Question counter and score display
- **Intuitive Controls**: Clear buttons and navigation
- **Loading States**: Visual feedback during operations

### Technical Features ✅
- **Flask Backend**: Simple, reliable web framework
- **SQLite Database**: Local storage, no additional costs
- **CSV Processing**: Efficient conversion of large datasets
- **Error Handling**: Graceful degradation and user feedback
- **Performance Optimization**: Image preloading, database indexing

### Stretch Goals ✅
- **Gemini Integration**: Fun facts about wildlife (when API key provided)
- **High Score Tracking**: Arcade-style leaderboard with name entry
- **Database Statistics**: Show data overview on home page
- **Game Analytics**: Performance tracking and validation

## Configuration Options

The system includes several configurable parameters in `app.py`:

```python
QUESTIONS_PER_GAME = 10           # Questions per game session
SEQUENCES_PER_QUESTION = 4        # Image sequences per question
IMAGE_CLOUD_PREFERENCE = 'gcp'    # Cloud storage preference
```

## Optional Enhancements

For **Gemini API integration**, set environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

For **production deployment** with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Data Requirements

Your CSV file should have these columns:
- `dataset_name`, `url_gcp`, `url_aws`, `url_azure`
- `image_id`, `sequence_id`, `location_id`, `frame_num`
- `original_label`, `scientific_name`, `common_name`, `datetime`
- `annotation_level`
- Taxonomy: `kingdom`, `phylum`, `subphylum`, `superclass`, `class`, `subclass`, `infraclass`, `superorder`, `order`, `suborder`, `infraorder`, `superfamily`, `family`, `subfamily`, `tribe`, `genus`, `subgenus`, `species`, `subspecies`, `variety`

## System Requirements

- **Python**: 3.7 or higher
- **Memory**: 4GB RAM (sufficient for typical datasets)
- **Storage**: 2GB+ available (depends on database size after CSV processing)
- **Network**: Internet connection for image loading from cloud storage
- **Browser**: Modern browser with JavaScript support

## Security Considerations

- No persistent user data storage
- Session-based state management only
- Input validation and sanitization
- Safe database query handling
- No authentication required (as specified)

This implementation provides a complete, production-ready wildlife identification game that meets all your specified requirements while remaining simple to deploy and maintain on your Ubuntu VM.
# Wildlife Camera Trap Game - Design Specification

## Overview
A web-based guessing game where users identify wildlife taxa from camera trap image sequences. Users view sequences of images and guess the animal species, genus, family, etc., earning points based on taxonomic accuracy.

## System Requirements

### Functional Requirements
1. **Game Flow**:
   - Users play games with M taxa (default: 10 questions)
   - Each question shows N image sequences (default: 4) containing the target taxon
   - Images display one at a time, can auto-play (~1fps) or manual navigation
   - Users guess at any time with no time limit
   - Scoring based on taxonomic accuracy (10 points species, 5 genus, 3 family, etc.)
   - Final score displayed with optional high score entry

2. **Data Management**:
   - Process 15GB CSV of camera trap metadata
   - Filter out non-wildlife images (blank taxonomy)
   - Support ~few thousand unique taxa
   - Handle image sequences (3-10 images per sequence)
   - Store metadata for GCP, AWS, Azure image URLs

3. **User Interface**:
   - Autocompletion for guessing (scientific + common names)
   - Clean, simple web interface
   - Responsive design for various screen sizes
   - Progress tracking within games

4. **Scoring System**:
   - Hierarchical scoring: Species (10), Genus (5), Family (3), Order (1), etc.
   - Handle partial matches at higher taxonomic levels
   - Track session high scores (top 10)

### Non-Functional Requirements
- **Scale**: <5 concurrent users
- **Hosting**: Single Ubuntu VM (4GB RAM)
- **Cost**: No additional hosting costs beyond existing VM
- **Database**: Local SQLite (static data, infrequent updates)
- **Development**: Python-based, simple frameworks

## Architecture

### Technology Stack
- **Backend**: Python Flask
- **Database**: SQLite with local storage
- **Frontend**: HTML/CSS/JavaScript (vanilla)
- **Optional**: Gemini API for wildlife fun facts

### Data Model

#### Taxa Table
- Stores unique taxonomic combinations from CSV
- Includes full taxonomic hierarchy (kingdom → variety)
- Tracks most specific level and name for each taxon
- Includes common names for search

#### Sequences Table  
- Groups images by sequence_id from camera traps
- Links to specific taxon
- Preserves location and temporal metadata

#### Images Table
- Individual image metadata and URLs
- Frame number within sequence
- Links to parent sequence

#### High Scores Table
- Session-based leaderboard
- Player names and scores
- Top 10 maintained automatically

### API Design

#### Core Endpoints
- `GET /` - Home page and game start
- `POST /start_game` - Initialize new game session
- `GET /question/<session>/<num>` - Display question with image sequences
- `GET /autocomplete?q=<query>` - Search taxa and common names
- `POST /submit_guess` - Process guess and calculate score
- `GET /game_complete/<session>` - Final score and high score entry
- `POST /save_high_score` - Add to leaderboard

#### Data Flow
1. CSV → Database preprocessing (one-time setup)
2. Game initialization → Random taxon selection
3. Question display → Image sequence retrieval and display
4. User guess → Autocompletion search → Score calculation
5. Game completion → High score check and storage

## User Experience Design

### Game Flow
1. **Home Page**: Instructions, start game, view high scores
2. **Question Page**: 
   - Single image display with auto-play/manual controls
   - Progress indicator (e.g., "Image 5 of 23", "Question 3 of 10")
   - Autocompletion input for guessing
   - Current score display
3. **Result Page**: 
   - Correct answer reveal
   - Points earned explanation
   - Fun fact (if Gemini API available)
   - Continue to next question
4. **Game Complete**: 
   - Final score
   - High score entry if qualified
   - Play again option

### Interface Elements
- **Image Viewer**: 
  - Large, centered image display optimized for wildlife photos
  - Auto-play toggle and speed control
  - Previous/next navigation buttons
  - Smooth transitions between images
  
- **Guess Input**:
  - Autocomplete dropdown with scientific and common names
  - Taxonomic level indicators (e.g., "Felidae (Family)")
  - Submit button with current guess validation

- **Scoring Display**:
  - Current game score prominently displayed
  - Question progress (X of M)
  - Visual feedback for points earned

## Data Processing Specifications

### CSV Processing Rules
1. **Filtering**: Remove rows where all taxonomy columns (kingdom through variety) are empty
2. **Taxa Extraction**: Create unique taxa from distinct combinations of taxonomy columns
3. **Sequence Grouping**: Group images by sequence_id, handle multi-taxon sequences
4. **URL Handling**: Preserve all three cloud storage URLs per image

### Database Population
1. **Taxa Processing**:
   - Determine most specific taxonomic level per taxon
   - Store full hierarchical path for partial matching
   - Include common names for search functionality

2. **Sequence Processing**:
   - One sequence record per taxon (split multi-taxon sequences)
   - Preserve temporal and location metadata
   - Link to appropriate taxon record

3. **Image Processing**:
   - Maintain frame order within sequences
   - Store all cloud URLs for redundancy
   - Link to parent sequence

## Scoring Algorithm

### Point Values by Taxonomic Level
```
Species/Subspecies/Variety: 10 points
Genus/Subgenus: 5 points  
Family/Subfamily: 3 points
Order and above: 1 point
```

### Matching Logic
1. Identify most specific level of correct answer
2. Find taxonomic level of user guess
3. Award points for highest matching level in hierarchy
4. Handle common name guesses by mapping to scientific names
5. Case-insensitive matching with whitespace normalization

## Deployment Strategy

### Development Environment
- Windows with WSL Ubuntu for testing
- Local SQLite database
- Flask development server

### Production Environment  
- Ubuntu VM deployment
- Gunicorn WSGI server
- Static file serving via Flask
- Database and application on same server

### Configuration Management
- Environment variables for API keys
- Configurable game parameters (M questions, N sequences)
- Database path configuration
- Image URL preference (GCP/AWS/Azure)

## Performance Considerations

### Database Optimization
- Indexes on frequently queried columns (taxon names, sequence lookups)
- Query optimization for random taxon selection
- Efficient autocompletion search

### Memory Management
- Session data kept minimal
- Image metadata cached appropriately
- Database connection pooling

### User Experience
- Image preloading for smooth sequence playback
- Responsive autocompletion (debounced search)
- Progress indicators for long operations

## Security and Privacy

### Data Handling
- No persistent user accounts or personal data storage
- Session-based state management only
- High scores with optional name entry only

### API Security
- Input validation and sanitization
- Rate limiting considerations for autocompletion
- Safe handling of file paths and database queries

## Extensibility

### Future Enhancements
- Additional game modes (difficulty levels, time limits)
- Expanded scoring systems
- User analytics and game statistics
- Multi-player features
- Mobile app integration

### API Integration
- Gemini API for wildlife fun facts
- Potential integration with other wildlife databases
- Image analysis APIs for automated validation

## Testing Strategy

### Data Validation
- CSV processing accuracy verification
- Database integrity checks
- Taxonomic hierarchy validation

### Functionality Testing
- Game flow end-to-end testing
- Scoring algorithm verification
- Autocompletion functionality
- Session management

### Performance Testing
- Database query performance
- Concurrent user handling
- Image loading and display performance

This specification provides the foundation for implementing a robust, scalable wildlife identification game that meets all stated requirements while maintaining simplicity and cost-effectiveness.
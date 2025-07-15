#!/usr/bin/env python3
"""
Main Flask application for Wildlife Camera Trap Game.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import uuid
import os
from dotenv import load_dotenv
from models import Taxa, Sequences, Images, HighScores, GameData
from game_logic import GameSession, get_scoring_explanation

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random secret key for sessions

# Configure for Apache proxy deployment
APPLICATION_ROOT = os.getenv('APPLICATION_ROOT', '/')
if APPLICATION_ROOT != '/':
    app.config['APPLICATION_ROOT'] = APPLICATION_ROOT
    
# Debug: Print the configuration
print(f"DEBUG: APPLICATION_ROOT set to: {APPLICATION_ROOT}")
print(f"DEBUG: Flask config APPLICATION_ROOT: {app.config.get('APPLICATION_ROOT', 'Not set')}")

# Configuration (with environment variable support)
QUESTIONS_PER_GAME = int(os.getenv('QUESTIONS_PER_GAME', '10'))
SEQUENCES_PER_QUESTION = int(os.getenv('SEQUENCES_PER_QUESTION', '4'))
IMAGE_CLOUD_PREFERENCE = os.getenv('IMAGE_CLOUD_PREFERENCE', 'gcp')  # 'gcp', 'aws', or 'azure'
PORT = int(os.getenv('PORT', '5001'))

# In-memory storage for game sessions
game_sessions = {}

@app.route('/')
def index():
    """Home page."""
    
    # Get database stats for display (simplified for large databases)
    try:
        # Skip slow stats and validation queries for faster loading
        stats = {}
        ready_to_play = True  # Assume ready since database exists
        
        # Get high scores (should be fast)
        high_scores = HighScores.get_top_scores()
        
    except Exception as e:
        print(f"Error loading home page data: {e}")
        stats = {}
        ready_to_play = False
        high_scores = []
    
    return render_template('index.html', 
                         stats=stats, 
                         ready_to_play=ready_to_play,
                         high_scores=high_scores,
                         scoring_explanation=get_scoring_explanation())

@app.route('/start_game', methods=['POST'])
def start_game():
    """Initialize a new game."""
    
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Get random taxa for the game
        taxa = Taxa.get_random_taxa(QUESTIONS_PER_GAME)
        
        if not taxa:
            return jsonify({'error': 'No taxa available for game'}), 500
        
        # Create game session
        game_session = GameSession(session_id, taxa, QUESTIONS_PER_GAME)
        game_sessions[session_id] = game_session
        
        # Store session ID in Flask session
        session['game_session_id'] = session_id
        
        return jsonify({
            'session_id': session_id,
            'taxa_count': len(taxa),
            'questions_per_game': QUESTIONS_PER_GAME
        })
        
    except Exception as e:
        print(f"Error starting game: {e}")
        return jsonify({'error': 'Failed to start game'}), 500

@app.route('/question/<session_id>/<int:question_num>')
def question(session_id, question_num):
    """Display a question with image sequences."""
    
    # Get game session
    game_session = game_sessions.get(session_id)
    if not game_session:
        return redirect(url_for('index'))
    
    # Check if question number is valid
    if question_num != game_session.current_question + 1:
        return redirect(url_for('question', 
                              session_id=session_id, 
                              question_num=game_session.current_question + 1))
    
    # Get current taxon
    current_taxon = game_session.get_current_taxon()
    if not current_taxon:
        return redirect(url_for('game_complete', session_id=session_id))
    
    try:
        # Get sequences for this taxon
        sequences = Sequences.get_sequences_for_taxon(current_taxon['id'], SEQUENCES_PER_QUESTION)
        
        if not sequences:
            return jsonify({'error': 'No sequences found for this taxon'}), 500
        
        # Get all images for these sequences
        sequence_ids = [seq['id'] for seq in sequences]
        images = Images.get_images_for_sequences(sequence_ids, IMAGE_CLOUD_PREFERENCE)
        
        if not images:
            return jsonify({'error': 'No images found for sequences'}), 500
        
        # Prepare data for template
        question_data = {
            'session_id': session_id,
            'question_num': question_num,
            'total_questions': QUESTIONS_PER_GAME,
            'current_score': game_session.total_score,
            'images': images,
            'total_images': len(images),
            'sequences_count': len(sequences)
        }
        
        return render_template('question.html', **question_data)
        
    except Exception as e:
        print(f"Error loading question: {e}")
        return jsonify({'error': 'Failed to load question'}), 500

@app.route('/autocomplete')
def autocomplete():
    """Provide autocompletion for taxon guessing."""
    
    query = request.args.get('q', '').strip()
    print(f"DEBUG: autocomplete route called with query: '{query}'")
    
    if len(query) < 2:  # Require at least 2 characters
        print("DEBUG: autocomplete - query too short, returning empty list")
        return jsonify([])
    
    try:
        results = Taxa.search_taxa(query, limit=20)
        
        # Format for autocompletion UI
        suggestions = []
        for taxon in results:
            suggestion = {
                'id': taxon['id'],
                'name': taxon['most_specific_name'],
                'level': taxon['most_specific_level'].title() if taxon['most_specific_level'] else 'Unknown',
                'common_name': taxon['common_name'],
                'display_name': taxon['display_name'],
                'value': taxon['most_specific_name']  # What gets filled in the input
            }
            suggestions.append(suggestion)
        
        print(f"DEBUG: autocomplete - returning {len(suggestions)} suggestions")
        return jsonify(suggestions)
        
    except Exception as e:
        print(f"ERROR: autocomplete - Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    """Process a user's guess and return scoring result."""
    
    data = request.get_json()
    session_id = data.get('session_id')
    guess_taxon_id = data.get('taxon_id')  # From autocomplete selection
    guess_name = data.get('guess_name', '').strip()
    
    # Get game session
    game_session = game_sessions.get(session_id)
    if not game_session:
        return jsonify({'error': 'Invalid session'}), 400
    
    if not guess_name:
        return jsonify({'error': 'No guess provided'}), 400
    
    try:
        # Get guess taxon if ID provided
        guess_taxon = None
        if guess_taxon_id:
            guess_taxon = Taxa.get_taxon_by_id(guess_taxon_id)
        
        # Submit answer and get result
        result = game_session.submit_answer(guess_taxon, guess_name)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error processing guess: {e}")
        return jsonify({'error': 'Failed to process guess'}), 500

@app.route('/get_hint', methods=['POST'])
def get_hint():
    """Get a hint for the current question."""
    
    data = request.get_json()
    session_id = data.get('session_id')
    
    # Get game session
    game_session = game_sessions.get(session_id)
    if not game_session:
        return jsonify({'error': 'Invalid session'}), 400
    
    try:
        hint = game_session.get_hint()
        return jsonify({
            'hint': hint,
            'has_hint': hint is not None
        })
        
    except Exception as e:
        print(f"Error getting hint: {e}")
        return jsonify({'error': 'Failed to get hint'}), 500

@app.route('/result/<session_id>/<int:question_num>')
def result(session_id, question_num):
    """Display result for a specific question (if needed as separate page)."""
    
    # This route could be used if you want a separate result page
    # For now, results are handled via AJAX in the question page
    
    game_session = game_sessions.get(session_id)
    if not game_session:
        return redirect(url_for('index'))
    
    # Redirect to appropriate page based on game state
    if game_session.is_complete():
        return redirect(url_for('game_complete', session_id=session_id))
    else:
        next_question = game_session.current_question + 1
        return redirect(url_for('question', session_id=session_id, question_num=next_question))

@app.route('/game_complete/<session_id>')
def game_complete(session_id):
    """Display final game results and high score entry."""
    
    game_session = game_sessions.get(session_id)
    if not game_session:
        return redirect(url_for('index'))
    
    if not game_session.is_complete():
        # Game not finished, redirect to current question
        next_question = game_session.current_question + 1
        return redirect(url_for('question', session_id=session_id, question_num=next_question))
    
    try:
        # Get final results
        final_results = game_session.get_final_score()
        
        # Check if score qualifies for high score list
        is_high_score = HighScores.is_high_score(final_results['total_score'])
        
        # Get current high scores
        high_scores = HighScores.get_top_scores()
        
        return render_template('game_complete.html',
                             session_id=session_id,
                             results=final_results,
                             is_high_score=is_high_score,
                             high_scores=high_scores)
        
    except Exception as e:
        print(f"Error loading game complete page: {e}")
        return redirect(url_for('index'))

@app.route('/save_high_score', methods=['POST'])
def save_high_score():
    """Save a high score."""
    
    data = request.get_json()
    session_id = data.get('session_id')
    player_name = data.get('player_name', '').strip()
    
    if not player_name:
        return jsonify({'error': 'Player name required'}), 400
    
    # Get game session
    game_session = game_sessions.get(session_id)
    if not game_session or not game_session.is_complete():
        return jsonify({'error': 'Invalid session or game not complete'}), 400
    
    try:
        # Save high score
        success = HighScores.add_score(player_name, game_session.total_score)
        
        if success:
            # Clean up session
            del game_sessions[session_id]
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to save high score'}), 500
            
    except Exception as e:
        print(f"Error saving high score: {e}")
        return jsonify({'error': 'Failed to save high score'}), 500

@app.route('/high_scores')
def high_scores():
    """Display high scores page."""
    
    try:
        scores = HighScores.get_top_scores()
        return render_template('high_scores.html', high_scores=scores)
        
    except Exception as e:
        print(f"Error loading high scores: {e}")
        return render_template('high_scores.html', high_scores=[])

@app.route('/debug')
def debug():
    """Debug page showing database statistics."""
    
    if not app.debug:
        return "Debug mode not enabled", 403
    
    try:
        stats = GameData.get_taxon_statistics()
        validation = GameData.validate_database()
        
        return jsonify({
            'statistics': stats,
            'validation': validation,
            'active_sessions': len(game_sessions)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('index.html'), 500

# Clean up old sessions periodically (basic implementation)
@app.before_request
def cleanup_sessions():
    """Remove old game sessions to prevent memory leaks."""
    
    # Simple cleanup: remove sessions if we have too many
    if len(game_sessions) > 100:
        # Remove oldest sessions (this is basic - could be improved with timestamps)
        session_ids = list(game_sessions.keys())
        for session_id in session_ids[:50]:  # Remove oldest 50
            game_sessions.pop(session_id, None)

if __name__ == '__main__':
    # Import DATABASE_PATH from models to use consistent path logic
    from models import DATABASE_PATH
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database not found at: {DATABASE_PATH}")
        print("Please run:")
        print("1. python db_setup.py")
        print("2. python data_processor.py --csv-path /path/to/your/data.csv")
        print(f"Expected database location: {DATABASE_PATH}")
        exit(1)
    
    # Validate database (commented out for large databases - slow queries)
    # try:
    #     validation = GameData.validate_database()
    #     if not all(validation.values()):
    #         print("Warning: Database validation failed:")
    #         for check, passed in validation.items():
    #             if not passed:
    #                 print(f"  - {check}: FAILED")
    #         print("The game may not work properly.")
    # except Exception as e:
    #     print(f"Warning: Could not validate database: {e}")
    print("Skipping database validation for faster startup...")
    
    # Run the application
    print("Starting The LILA Game...")
    print(f"Open your browser to http://localhost:{PORT}")
    
    # Use environment-based debug mode
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=PORT)
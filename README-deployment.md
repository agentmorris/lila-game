# The LILA Game - Deployment Guide

A web-based wildlife camera trap identification game using real camera trap images from conservation research projects.

## Project Overview

This app provides an educational wildlife identification game where players view sequences of camera trap images and identify animals at various taxonomic levels. Players earn points based on the accuracy of their identification, from species (10 points) to family (3 points) to order (1 point).

**Tech Stack:**
- Backend: Flask with SQLite database
- Frontend: HTML/CSS/JavaScript (vanilla, no frameworks)
- LLM: Google Gemini API for hints and fun facts
- Deployment: Docker container with volume persistence
- Database: SQLite with camera trap image metadata

## Features

- **Real camera trap sequences** from wildlife research projects
- **Hierarchical scoring system** rewarding taxonomic accuracy
- **AI-powered hints** using Gemini API (without revealing answers)
- **Fun facts** about correctly identified animals
- **Autocomplete search** supporting scientific and common names
- **High score leaderboard** with persistent storage
- **Responsive interface** optimized for wildlife learning

## Project Structure

```
lila-game/
├── app.py                    # Main Flask application
├── models.py                 # Database models and queries
├── game_logic.py             # Game mechanics, scoring, and AI features
├── db_setup.py               # Database schema creation
├── data_processor.py         # CSV to database import tool
├── templates/                # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── question.html
│   └── high_scores.html
├── static/                   # CSS and JavaScript
│   └── style.css
├── data/                     # Docker volume mount point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── .env.example            # Environment variables template
└── README.md               # Main documentation
```

## Setup Instructions

### Local Development (Recommended for Testing)

1. **Clone/Setup the project directory:**
   ```bash
   cd lila-game
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Linux/WSL:
   source venv/bin/activate
   # On Windows Command Prompt:
   # venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database:**
   ```bash
   # Initialize database schema
   python db_setup.py
   
   # Import your camera trap CSV data
   python data_processor.py --csv-path /path/to/your/camera-trap-data.csv
   ```

5. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key for AI features
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Access the app:**
   Open your browser to `http://localhost:5001`

### Docker Deployment

1. **Prepare data directory:**
   ```bash
   mkdir -p data
   # Copy your existing database file to data directory
   cp camera_trap_data.db data/
   ```

2. **Set up configuration:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   
   # Optional: Configure Gemini model
   echo "gemini-1.5-flash" > .gemini-config
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the app:**
   Open your browser to `http://your-hostname:5001` or `http://your-ip:5001`

### Production Deployment

For production deployment on your Ubuntu VM:

1. **Copy files to your server**
2. **Set up environment and database**
3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

The app will be available at `your-hostname.com:5001` alongside your existing Apache setup.

## Environment Variables

Create a `.env` file in the root directory:

```env
# Gemini API Configuration (optional, for AI features)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash

# Flask Configuration
PORT=5001
FLASK_ENV=production

# Game Configuration (optional)
QUESTIONS_PER_GAME=10
SEQUENCES_PER_QUESTION=4
IMAGE_CLOUD_PREFERENCE=gcp

# Proxy Configuration (for Apache reverse proxy deployment)
APPLICATION_ROOT=/

# Debugging Configuration (for development)
DISABLE_AI=false

# Database Configuration (optional)
DATABASE_PATH=/app/data/camera_trap_data.db
```

## AI Features Setup (Optional)

For hints and fun facts features:

1. **Get Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **Provide the API key** using one of these methods (in order of priority):

   **Option A: Environment Variable**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

   **Option B: .env File**
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

   **Option C: .gemini-key File**
   Create a `.gemini-key` file in the project root:
   ```
   your-api-key-here
   ```

3. **Configure model (optional):**
   Create a `.gemini-config` file:
   ```
   gemini-1.5-flash
   ```
   
   Available models: `gemini-1.5-flash` (fast), `gemini-1.5-pro` (balanced), `gemini-2.5-pro` (advanced)

4. **Restart the application** - AI features will now be available

## Deployment

### Ubuntu Linux Server Deployment

#### Prerequisites

1. **Install Docker and Docker Compose on Ubuntu:**
   ```bash
   # Update package index
   sudo apt update
   
   # Install Docker
   sudo apt install -y docker.io docker-compose
   
   # Start and enable Docker
   sudo systemctl start docker
   sudo systemctl enable docker
   
   # Add your user to docker group (logout/login required)
   sudo usermod -aG docker $USER
   ```

2. **Open required ports:**
   ```bash
   # Open port 5001 (or your chosen port) in UFW firewall
   sudo ufw allow 5001
   
   # If using iptables instead:
   sudo iptables -A INPUT -p tcp --dport 5001 -j ACCEPT
   ```

#### Deployment Steps

1. **Copy project files to your server:**
   ```bash
   # Using scp from your local machine:
   scp -r lila-game/ user@your-server-ip:/home/user/
   
   # Or clone if using git:
   git clone your-repo-url lila-game
   cd lila-game
   ```

2. **Set up database and configuration:**
   ```bash
   # Ensure data directory exists
   mkdir -p data
   
   # Copy your populated database if you have one
   cp camera_trap_data.db data/
   
   # Set up environment variables
   cp .env.example .env
   nano .env  # Add your Gemini API key
   
   # Optional: Set up Gemini model preference
   echo "gemini-1.5-flash" > .gemini-config
   ```

3. **Deploy with Docker:**
   ```bash
   # Build and start the application
   docker-compose up -d --build
   
   # View logs to ensure it's running
   docker-compose logs -f
   ```

4. **Verify deployment:**
   ```bash
   # Check if the container is running
   docker-compose ps
   
   # Test the application
   curl http://localhost:5001/
   
   # Or test from another machine
   curl http://your-server-ip:5001/
   ```

5. **Access your application:**
   - Local: `http://your-server-ip:5001`
   - Domain: `http://yourdomain.com:5001`

#### Managing the Deployment

**Stop the application:**
```bash
docker-compose down
```

**Update and restart:**
```bash
# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

**View logs:**
```bash
# View current logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f
```

**Change the port:**
Edit `docker-compose.yml` and change the port mapping:
```yaml
ports:
  - "5002:5001"  # This would make it accessible on port 5002
```

**Database management:**
```bash
# Access the database directly
docker-compose exec lila-game sqlite3 /app/data/camera_trap_data.db

# Backup the database
docker-compose exec lila-game cp /app/data/camera_trap_data.db /app/data/backup-$(date +%Y%m%d).db

# Clear high scores (for testing/reset)
sqlite3 data/camera_trap_data.db "DELETE FROM high_scores;"

# View current high scores
sqlite3 data/camera_trap_data.db "SELECT player_name, score, game_date FROM high_scores ORDER BY score DESC;"

# Check database stats
sqlite3 data/camera_trap_data.db "SELECT COUNT(*) as taxa_count FROM taxa; SELECT COUNT(*) as scores_count FROM high_scores;"
```

#### Running alongside Apache

Since you mentioned Apache is already running on your server:

1. **The app runs on port 5001 by default** (separate from Apache's 80/443)
2. **Users access it directly**: `yourdomain.com:5001`
3. **Set up Apache reverse proxy** to serve it on a subdirectory path:

   **Option A: Subdirectory Path (Recommended)**
   ```apache
   # In your existing Apache virtual host config
   <VirtualHost *:80>
       ServerName yourdomain.com
       
       # Your existing configuration...
       
       # LILA Game proxy
       ProxyPass /lila-game http://localhost:5001/
       ProxyPassReverse /lila-game http://localhost:5001/
       ProxyPreserveHost On
   </VirtualHost>
   ```
   
   **Configure APPLICATION_ROOT for subdirectory deployment:**
   ```bash
   # In your .env file:
   APPLICATION_ROOT=/lila-game
   ```
   
   **Access:** `yourdomain.com/lila-game`

   **Option B: Subdomain**
   ```apache
   # Separate virtual host for subdomain
   <VirtualHost *:80>
       ServerName lila-game.yourdomain.com
       ProxyPass / http://localhost:5001/
       ProxyPassReverse / http://localhost:5001/
       ProxyPreserveHost On
   </VirtualHost>
   ```
   
   **Configure APPLICATION_ROOT for subdomain deployment:**
   ```bash
   # In your .env file:
   APPLICATION_ROOT=/
   ```
   
   **Access:** `lila-game.yourdomain.com`

#### APPLICATION_ROOT Configuration

The `APPLICATION_ROOT` setting is crucial for proper asset loading when using Apache reverse proxy:

**For direct access (yourdomain.com:5001):**
```env
APPLICATION_ROOT=/
```

**For subdirectory proxy (yourdomain.com/lila-game):**
```env
APPLICATION_ROOT=/lila-game
```

**For subdomain proxy (lila-game.yourdomain.com):**
```env
APPLICATION_ROOT=/
```

This setting ensures that CSS files, JavaScript files, and AJAX requests use the correct paths when accessed through the Apache proxy.

#### Troubleshooting

**Port already in use:**
```bash
# Check what's using port 5001
sudo netstat -tlnp | grep :5001

# Change port in docker-compose.yml if needed
```

**Database issues:**
```bash
# Check if database file exists and is readable
docker-compose exec lila-game ls -la /app/data/

# Check database contents
docker-compose exec lila-game sqlite3 /app/data/camera_trap_data.db "SELECT COUNT(*) FROM taxa;"
```

**AI features not working:**
```bash
# Check API key configuration
docker-compose exec lila-game cat /app/.gemini-key

# Check logs for API errors
docker-compose logs | grep -i gemini
```

**Container won't start:**
```bash
# Check detailed logs
docker-compose logs lila-game

# Check container status
docker-compose ps
```

## Data Management

### Importing New Camera Trap Data

1. **Prepare your CSV file** with camera trap data
2. **Copy to container:**
   ```bash
   # Copy CSV to data directory
   cp your-new-data.csv data/
   
   # Process the data
   docker-compose exec lila-game python data_processor.py --csv-path /app/data/your-new-data.csv
   ```

### Database Maintenance

```bash
# Check database size
docker-compose exec lila-game ls -lh /app/data/camera_trap_data.db

# Vacuum database (reclaim space)
docker-compose exec lila-game sqlite3 /app/data/camera_trap_data.db "VACUUM;"

# Check database integrity
docker-compose exec lila-game sqlite3 /app/data/camera_trap_data.db "PRAGMA integrity_check;"
```

## Customization

### Changing Game Configuration

Edit `.env` file:
```env
QUESTIONS_PER_GAME=15          # More questions per game
SEQUENCES_PER_QUESTION=6       # More image sequences per question
IMAGE_CLOUD_PREFERENCE=aws     # Prefer AWS images over GCP
```

### Modifying AI Behavior

1. **Switch to faster model**: Edit `.gemini-config` to use `gemini-1.5-flash`
2. **Adjust prompts**: Edit `game_logic.py` functions `get_hint()` and `get_fun_fact()`
3. **Change timeout**: Modify timeout values in API calls (currently 20 seconds)

### Styling Changes

Modify `static/style.css` to change the appearance of the game interface.

## Monitoring

### Application Health

```bash
# Check if application is responding
curl http://localhost:5001/

# Monitor resource usage
docker-compose exec lila-game top

# Check disk usage
docker-compose exec lila-game df -h
```

### Log Analysis

```bash
# Search for errors
docker-compose logs | grep -i error

# Monitor AI API calls
docker-compose logs | grep -i "DEBUG.*gemini"

# Check game activity
docker-compose logs | grep -i "new game\|submit_answer"
```

## Performance Optimization

### Database Performance

For large databases (>1GB):
```bash
# Increase SQLite cache size (edit models.py)
# Add indexes for slow queries
# Consider splitting very large datasets
```

### AI API Performance

```bash
# Use faster model for better response times
echo "gemini-1.5-flash" > .gemini-config

# Monitor API response times in logs
docker-compose logs | grep "API response status"
```

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# Daily backup script
DATE=$(date +%Y%m%d)
docker-compose exec lila-game cp /app/data/camera_trap_data.db /app/data/backup-$DATE.db
```

### Recovery

```bash
# Restore from backup
cp data/backup-YYYYMMDD.db data/camera_trap_data.db
docker-compose restart
```

## Future Enhancements

Potential features to add:
- **User accounts** with personal statistics
- **Multiple difficulty levels** (species-only vs all levels)
- **Geographic filtering** by region/continent
- **Seasonal challenges** with themed content
- **Educational mode** with immediate answer reveals
- **Mobile app** version with offline capability

## Support

This deployment follows the same pattern as your successful NFL chatbot deployment. The codebase is designed to be simple and maintainable while providing robust wildlife education features.

For issues specific to camera trap data or large databases, most problems relate to CSV format compatibility or database size management during import.
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json
import pandas as pd
import subprocess
import threading
import sys

app = Flask(__name__)

# Paths
DATA_DIR = Path('data')
OUTPUT_DIR = DATA_DIR / 'output'
INPUT_DIR = DATA_DIR / 'input'
HIGH_RATED_FILE = OUTPUT_DIR / 'enriched_netflix_complete.json'
ENRICHED_FILE = OUTPUT_DIR / 'enriched_netflix_complete.json'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
INPUT_DIR.mkdir(exist_ok=True)

# Load data on startup
def load_data():
    """Load recommendations data"""
    try:
        with open(HIGH_RATED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []

# Global data storage
movies_data = load_data()

def reload_data():
    """Reload data from file"""
    global movies_data
    movies_data = load_data()

def run_python_script(script_name):
    """Run a Python script and return output"""
    try:
        # Get the Python executable from the virtual environment
        if sys.platform == 'win32':
            python_path = Path('venv/Scripts/python.exe')
        else:
            python_path = Path('venv/bin/python3')
        
        if not python_path.exists():
            python_path = Path(sys.executable)
        
        script_path = Path('scripts') / script_name
        
        result = subprocess.run(
            [str(python_path), str(script_path)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Script timed out (exceeded 10 minutes)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def run_enrichment_script():
    """Run enrichment script (in project root)"""
    try:
        if sys.platform == 'win32':
            python_path = Path('venv/Scripts/python.exe')
        else:
            python_path = Path('venv/bin/python3')
        
        if not python_path.exists():
            python_path = Path(sys.executable)
        
        script_path = Path('scripts/enrich_with_imdb.py')
        
        result = subprocess.run(
            [str(python_path), str(script_path)],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout for enrichment
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Enrichment timed out (exceeded 30 minutes)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ============= Movie Routes =============

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/movies')
def get_movies():
    """Get all movies with optional filters"""
    
    # Get filter parameters
    category = request.args.get('category', None)
    min_rating = float(request.args.get('min_rating', 0))
    max_rating = float(request.args.get('max_rating', 10))
    search = request.args.get('search', '').lower()
    genre = request.args.get('genre', None)
    watched_filter = request.args.get('watched', 'all')  # all, watched, unwatched
    
    # Filter data
    filtered = movies_data.copy()
    
    # Filter by category
    if category and category != 'all':
        filtered = [m for m in filtered if category in m.get('categories', [])]
    
    # Filter by rating - handle N/A and None
    def get_rating_value(movie):
        rating = movie.get('imdb_rating')
        if rating and rating != 'N/A':
            try:
                return float(rating)
            except (ValueError, TypeError):
                return 0
        return 0
    
    filtered = [m for m in filtered if min_rating <= get_rating_value(m) <= max_rating]
    
    # Filter by search
    if search:
        filtered = [m for m in filtered if search in m.get('title', '').lower()]
    
    # Filter by genre
    if genre and genre != 'all':
        filtered = [m for m in filtered if genre.lower() in str(m.get('genres', '')).lower()]
    
    # Filter by watched status
    if watched_filter == 'watched':
        filtered = [m for m in filtered if m.get('watched', False)]
    elif watched_filter == 'unwatched':
        filtered = [m for m in filtered if not m.get('watched', False)]
    
    return jsonify({
        'movies': filtered,
        'total': len(filtered)
    })

@app.route('/api/categories')
def get_categories():
    """Get all unique categories"""
    categories = set()
    for movie in movies_data:
        for cat in movie.get('categories', []):
            categories.add(cat)
    
    return jsonify(sorted(list(categories)))

@app.route('/api/genres')
def get_genres():
    """Get all unique genres"""
    genres = set()
    for movie in movies_data:
        genre_str = movie.get('genres', '')
        if genre_str and genre_str != 'N/A':
            for genre in genre_str.split(','):
                genre = genre.strip()
                if genre:
                    genres.add(genre)
    
    return jsonify(sorted(list(genres)))

@app.route('/api/movie/<netflix_id>/watched', methods=['POST'])
def mark_watched(netflix_id):
    """Mark a movie as watched/unwatched"""
    data = request.json
    watched = data.get('watched', False)
    
    # Find and update movie
    for movie in movies_data:
        if movie.get('netflixId') == netflix_id:
            movie['watched'] = watched
            
            # Save back to file
            with open(HIGH_RATED_FILE, 'w', encoding='utf-8') as f:
                json.dump(movies_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'watched': watched})
    
    return jsonify({'success': False, 'error': 'Movie not found'}), 404

@app.route('/api/stats')
def get_stats():
    """Get statistics about the data"""
    total = len(movies_data)
    watched = sum(1 for m in movies_data if m.get('watched', False))
    unwatched = total - watched
    
    # Average rating - handle N/A, None, and valid ratings
    ratings = []
    for m in movies_data:
        rating = m.get('imdb_rating')
        # Skip if None, "N/A", or empty
        if rating and rating != 'N/A':
            try:
                ratings.append(float(rating))
            except (ValueError, TypeError):
                continue
    
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Genre distribution
    genre_count = {}
    for movie in movies_data:
        genres = movie.get('genres', '')
        if genres and genres != 'N/A':
            for genre in genres.split(','):
                genre = genre.strip()
                if genre:
                    genre_count[genre] = genre_count.get(genre, 0) + 1
    
    # Top genres
    top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'total': total,
        'watched': watched,
        'unwatched': unwatched,
        'avg_rating': round(avg_rating, 1),
        'top_genres': dict(top_genres)
    })

# ============= Scraper Routes =============

@app.route('/api/scraper/login', methods=['POST'])
def scraper_login():
    """Run Netflix login script"""
    try:
        print('[Scraper] Starting Netflix login...')
        result = run_python_script('scripts/login.py')
        
        return jsonify({
            'success': result['success'],
            'message': 'Login completed' if result['success'] else 'Login failed',
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '') or result.get('error', '')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraper/viewing-activity', methods=['POST'])
def scraper_viewing_activity():
    """Run viewing activity scraper"""
    try:
        print('[Scraper] Starting viewing activity scrape...')
        result = run_python_script('scrape_viewing_activity.py')
        
        return jsonify({
            'success': result['success'],
            'message': 'Viewing activity scraped' if result['success'] else 'Scrape failed',
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '') or result.get('error', '')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraper/browse', methods=['POST'])
def scraper_browse():
    """Run browse page scraper"""
    try:
        print('[Scraper] Starting browse page scrape...')
        result = run_python_script('scripts/scrape_browse_complete.py')
        
        return jsonify({
            'success': result['success'],
            'message': 'Browse page scraped' if result['success'] else 'Scrape failed',
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '') or result.get('error', '')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraper/enrich', methods=['POST'])
def scraper_enrich():
    """Run IMDb enrichment script"""
    try:
        print('[Enrichment] Starting IMDb enrichment...')
        result = run_enrichment_script()
        
        # Reload data after enrichment
        if result['success']:
            reload_data()
        
        return jsonify({
            'success': result['success'],
            'message': 'Enrichment completed' if result['success'] else 'Enrichment failed',
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '') or result.get('error', '')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraper/full-pipeline', methods=['POST'])
def scraper_full_pipeline():
    """Run the complete scraping and enrichment pipeline"""
    try:
        print('[Pipeline] Starting full pipeline...')
        
        results = {
            'viewing_activity': None,
            'browse': None,
            'enrichment': None
        }
        
        # Step 1: Scrape viewing activity
        print('[Pipeline] Step 1/3: Scraping viewing activity...')
        results['viewing_activity'] = run_python_script('scripts/scrape_viewing_activity.py')
        if not results['viewing_activity']['success']:
            return jsonify({
                'success': False,
                'message': 'Pipeline failed at viewing activity step',
                'results': results
            }), 500
        
        # Step 2: Scrape browse page
        print('[Pipeline] Step 2/3: Scraping browse page...')
        results['browse'] = run_python_script('scrape_browse_complete.py')
        if not results['browse']['success']:
            return jsonify({
                'success': False,
                'message': 'Pipeline failed at browse scrape step',
                'results': results
            }), 500
        
        # Step 3: Enrich with IMDb
        print('[Pipeline] Step 3/3: Enriching with IMDb data...')
        results['enrichment'] = run_enrichment_script()
        if not results['enrichment']['success']:
            return jsonify({
                'success': False,
                'message': 'Pipeline failed at enrichment step',
                'results': results
            }), 500
        
        # Reload data after successful pipeline
        reload_data()
        
        return jsonify({
            'success': True,
            'message': 'Full pipeline completed successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraper/status', methods=['GET'])
def scraper_status():
    """Check if data files exist"""
    return jsonify({
        'session_exists': Path('netflix-session.json').exists(),
        'cookies_exist': Path('netflix-cookies.json').exists(),
        'browse_data_exists': (INPUT_DIR / 'netflix-browse-complete.json').exists(),
        'viewing_activity_exists': (INPUT_DIR / 'netflix-viewing-activity.json').exists(),
        'enriched_data_exists': HIGH_RATED_FILE.exists()
    })

@app.route('/api/data/reload', methods=['POST'])
def reload_data_endpoint():
    """Reload data from files"""
    try:
        reload_data()
        return jsonify({
            'success': True,
            'message': f'Reloaded {len(movies_data)} movies'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============= Health Check =============

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'movies_loaded': len(movies_data),
        'data_dir_exists': DATA_DIR.exists(),
        'output_dir_exists': OUTPUT_DIR.exists()
    })

if __name__ == '__main__':
    print('🚀 Netflix Recommender Flask Server')
    print('='*50)
    print(f'📊 Loaded {len(movies_data)} movies')
    print(f'📁 Data directory: {DATA_DIR.absolute()}')
    print(f'🌐 Server starting on http://localhost:5000')
    print('='*50)
    app.run(debug=True, port=5000)
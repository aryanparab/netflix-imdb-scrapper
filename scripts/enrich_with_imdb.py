import asyncio
import json
import pandas as pd
import requests
from datetime import datetime
import time
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv()
OMDB_API_KEY = os.getenv('OMDB_API_KEY')

if not OMDB_API_KEY:
    raise Exception("Please set OMDB_API_KEY in .env file")

# Create data directory structure
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

INPUT_DIR = DATA_DIR / 'input'
OUTPUT_DIR = DATA_DIR / 'output'
CHECKPOINT_DIR = DATA_DIR / 'checkpoints'

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)

# File paths
NETFLIX_BROWSE_FILE = INPUT_DIR / 'netflix-browse-complete.json'
VIEWING_ACTIVITY_FILE = INPUT_DIR / 'netflix-viewing-activity.json'
CHECKPOINT_FILE = CHECKPOINT_DIR / 'enrichment_checkpoint.json'
ENRICHED_COMPLETE_FILE = OUTPUT_DIR / 'enriched_netflix_complete.json'
HIGH_RATED_FILE = OUTPUT_DIR / 'high_rated_recommendations.json'
RECOMMENDATIONS_CSV = OUTPUT_DIR / 'recommendations.csv'
SIMPLE_RECS_FILE = OUTPUT_DIR / 'simple_recommendations.json'

print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔑 API Key loaded')
print(f'[{datetime.now().strftime("%H:%M:%S")}] 📁 Data directories created')


def load_netflix_data():
    """Load Netflix scraped data"""
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 📂 Loading Netflix data...')
    
    with open(NETFLIX_BROWSE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Loaded {len(df)} titles')
    
    return df


def load_viewing_activity():
    """Load viewing activity to mark watched items"""
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📺 Loading viewing activity...')
    
    try:
        with open(VIEWING_ACTIVITY_FILE, 'r', encoding='utf-8') as f:
            viewing_data = json.load(f)
        
        # Extract just the titles
        watched_titles = set()
        for item in viewing_data:
            title = item.get('title', '')
            # Clean up episode info (e.g., "Show Name: Season 1: Episode 1" -> "Show Name")
            clean_title = title.split(':')[0].strip()
            watched_titles.add(clean_title.lower())
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Found {len(watched_titles)} watched titles')
        return watched_titles
        
    except FileNotFoundError:
        print(f'[{datetime.now().strftime("%H:%M:%S")}] ⚠️ Viewing activity file not found, skipping...')
        return set()


def mark_watched_items(df, watched_titles):
    """Add 'watched' column based on viewing activity"""
    if not watched_titles:
        df['watched'] = False
        return df
    
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 🏷️ Marking watched items...')
    
    def is_watched(title):
        clean_title = title.lower().strip()
        return clean_title in watched_titles
    
    df['watched'] = df['title'].apply(is_watched)
    
    watched_count = df['watched'].sum()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Marked {watched_count} items as watched')
    
    return df


def merge_existing_with_new(existing_df, new_df):
    """
    Merge existing enriched data with new browse data
    - Preserves IMDb data and watched status from existing
    - Merges categories from both
    - Adds completely new titles
    """
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 🔄 Merging datasets...')
    print(f'  Existing: {len(existing_df)} titles')
    print(f'  New: {len(new_df)} titles')
    
    # Create lookup maps by netflixId AND title (for items without ID)
    existing_by_id = {}
    existing_by_title = {}
    
    for idx, row in existing_df.iterrows():
        netflix_id = row.get('netflixId')
        title = row.get('title', '').lower().strip()
        
        if pd.notna(netflix_id):
            existing_by_id[netflix_id] = idx
        if title:
            existing_by_title[title] = idx
    
    # Track what we're doing
    updated_count = 0
    new_count = 0
    titles_to_enrich = []
    
    # Process each new title
    for _, new_row in new_df.iterrows():
        netflix_id = new_row.get('netflixId')
        title = new_row.get('title', '').lower().strip()
        
        existing_idx = None
        
        # Try to find existing by Netflix ID first (most reliable)
        if pd.notna(netflix_id) and netflix_id in existing_by_id:
            existing_idx = existing_by_id[netflix_id]
        # Fall back to title matching if no ID match
        elif title and title in existing_by_title:
            existing_idx = existing_by_title[title]
        
        if existing_idx is not None:
            # Movie exists - merge categories and update metadata
            existing_row = existing_df.loc[existing_idx]
            
            # Merge categories (unique)
            existing_cats = existing_row.get('categories', [])
            new_cats = new_row.get('categories', [])
            
            if not isinstance(existing_cats, list):
                existing_cats = [existing_cats] if existing_cats else []
            if not isinstance(new_cats, list):
                new_cats = [new_cats] if new_cats else []
            
            merged_cats = list(set(existing_cats + new_cats))
            
            # Update the existing row
            existing_df.at[existing_idx, 'categories'] = merged_cats
            
            # Update image and link if they exist in new data
            if pd.notna(new_row.get('image')):
                existing_df.at[existing_idx, 'image'] = new_row['image']
            if pd.notna(new_row.get('link')):
                existing_df.at[existing_idx, 'link'] = new_row['link']
            
            updated_count += 1
        else:
            # New movie - add it to list for enrichment
            new_count += 1
            titles_to_enrich.append(new_row.to_dict())
    
    print(f'  🔄 Updated: {updated_count} existing titles')
    print(f'  ➕ Found: {new_count} new titles')
    
    # Convert new titles to DataFrame
    if titles_to_enrich:
        new_titles_df = pd.DataFrame(titles_to_enrich)
        return existing_df, new_titles_df, new_count
    else:
        return existing_df, pd.DataFrame(), 0


def search_omdb(title, year=None):
    """
    Search OMDb API for a title
    Returns movie/show data or None if not found
    """
    url = "http://www.omdbapi.com/"
    
    params = {
        'apikey': OMDB_API_KEY,
        't': title,
    }
    
    if year:
        params['y'] = year
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('Response') == 'True':
            return {
                'imdb_id': data.get('imdbID'),
                'imdb_rating': data.get('imdbRating'),
                'imdb_votes': data.get('imdbVotes'),
                'year': data.get('Year'),
                'rated': data.get('Rated'),
                'runtime': data.get('Runtime'),
                'genres': data.get('Genre'),
                'director': data.get('Director'),
                'actors': data.get('Actors'),
                'plot': data.get('Plot'),
                'awards': data.get('Awards'),
                'poster': data.get('Poster'),
                'type': data.get('Type'),
                'total_seasons': data.get('totalSeasons')
            }
        else:
            return None
            
    except Exception as e:
        print(f'  ⚠️ Error searching for "{title}": {str(e)[:50]}')
        return None


def load_checkpoint():
    """Load checkpoint if it exists"""
    if CHECKPOINT_FILE.exists():
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 📂 Loading checkpoint...')
        try:
            df = pd.read_json(CHECKPOINT_FILE)
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Checkpoint loaded: {len(df)} titles')
            return df, True
        except Exception as e:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ⚠️ Error loading checkpoint: {e}')
    
    return None, False


def save_checkpoint(df):
    """Save checkpoint (overwrites previous checkpoint)"""
    df.to_json(CHECKPOINT_FILE, orient='records', indent=2, force_ascii=False)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 💾 Checkpoint saved')


def enrich_dataframe(df, checkpoint_every=50):
    """
    Enrich DataFrame with IMDb data
    Saves checkpoints periodically to single file
    """
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 🔍 Starting IMDb enrichment...')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 Processing {len(df)} titles')
    
    # Add IMDb columns if they don't exist
    imdb_columns = [
        'imdb_id', 'imdb_rating', 'imdb_votes', 'year', 'rated',
        'runtime', 'genres', 'director', 'actors', 'plot', 
        'awards', 'imdb_poster', 'content_type', 'total_seasons'
    ]
    
    for col in imdb_columns:
        if col not in df.columns:
            df[col] = None
    
    # Track statistics
    found_count = 0
    not_found_count = 0
    skipped_count = 0
    
    # Find where to start (first row without imdb_id)
    start_index = 0
    if 'imdb_id' in df.columns:
        unenriched = df[df['imdb_id'].isna()]
        if len(unenriched) > 0:
            start_index = unenriched.index[0]
            skipped_count = start_index
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ⏭️ Resuming from index {start_index}')
    
    # Process each row
    for idx in range(start_index, len(df)):
        row = df.iloc[idx]
        title = row['title']
        
        # Skip if already enriched
        if pd.notna(row.get('imdb_id')):
            skipped_count += 1
            continue
        
        # Progress update
        if idx % 10 == 0 and idx > start_index:
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📍 Progress: {idx}/{len(df)} ({idx*100//len(df)}%)')
            print(f'  Found: {found_count} | Not Found: {not_found_count} | Skipped: {skipped_count}')
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔎 Searching: {title}')
        
        # Search OMDb
        imdb_data = search_omdb(title)
        
        if imdb_data:
            for key, value in imdb_data.items():
                col_name = key if key != 'poster' else 'imdb_poster'
                df.at[idx, col_name] = value
            
            rating = imdb_data.get('imdb_rating', 'N/A')
            print(f'  ✅ Found! Rating: {rating}')
            found_count += 1
        else:
            print(f'  ❌ Not found on IMDb')
            not_found_count += 1
        
        # Checkpoint: Save progress every N items
        if (idx + 1) % checkpoint_every == 0:
            save_checkpoint(df)
        
        # Rate limiting
        time.sleep(1.1)
    
    # Final statistics
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ✅ Enrichment complete!')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 Final Stats:')
    print(f'  ✅ Found: {found_count}')
    print(f'  ❌ Not found: {not_found_count}')
    print(f'  ⏭️ Skipped: {skipped_count}')
    
    save_checkpoint(df)
    
    return df


def filter_and_rank(df, min_rating=7.0, min_votes=1000):
    """Filter and rank movies by IMDb rating"""
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 🔍 Filtering movies...')
    
    df['imdb_rating_numeric'] = pd.to_numeric(df['imdb_rating'], errors='coerce')
    
    def clean_votes(votes):
        if pd.isna(votes) or votes == "N/A":
            return 0
        return int(str(votes).replace(',', ''))
    
    df['imdb_votes_numeric'] = df['imdb_votes'].apply(clean_votes)
    
    filtered = df[
        (df['imdb_rating_numeric'] >= min_rating) &
        (df['imdb_votes_numeric'] >= min_votes) &
        (df['watched'] == False)
    ].copy()
    
    filtered = filtered.sort_values('imdb_rating_numeric', ascending=False)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Filtered to {len(filtered)} high-rated unwatched titles')
    
    return filtered


def export_results(df, filtered_df):
    """Export results in multiple formats"""
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 💾 Exporting results...')
    
    df.to_json(ENRICHED_COMPLETE_FILE, orient='records', indent=2, force_ascii=False)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Saved: {ENRICHED_COMPLETE_FILE}')
    
    filtered_df.to_json(HIGH_RATED_FILE, orient='records', indent=2, force_ascii=False)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Saved: {HIGH_RATED_FILE}')
    
    filtered_df.to_csv(RECOMMENDATIONS_CSV, index=False, encoding='utf-8')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Saved: {RECOMMENDATIONS_CSV}')
    
    simple_list = filtered_df[['title', 'imdb_rating', 'year', 'genres', 'plot', 'categories']].to_dict('records')
    with open(SIMPLE_RECS_FILE, 'w', encoding='utf-8') as f:
        json.dump(simple_list, f, indent=2, ensure_ascii=False)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Saved: {SIMPLE_RECS_FILE}')


def print_summary(df, filtered_df):
    """Print summary statistics"""
    print(f'\n{"="*70}')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 SUMMARY')
    print(f'{"="*70}')
    
    print(f'\n📺 Total titles: {len(df)}')
    print(f'✅ Found on IMDb: {df["imdb_id"].notna().sum()}')
    print(f'❌ Not found: {df["imdb_id"].isna().sum()}')
    print(f'👁️ Already watched: {df["watched"].sum()}')
    print(f'🎯 High-rated unwatched: {len(filtered_df)}')
    
    if len(filtered_df) > 0:
        print(f'\n🏆 TOP 10 RECOMMENDATIONS:')
        for idx, row in filtered_df.head(10).iterrows():
            cats = ', '.join(row['categories'][:2]) if isinstance(row['categories'], list) else row.get('categories', 'N/A')
            print(f'  {row["imdb_rating"]} - {row["title"]} ({row.get("year", "N/A")})')
            print(f'       {cats}')


def main():
    """Main execution pipeline"""
    print(f'\n{"="*70}')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 🚀 Netflix IMDb Enrichment Pipeline')
    print(f'{"="*70}')
    
    # Check if we have existing enriched data
    if ENRICHED_COMPLETE_FILE.exists():
        print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📂 Found existing enriched data')
        existing_enriched = pd.read_json(ENRICHED_COMPLETE_FILE)
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 Existing: {len(existing_enriched)} titles')
        
        # Load new browse data
        if NETFLIX_BROWSE_FILE.exists():
            new_browse = pd.read_json(NETFLIX_BROWSE_FILE)
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 New browse: {len(new_browse)} titles')
            
            # Merge datasets
            merged_existing, new_titles_df, new_count = merge_existing_with_new(
                existing_enriched, new_browse
            )
            
            if new_count > 0:
                print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔍 Enriching {new_count} new titles...')
                
                # Mark watched status for new titles
                watched_titles = load_viewing_activity()
                new_titles_df = mark_watched_items(new_titles_df, watched_titles)
                
                # Enrich only new titles
                new_titles_enriched = enrich_dataframe(new_titles_df, checkpoint_every=50)
                
                # Combine everything
                df = pd.concat([merged_existing, new_titles_enriched], ignore_index=True)
                
                # Remove duplicates (just in case)
                df = df.drop_duplicates(subset=['netflixId'], keep='first')
                
                print(f'[{datetime.now().strftime("%H:%M:%S")}] 💾 Total after merge: {len(df)} titles')
            else:
                print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ No new titles to enrich')
                df = merged_existing
        else:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ⚠️ No new browse data found')
            df = existing_enriched
        
        # Always regenerate filtered recommendations
        filtered_df = filter_and_rank(df, min_rating=7.5, min_votes=5000)
        export_results(df, filtered_df)
        print_summary(df, filtered_df)
        
    else:
        # No existing data - start from scratch
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 📂 No existing data, starting fresh...')
        
        df, has_checkpoint = load_checkpoint()
        
        if not has_checkpoint:
            df = load_netflix_data()
            watched_titles = load_viewing_activity()
            df = mark_watched_items(df, watched_titles)
        
        df = enrich_dataframe(df, checkpoint_every=50)
        filtered_df = filter_and_rank(df, min_rating=7.5, min_votes=5000)
        export_results(df, filtered_df)
        print_summary(df, filtered_df)
        
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 🧹 Checkpoint removed')
    
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ✨ All done!\n')


if __name__ == '__main__':
    main()
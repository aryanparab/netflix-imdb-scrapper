import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path

# Data directories
DATA_DIR = Path('data')
INPUT_DIR = DATA_DIR / 'input'
OUTPUT_DIR = DATA_DIR / 'output'

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BROWSE_FILE = INPUT_DIR / 'netflix-browse-complete.json'

async def scrape_netflix_browse_optimized():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=30
        )
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔐 Loading saved session...')
        context = await browser.new_context(
            storage_state='netflix-session.json',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 🌐 Navigating to Netflix browse...')
            
            await page.goto('https://www.netflix.com/browse', wait_until='domcontentloaded')
            await asyncio.sleep(5)
            
            if 'login' in page.url:
                print(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Session expired! Run login.py')
                return
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Page loaded')
            
            # STEP 1: Scroll to load ALL rows
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📜 Scrolling to load all category rows...')
            await load_all_rows(page)
            
            # STEP 2: Get all row names
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📋 Getting all category names...')
            row_names = await page.evaluate('''
                () => {
                    const elements = document.getElementsByClassName(
                        "lolomoRow lolomoRow_title_card"
                    );
                    const names = [];
                    for (let elem of elements) {
                        try {
                            const headerElem = elem.getElementsByClassName('row-header-title')[0];
                            if (headerElem) {
                                names.push(headerElem.innerText.trim());
                            }
                        } catch (e) {}
                    }
                    return names;
                }
            ''')
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Found {len(row_names)} categories')
            
            # STEP 3: Get all row containers
            row_containers = await page.query_selector_all('.lolomoRow.lolomoRow_title_card .rowContainer')
            
            if len(row_containers) != len(row_names):
                row_names = row_names[:len(row_containers)]
            
            all_movies = []
            
            # STEP 4: Process each row
            for idx, (row_name, row_container) in enumerate(zip(row_names, row_containers), 1):
                print(f'\n{"="*70}')
                print(f'[{datetime.now().strftime("%H:%M:%S")}] 📂 Row {idx}/{len(row_names)}: {row_name}')
                
                try:
                    row_items = await extract_all_from_row(page, row_container, row_name, idx)
                    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Got {len(row_items)} items')
                    all_movies.extend(row_items)
                except Exception as e:
                    print(f'[{datetime.now().strftime("%H:%M:%S")}] ⚠️ Error in row: {str(e)[:80]}')
                    continue
            
            # STEP 5: Merge with existing data
            print(f'\n{"="*70}')
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔄 Processing results...')
            
            unique_movies = merge_duplicates(all_movies)
            
            # Check if we have existing data
            existing_movies = []
            if BROWSE_FILE.exists():
                print(f'[{datetime.now().strftime("%H:%M:%S")}] 📂 Found existing browse data')
                with open(BROWSE_FILE, 'r', encoding='utf-8') as f:
                    existing_movies = json.load(f)
                print(f'[{datetime.now().strftime("%H:%M:%S")}] 📊 Existing: {len(existing_movies)} movies')
            
            # Merge with existing data
            final_movies = merge_with_existing(existing_movies, unique_movies)
            
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📊 FINAL RESULTS:')
            print(f'  New scraped: {len(all_movies)}')
            print(f'  Unique from scrape: {len(unique_movies)}')
            print(f'  Total after merge: {len(final_movies)}')
            
            # Save to file
            with open(BROWSE_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_movies, f, indent=2, ensure_ascii=False)
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 💾 Saved to {BROWSE_FILE}')
            
            # Keep browser open
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 👀 Keeping browser open for 10 seconds...')
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ❌ Fatal error: {str(e)}')
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 👋 Done!\n')


async def load_all_rows(page):
    """Scroll down to load all category rows"""
    previous_count = 0
    no_change_count = 0
    max_attempts = 25
    
    for attempt in range(max_attempts):
        current_count = await page.evaluate('''
            () => {
                return document.getElementsByClassName("lolomoRow lolomoRow_title_card").length;
            }
        ''')
        
        if current_count > previous_count:
            print(f'[{datetime.now().strftime("%H:%M:%S")}]   Loaded {current_count} rows...')
            previous_count = current_count
            no_change_count = 0
        else:
            no_change_count += 1
        
        if no_change_count >= 3:
            break
        
        await page.evaluate('window.scrollBy(0, 800)')
        await asyncio.sleep(1.5)
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}]   ✅ Total rows loaded: {current_count}')


async def extract_all_from_row(page, row_container, category_name, row_index):
    """Extract all items from a single row by clicking arrows"""
    seen_titles = set()
    seen_netflix_ids = set()
    row_items = []
    
    max_arrow_clicks = 25
    consecutive_no_new = 0
    
    for click_num in range(max_arrow_clicks):
        visible_items = await row_container.evaluate('''
            (container, categoryName) => {
                const items = [];
                const titleCards = container.querySelectorAll('.slider-item .title-card');
                
                titleCards.forEach(card => {
                    try {
                        const fallbackText = card.querySelector('.fallback-text');
                        const title = fallbackText ? fallbackText.textContent.trim() : null;
                        
                        const link = card.querySelector('a');
                        const href = link ? link.href : null;
                        
                        const img = card.querySelector('img.boxart-image');
                        const image = img ? img.src : null;
                        
                        let netflixId = null;
                        if (href) {
                            const match = href.match(/\\/watch\\/(\\d+)/);
                            if (match) netflixId = match[1];
                        }
                        
                        if (!netflixId) {
                            const trackingElem = card.querySelector('[data-ui-tracking-context]');
                            if (trackingElem) {
                                try {
                                    const trackingData = JSON.parse(trackingElem.getAttribute('data-ui-tracking-context'));
                                    netflixId = trackingData.video_id?.toString();
                                } catch (e) {}
                            }
                        }
                        
                        if (title) {
                            items.push({
                                title: title,
                                category: categoryName,
                                netflixId: netflixId,
                                image: image,
                                link: href
                            });
                        }
                    } catch (e) {}
                });
                
                return items;
            }
        ''', category_name)
        
        new_items_count = 0
        for item in visible_items:
            identifier = item['netflixId'] if item['netflixId'] else item['title']
            
            if identifier not in seen_netflix_ids and item['title'] not in seen_titles:
                seen_titles.add(item['title'])
                if item['netflixId']:
                    seen_netflix_ids.add(item['netflixId'])
                row_items.append(item)
                new_items_count += 1
        
        if new_items_count > 0:
            print(f'[{datetime.now().strftime("%H:%M:%S")}]   +{new_items_count} new (Total: {len(row_items)})')
            consecutive_no_new = 0
        else:
            consecutive_no_new += 1
        
        if consecutive_no_new >= 2:
            print(f'[{datetime.now().strftime("%H:%M:%S")}]   No more new items')
            break
        
        try:
            arrow_clicked = await click_next_arrow(row_container)
            if not arrow_clicked:
                print(f'[{datetime.now().strftime("%H:%M:%S")}]   No more arrows')
                break
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}]   → Arrow click #{click_num + 1}')
            await asyncio.sleep(1.2)
        except Exception as e:
            break
    
    return row_items


async def click_next_arrow(row_container):
    """Try to click the next arrow button in a row"""
    try:
        arrow = await row_container.query_selector('.handle.handleNext')
        if not arrow:
            return False
        
        is_visible = await arrow.is_visible()
        if not is_visible:
            return False
        
        class_name = await arrow.get_attribute('class')
        if 'active' not in class_name:
            return False
        
        await arrow.scroll_into_view_if_needed()
        await asyncio.sleep(0.2)
        await arrow.click()
        return True
    except Exception as e:
        return False


def merge_duplicates(movies):
    """Merge duplicate movies within the scraped data, combining categories"""
    unique = {}
    
    for movie in movies:
        title = movie['title']
        
        if title in unique:
            if movie['category'] not in unique[title]['categories']:
                unique[title]['categories'].append(movie['category'])
        else:
            movie['categories'] = [movie['category']]
            del movie['category']
            unique[title] = movie
    
    return list(unique.values())


def merge_with_existing(existing_movies, new_movies):
    """
    Merge new scraped movies with existing database
    - Preserves watched status and IMDb data from existing
    - Adds new categories from new scrape
    - Adds completely new movies
    """
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔄 Merging data...')
    
    # Create a map of existing movies by netflixId
    existing_map = {}
    for movie in existing_movies:
        if movie.get('netflixId'):
            existing_map[movie['netflixId']] = movie
    
    added_count = 0
    updated_count = 0
    
    # Process new movies
    for new_movie in new_movies:
        if not new_movie.get('netflixId'):
            # No Netflix ID - try to match by title
            title_match = None
            for existing_movie in existing_movies:
                if existing_movie.get('title', '').lower() == new_movie.get('title', '').lower():
                    title_match = existing_movie
                    break
            
            if title_match and not title_match.get('netflixId'):
                # Found match by title - merge categories
                all_categories = list(set(
                    (title_match.get('categories', []) or []) + 
                    (new_movie.get('categories', []) or [])
                ))
                title_match['categories'] = all_categories
                updated_count += 1
            else:
                # New movie without ID - add it
                new_movie['watched'] = False
                existing_movies.append(new_movie)
                added_count += 1
            continue
        
        netflix_id = new_movie['netflixId']
        
        if netflix_id in existing_map:
            # Movie exists - merge categories and preserve important data
            existing_movie = existing_map[netflix_id]
            
            # Merge categories (unique values)
            all_categories = list(set(
                (existing_movie.get('categories', []) or []) + 
                (new_movie.get('categories', []) or [])
            ))
            
            # Update existing movie
            existing_movie['categories'] = all_categories
            existing_movie['image'] = new_movie.get('image') or existing_movie.get('image')
            existing_movie['link'] = new_movie.get('link') or existing_movie.get('link')
            
            # Preserve these fields from existing data
            # (watched status, IMDb data, etc. should not be overwritten)
            
            updated_count += 1
        else:
            # New movie - add it
            new_movie['watched'] = False
            existing_map[netflix_id] = new_movie
            existing_movies.append(new_movie)
            added_count += 1
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}]   ➕ Added: {added_count} new movies')
    print(f'[{datetime.now().strftime("%H:%M:%S")}]   🔄 Updated: {updated_count} existing movies')
    
    return existing_movies


if __name__ == '__main__':
    asyncio.run(scrape_netflix_browse_optimized())
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path

# Data directories
DATA_DIR = Path('data')
INPUT_DIR = DATA_DIR / 'input'

INPUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWING_ACTIVITY_FILE = INPUT_DIR / 'netflix-viewing-activity.json'

async def scrape_viewing_activity():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 🔐 Loading saved session...')
        context = await browser.new_context(
            storage_state='netflix-session.json'
        )
        
        page = await context.new_page()
        
        try:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 🌐 Navigating to viewing activity...')
            
            await page.goto('https://www.netflix.com/viewingactivity', 
                          wait_until='domcontentloaded')
            
            await asyncio.sleep(3)
            
            # Check if logged in
            current_url = page.url
            if 'login' in current_url:
                print(f'[{datetime.now().strftime("%H:%M:%S")}] ❌ Session expired! Please run login.py again.')
                return
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Page loaded, starting scroll...')
            
            # Scroll to load all content
            previous_height = 0
            scroll_count = 0
            max_scrolls = 50
            
            while scroll_count < max_scrolls:
                current_height = await page.evaluate('document.body.scrollHeight')
                
                if current_height == previous_height:
                    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Reached end of page')
                    break
                
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                
                scroll_count += 1
                print(f'[{datetime.now().strftime("%H:%M:%S")}] 📜 Scroll #{scroll_count} (height: {current_height}px)')
                
                await asyncio.sleep(2)
                previous_height = current_height
            
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📊 Extracting viewing data...')
            
            # Extract all viewing activity
            viewing_data = await page.evaluate('''
                () => {
                    const rows = document.querySelectorAll('.retableRow');
                    const data = [];
                    
                    rows.forEach(row => {
                        const titleElement = row.querySelector('.title a');
                        const dateElement = row.querySelector('.date');
                        
                        if (titleElement && dateElement) {
                            const url = titleElement.href;
                            const idMatch = url.match(/\\/watch\\/(\\d+)/);
                            
                            data.push({
                                title: titleElement.textContent.trim(),
                                date: dateElement.textContent.trim(),
                                url: url,
                                netflixId: idMatch ? idMatch[1] : null
                            });
                        }
                    });
                    
                    return data;
                }
            ''')
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Found {len(viewing_data)} items')
            
            # Save to file
            with open(VIEWING_ACTIVITY_FILE, 'w', encoding='utf-8') as f:
                json.dump(viewing_data, f, indent=2, ensure_ascii=False)
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 💾 Saved to {VIEWING_ACTIVITY_FILE}')
            
            # Print first 10 items
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 📺 First 10 items:')
            for i, item in enumerate(viewing_data[:10], 1):
                print(f"  {i}. {item['title']} - {item['date']}")
            
            if len(viewing_data) > 10:
                print(f"  ... and {len(viewing_data) - 10} more")
            
            # Keep browser open
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 👀 Keeping browser open for 5 seconds...')
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ❌ Error: {str(e)}')
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 👋 Done!\n')

if __name__ == '__main__':
    asyncio.run(scrape_viewing_activity())
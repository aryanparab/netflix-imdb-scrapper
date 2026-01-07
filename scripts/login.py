import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def login_to_netflix():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 🚀 Starting Netflix login process...')
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 🌐 Navigating to Netflix login page...')
            
            await page.goto('https://www.netflix.com/login', wait_until='domcontentloaded')
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Login page loaded')
            print('\n' + '='*60)
            print('🔐 Please complete login in the browser window')
            print('⏳ Waiting for you to reach browse or profiles page...')
            print('='*60 + '\n')
            
            # Simple approach: just wait for URL to change
            # This won't break during navigation
            timeout = 300  # 5 minutes
            elapsed = 0
            
            while elapsed < timeout:
                if elapsed % 10 == 0 and elapsed > 0:
                    print(f'[{datetime.now().strftime("%H:%M:%S")}] ⏱️  Still waiting... ({elapsed}s elapsed)')
                
                try:
                    current_url = page.url
                    
                    if 'browse' in current_url:
                        print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Detected browse page!')
                        break
                    elif 'profiles' in current_url:
                        print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Detected profiles page!')
                        break
                    elif '/login' not in current_url and 'netflix.com' in current_url:
                        # User navigated away from login page
                        print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Navigated away from login: {current_url}')
                        break
                        
                except Exception as e:
                    # Even URL checking can occasionally fail during rapid navigation
                    pass
                
                await asyncio.sleep(2)
                elapsed += 2
            
            if elapsed >= timeout:
                raise Exception('Login timeout - took longer than 5 minutes')
            
            # Wait a bit more for page to settle
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ⏳ Waiting for page to stabilize...')
            await asyncio.sleep(3)
            
            # Try to wait for network to be idle (with timeout)
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except:
                print(f'[{datetime.now().strftime("%H:%M:%S")}] ⚠️  Network still active, continuing anyway...')
            
            # Save session
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 💾 Saving session data...')
            
            cookies = await context.cookies()
            with open('netflix-cookies.json', 'w') as f:
                json.dump(cookies, f, indent=2)
            
            await context.storage_state(path='netflix-session.json')
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Saved {len(cookies)} cookies')
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Session saved to netflix-session.json')
            
            final_url = page.url
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 📍 Final URL: {final_url}')
            
            # Keep browser open
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] 👀 Keeping browser open for 10 seconds...')
            await page.wait_for_timeout(10000)
            
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ✨ Success! Session saved.')
            
        except Exception as e:
            print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ❌ Error: {str(e)}')
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 👋 Browser closed\n')

if __name__ == '__main__':
    asyncio.run(login_to_netflix())
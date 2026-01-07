# 🎬 Netflix IMDb Recommender

> Your personal Netflix recommendation system powered by IMDb ratings. Discover hidden gems and filter out the noise from your Netflix catalog.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg?logo=react)](https://reactjs.org/)
[![Express](https://img.shields.io/badge/Express-4.18+-green.svg?logo=express)](https://expressjs.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 What Makes This Special?

Netflix shows you thousands of titles, but which ones are actually worth watching? **Netflix IMDb Recommender** solves this by:

- 🔍 **Scraping** your personalized Netflix recommendations
- ⭐ **Enriching** them with real IMDb ratings and metadata
- 🎯 **Filtering** to show only highly-rated content you haven't watched yet
- 💎 **Discovering** hidden gems that match your taste with actual quality scores

### The Problem It Solves

Netflix's algorithm suggests content based on viewing patterns, but doesn't always reflect actual quality. You might see:
- Low-rated shows pushed because they're "Netflix Originals"
- Clickbait content with misleading thumbnails
- Shows that were popular but aren't actually good

**This app combines Netflix's personalization with IMDb's crowd-sourced quality ratings** to give you the best of both worlds.

---

## ✨ Features

### 🎨 Beautiful Modern UI
- **Glassmorphism design** with smooth gradients and animations
- **Responsive layout** works perfectly on desktop, tablet, and mobile
- **Dark theme** optimized for comfortable viewing
- **Intuitive filters** for quick discovery

### 🔧 Powerful Admin Panel
- **One-click scraping** with real-time progress logs
- **Full pipeline automation** - run everything with a single button
- **Session management** - login once, scrape many times
- **Status dashboard** - see what data you have at a glance

### 🎯 Smart Filtering
- **By Category**: "Trending Now", "Because You Watched", "Award Winners", etc.
- **By Genre**: Drama, Comedy, Action, Documentary, and more
- **By Rating**: Set minimum IMDb rating (7.5+, 8.0+, etc.)
- **By Status**: Show only unwatched or watched content
- **Search**: Find specific titles instantly

### 💡 Intelligent Features
- **Watched Status Tracking**: Mark shows as watched, status persists
- **Smart Data Merging**: Re-scrape without losing your watched history
- **Category Aggregation**: Shows appear in all their Netflix categories
- **Incremental Updates**: Only enriches new titles on subsequent runs
- **Checkpoint System**: Resume IMDb enrichment if interrupted

---

## 📸 Screenshots

### Main Application
![Main App Interface](screenshots/main-app.png)
*Filter and browse your highly-rated Netflix recommendations*

### Admin Panel
![Admin Panel](screenshots/admin-panel.png)
*Manage scraping jobs and view real-time logs*

### Movie Cards
![Movie Cards](screenshots/movie-cards.png)
*Rich metadata including IMDb ratings, genres, and plot summaries*

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Netflix Account**
- **OMDb API Key** (free from [omdbapi.com](https://www.omdbapi.com/apikey.aspx))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/netflix-imdb-recommender.git
cd netflix-imdb-recommender

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Create .env file with your OMDb API key
echo "OMDB_API_KEY=your_api_key_here" > .env

# 6. You're ready to go!
```

### Running the App

**Two terminals required:**

```bash
# Terminal 1 - Backend (Flask)
python app.py

# Terminal 2 - Frontend (React)
cd frontend && npm start
```

Open **http://localhost:3000** in your browser.

---

## 📖 How to Use

### First Time Setup (5 minutes)

1. **Get Your API Key**
   - Visit [omdbapi.com/apikey.aspx](https://www.omdbapi.com/apikey.aspx)
   - Sign up for free (1,000 requests/day)
   - Add key to `.env` file

2. **Login to Netflix**
   - Click "Admin Panel" in top right
   - Go to "Scraper Tools"
   - Click "Netflix Login"
   - Complete login in the browser window that opens
   - Session saved automatically ✓

3. **Run Full Pipeline**
   - Click "Run Full Pipeline" button
   - This will:
     - Scrape your viewing activity (~2 min)
     - Scrape Netflix browse page (~5-10 min)
     - Enrich with IMDb data (~10-30 min depending on catalog size)
   - Watch progress in real-time logs

4. **Browse Your Recommendations**
   - Go back to main app
   - See your highly-rated, unwatched recommendations
   - Use filters to narrow down choices
   - Click "Watch on Netflix" to start viewing

### Daily Usage

**Option A: Quick Update (Recommended)**
- Go to Admin Panel → Scraper Tools
- Click "Browse Page" to get new recommendations
- New titles automatically merged with existing data
- Only new titles get enriched with IMDb data

**Option B: Manual Control**
- Run individual scripts as needed
- View logs for each step
- Check status dashboard for data availability

---

## 🏗️ Architecture

### Technology Stack

**Frontend**
```
React 18.2          → UI Framework
React Router 6      → Navigation
Axios               → API Calls
CSS3                → Styling (Glassmorphism, Gradients)
```

**Backend**
```
Flask 3.0           → Web Framework
Express.js 4.18     → Alternative Backend (Node.js)
Playwright 1.41     → Web Scraping
Pandas 2.1          → Data Processing
Requests 2.31       → API Calls (OMDb)
```

**Data Flow**
```
Netflix → Playwright Scraper → JSON Files → 
OMDb API → Data Enrichment → Filtered Results → 
React UI → User Interaction
```

### Project Structure

```
netflix-imdb-recommender/
│
├── 🎨 Frontend (React)
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── Header.jsx
│   │   │   ├── StatsBar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── MovieCard.jsx
│   │   │   └── MoviesGrid.jsx
│   │   ├── pages/
│   │   │   └── AdminPanel.jsx   # Admin dashboard
│   │   ├── styles/
│   │   │   ├── App.css
│   │   │   └── AdminPanel.css
│   │   └── App.jsx              # Main app with routing
│   └── package.json
│
├── 🔧 Backend (Python)
│   ├── app.py                   # Flask server (recommended)
│   ├── enrich_with_imdb.py      # IMDb enrichment script
│   └── scripts/
│       ├── login.py                      # Netflix authentication
│       ├── scrape_viewing_activity.py    # Watch history
│       └── scrape_browse_complete.py     # Recommendations
│
├── 🔧 Backend (Node.js - Alternative)
│   ├── server.js                # Express server
│   ├── controllers/
│   │   ├── moviesController.js
│   │   └── scraperController.js
│   └── utils/
│       ├── pythonRunner.js      # Python script executor
│       └── dataManager.js       # Data handling
│
├── 💾 Data
│   ├── input/                   # Raw scraped data
│   │   ├── netflix-browse-complete.json
│   │   └── netflix-viewing-activity.json
│   ├── output/                  # Processed data
│   │   ├── enriched_netflix_complete.json
│   │   ├── high_rated_recommendations.json
│   │   ├── recommendations.csv
│   │   └── simple_recommendations.json
│   └── checkpoints/             # Resume points
│       └── enrichment_checkpoint.json
│
├── 📝 Configuration
│   ├── .env                     # API keys (not committed)
│   ├── requirements.txt         # Python dependencies
│   └── .gitignore
│
└── 📚 Documentation
    ├── README.md
    └── screenshots/
```

---

## 🎯 API Reference

### REST Endpoints

#### Movies API

```http
GET /api/movies
```
Get filtered movies with optional query parameters:
- `category` - Filter by Netflix category
- `genre` - Filter by genre
- `min_rating` - Minimum IMDb rating (0-10)
- `max_rating` - Maximum IMDb rating (0-10)
- `search` - Search by title
- `watched` - Filter by watched status (all/watched/unwatched)

```http
GET /api/categories
```
Returns array of all unique Netflix categories

```http
GET /api/genres
```
Returns array of all unique genres

```http
GET /api/stats
```
Returns statistics:
```json
{
  "total": 250,
  "watched": 45,
  "unwatched": 205,
  "avg_rating": 8.2,
  "top_genres": {
    "Drama": 78,
    "Comedy": 62,
    "Action": 45
  }
}
```

```http
POST /api/movie/:netflixId/watched
```
Mark movie as watched/unwatched
```json
{
  "watched": true
}
```

#### Scraper API

```http
POST /api/scraper/login
```
Run Netflix login script (opens browser)

```http
POST /api/scraper/viewing-activity
```
Scrape Netflix viewing activity

```http
POST /api/scraper/browse
```
Scrape Netflix browse page (merges with existing data)

```http
POST /api/scraper/enrich
```
Enrich with IMDb data (only processes new titles)

```http
POST /api/scraper/full-pipeline
```
Run all scraping steps in sequence

```http
GET /api/scraper/status
```
Check which data files exist
```json
{
  "session_exists": true,
  "cookies_exist": true,
  "browse_data_exists": true,
  "viewing_activity_exists": true,
  "enriched_data_exists": true
}
```

---

## 🔐 How It Works

### 1. Authentication
- Uses Playwright to open Netflix login page
- You complete login manually (for security)
- Session cookies saved locally
- Reused for future scrapes (until they expire)

### 2. Viewing Activity Scraping
- Navigates to `netflix.com/viewingactivity`
- Auto-scrolls to load complete history
- Extracts titles and dates
- Used to mark shows as "watched" in the UI

### 3. Browse Page Scraping
- Loads `netflix.com/browse`
- Scrolls to reveal all recommendation rows
- For each row:
  - Clicks arrows to reveal all titles
  - Extracts: title, image, link, Netflix ID, category
- Smart duplicate detection (stops when no new items)
- Merges with existing data (preserves enriched info)

### 4. IMDb Enrichment
- For each title, queries OMDb API
- Retrieves: rating, votes, year, genres, plot, actors, etc.
- Rate-limited to 1 request per 1.1 seconds (free tier)
- Saves checkpoints every 50 items
- Skips titles already enriched
- Merges intelligently:
  - Preserves watched status
  - Keeps existing IMDb data
  - Combines categories from multiple scrapes

### 5. Smart Merging
When re-scraping:
- Matches by Netflix ID (most reliable)
- Falls back to title matching
- Updates: categories, images, links
- Preserves: IMDb data, watched status
- Only enriches genuinely new titles

---

## 🎓 Key Algorithms

### Duplicate Detection (Browse Scraper)
```python
seen_titles = set()
seen_netflix_ids = set()

for item in visible_items:
    identifier = item['netflixId'] or item['title']
    
    if identifier not in seen_ids:
        items.append(item)
        seen_ids.add(identifier)
    
    if no_new_items_for_2_attempts:
        break  # All items loaded
```

### Data Merging (Enrichment)
```python
def merge_existing_with_new(existing_df, new_df):
    # Match by Netflix ID first
    existing_by_id = {row['netflixId']: idx}
    
    for new_row in new_df:
        if new_row['netflixId'] in existing_by_id:
            # Merge categories
            merge_categories(existing_row, new_row)
            # Preserve IMDb data and watched status
        else:
            # New title - add to enrichment queue
            new_titles.append(new_row)
```

### Rating Filter
```python
filtered = df[
    (df['imdb_rating'] >= min_rating) &
    (df['imdb_votes'] >= min_votes) &
    (df['watched'] == False)
].sort_values('imdb_rating', ascending=False)
```

---

## 📊 Performance & Limits

### Scraping Speed
| Task | Duration | Notes |
|------|----------|-------|
| Login | 30s | Manual interaction required |
| Viewing Activity | 1-3 min | Depends on watch history size |
| Browse Page | 5-10 min | Depends on recommendation count |
| IMDb Enrichment | 10-30 min | Rate limited by OMDb API |

### API Limits (OMDb Free Tier)
- **1,000 requests per day**
- **1 request per second** (rate limited in code)
- Sufficient for most users (~250 titles = 250 requests)
- Consider paid tier for large catalogs (10,000+ requests/day)

### Storage
- **~5-10 MB** for 500 titles (enriched JSON)
- **Incremental growth** as new titles discovered
- **Efficient**: Only new titles enriched on re-scrape

---

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in project root:

```bash
# Required
OMDB_API_KEY=your_api_key_here

# Optional
FLASK_ENV=development
FLASK_PORT=5000
REACT_PORT=3000
```

### Customizing Filters

Edit `enrich_with_imdb.py` to change default thresholds:

```python
# Line ~450
filtered_df = filter_and_rank(
    df, 
    min_rating=7.5,      # Change minimum rating
    min_votes=5000       # Change minimum vote count
)
```

### Rate Limiting

Adjust OMDb request delay in `enrich_with_imdb.py`:

```python
# Line ~280
time.sleep(1.1)  # Increase for slower, safer scraping
```

---

## 🐛 Troubleshooting

### "Session expired" when scraping
**Solution**: Run the login script again
```bash
# Via UI: Admin Panel → Netflix Login
# Via CLI: python scripts/login.py
```

### "OMDB_API_KEY not found"
**Solution**: Create `.env` file with your API key
```bash
echo "OMDB_API_KEY=your_key" > .env
```

### Netflix shows different content
**Netflix recommendations are personalized and change daily**
- Re-scrape browse page to get latest
- Your recommendations differ from others
- Categories appear/disappear based on Netflix's algorithm

### Enrichment taking too long
**Each title needs 1 API call (1.1s each)**
- 250 titles = ~5 minutes minimum
- Use checkpoint system to resume if interrupted
- Consider paid OMDb tier for faster processing

### Port already in use
```bash
# Find and kill process
# macOS/Linux:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

## 🚧 Roadmap

### Planned Features

- [ ] **User Accounts**: Multi-user support with individual watchlists
- [ ] **Recommendations Engine**: ML-based personalized suggestions
- [ ] **Streaming Availability**: Check which services have each title
- [ ] **Price Comparison**: Compare rental/purchase prices across platforms
- [ ] **Watchlist Sync**: Import from IMDb, Letterboxd, Trakt
- [ ] **Social Features**: Share recommendations with friends
- [ ] **Mobile App**: React Native version
- [ ] **Email Notifications**: Weekly digest of new high-rated content
- [ ] **Advanced Analytics**: Viewing patterns and preference insights
- [ ] **Export Options**: PDF reports, Excel spreadsheets
- [ ] **Scheduling**: Auto-scrape daily/weekly
- [ ] **Multiple Profiles**: Support Netflix profile switching
- [ ] **Trailer Integration**: YouTube trailers in-app

### Future Improvements

- [ ] Async scraping with WebSockets for real-time progress
- [ ] Database migration (PostgreSQL or MongoDB)
- [ ] Caching layer (Redis) for faster API responses
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] CI/CD pipeline
- [ ] Unit and integration tests
- [ ] API documentation (Swagger/OpenAPI)

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Guidelines

- Follow existing code style
- Add comments for complex logic
- Update README for new features
- Test thoroughly before submitting

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### What this means:
✅ Commercial use allowed  
✅ Modification allowed  
✅ Distribution allowed  
✅ Private use allowed  

⚠️ Use at your own risk (no warranty)

---

## ⚠️ Disclaimer

This project is for **personal, educational use only**. 

- **Not affiliated with Netflix**: This is an independent project
- **Terms of Service**: Check Netflix ToS before scraping
- **Rate Limiting**: Respects Netflix's servers with delays
- **No Piracy**: Only organizes your legitimate Netflix access
- **API Usage**: Complies with OMDb API terms

**Use responsibly and respect Netflix's terms of service.**

---

## 🙏 Acknowledgments

- **Netflix** - For the content platform
- **IMDb/OMDb** - For ratings and metadata API
- **Playwright** - For reliable web scraping
- **React** - For the incredible UI framework
- **Open Source Community** - For all the amazing tools

---

## 📧 Contact

**Your Name** - [@yourtwitter](https://twitter.com/yourtwitter)

Project Link: [https://github.com/yourusername/netflix-imdb-recommender](https://github.com/yourusername/netflix-imdb-recommender)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/netflix-imdb-recommender&type=Date)](https://star-history.com/#yourusername/netflix-imdb-recommender&Date)

---

<div align="center">

**Made with ❤️ and lots of ☕**

If this project helped you discover your next binge-worthy show, consider giving it a ⭐!

[⬆ Back to Top](#-netflix-imdb-recommender)

</div>

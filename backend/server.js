import express from 'express';
import cors from 'cors';
import { ensureDirectories } from './utils/dataManager.js';

// Import controllers
import * as moviesController from './controllers/moviesController.js';
import * as scraperController from './controllers/scraperController.js';

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Ensure data directories exist
await ensureDirectories();

// ===== Movie Routes =====
app.get('/api/movies', moviesController.getMovies);
app.get('/api/categories', moviesController.getCategories);
app.get('/api/genres', moviesController.getGenres);
app.get('/api/stats', moviesController.getStats);
app.post('/api/movie/:netflixId/watched', moviesController.markWatched);

// ===== Scraper Routes =====
app.post('/api/scraper/login', scraperController.loginToNetflix);
app.post('/api/scraper/viewing-activity', scraperController.scrapeViewingActivity);
app.post('/api/scraper/browse', scraperController.scrapeBrowsePage);
app.get('/api/scraper/browse/stream', scraperController.scrapeBrowsePageStream);
app.post('/api/scraper/enrich', scraperController.enrichWithIMDb);
app.get('/api/scraper/enrich/stream', scraperController.enrichWithIMDbStream);
app.post('/api/scraper/full-pipeline', scraperController.runFullPipeline);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Server is running' });
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📊 API endpoints:`);
  console.log(`   - GET  /api/movies`);
  console.log(`   - POST /api/scraper/login`);
  console.log(`   - POST /api/scraper/viewing-activity`);
  console.log(`   - POST /api/scraper/browse`);
  console.log(`   - POST /api/scraper/enrich`);
  console.log(`   - POST /api/scraper/full-pipeline`);
});
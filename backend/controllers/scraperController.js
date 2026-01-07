import { runPythonScript, runPythonScriptStream } from '../utils/pythonRunner.js';
import { loadJSON, saveJSON, mergeMovieData, fileExists } from '../utils/dataManager.js';

export async function loginToNetflix(req, res) {
  try {
    console.log('[Scraper] Starting Netflix login...');
    
    const result = await runPythonScript('login.py');
    
    res.json({
      success: true,
      message: 'Successfully logged in to Netflix',
      output: result.stdout
    });
  } catch (error) {
    console.error('[Scraper] Login failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export async function scrapeViewingActivity(req, res) {
  try {
    console.log('[Scraper] Scraping viewing activity...');
    
    const result = await runPythonScript('scrape_viewing_activity.py');
    
    res.json({
      success: true,
      message: 'Successfully scraped viewing activity',
      output: result.stdout
    });
  } catch (error) {
    console.error('[Scraper] Viewing activity scrape failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export async function scrapeBrowsePage(req, res) {
  try {
    console.log('[Scraper] Starting browse page scrape...');
    
    // Check if we have existing data
    const hasExistingData = await fileExists('netflix-browse-complete.json');
    
    if (hasExistingData) {
      console.log('[Scraper] Found existing data, will merge after scraping');
    }

    // Run the scraper
    const result = await runPythonScript('scrape_browse_complete.py');
    
    // If we have existing enriched data, merge the new scrape with it
    if (hasExistingData) {
      console.log('[Scraper] Merging new data with existing data...');
      
      const existingBrowseData = await loadJSON('netflix-browse-complete.json');
      const newBrowseData = await loadJSON('netflix-browse-complete.json');
      
      // Check if we have enriched data
      const hasEnrichedData = await fileExists('enriched_netflix_complete.json');
      
      if (hasEnrichedData) {
        const enrichedData = await loadJSON('enriched_netflix_complete.json');
        const mergedData = await mergeMovieData(enrichedData, newBrowseData);
        
        // Save merged data
        await saveJSON('enriched_netflix_complete.json', mergedData);
        console.log('[Scraper] Merged with enriched data');
      }
    }
    
    res.json({
      success: true,
      message: 'Successfully scraped browse page',
      output: result.stdout
    });
  } catch (error) {
    console.error('[Scraper] Browse page scrape failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export async function scrapeBrowsePageStream(req, res) {
  try {
    console.log('[Scraper] Starting browse page scrape with streaming...');
    
    // Set headers for streaming
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const process = runPythonScriptStream('scrape_browse_complete.py', [], (data) => {
      // Send data to client as Server-Sent Events
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    });

    process.on('close', (code) => {
      if (code === 0) {
        res.write(`data: ${JSON.stringify({ type: 'done', message: 'Scraping completed' })}\n\n`);
      } else {
        res.write(`data: ${JSON.stringify({ type: 'error', message: 'Scraping failed' })}\n\n`);
      }
      res.end();
    });

    // Handle client disconnect
    req.on('close', () => {
      console.log('[Scraper] Client disconnected, killing process');
      process.kill();
    });

  } catch (error) {
    console.error('[Scraper] Browse page scrape failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export async function enrichWithIMDb(req, res) {
  try {
    console.log('[Enrichment] Starting IMDb enrichment...');
    
    const result = await runPythonScript('enrich_with_imdb.py');
    
    res.json({
      success: true,
      message: 'Successfully enriched with IMDb data',
      output: result.stdout
    });
  } catch (error) {
    console.error('[Enrichment] IMDb enrichment failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export async function enrichWithIMDbStream(req, res) {
  try {
    console.log('[Enrichment] Starting IMDb enrichment with streaming...');
    
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const process = runPythonScriptStream('enrich_with_imdb.py', [], (data) => {
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    });

    process.on('close', (code) => {
      if (code === 0) {
        res.write(`data: ${JSON.stringify({ type: 'done', message: 'Enrichment completed' })}\n\n`);
      } else {
        res.write(`data: ${JSON.stringify({ type: 'error', message: 'Enrichment failed' })}\n\n`);
      }
      res.end();
    });

    req.on('close', () => {
      console.log('[Enrichment] Client disconnected, killing process');
      process.kill();
    });

  } catch (error) {
    console.error('[Enrichment] IMDb enrichment failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

export async function runFullPipeline(req, res) {
  try {
    console.log('[Pipeline] Starting full pipeline...');
    
    const results = {
      login: null,
      viewingActivity: null,
      browseScrape: null,
      enrichment: null
    };

    // Step 1: Login (optional - only if session expired)
    // Uncomment if needed
    // results.login = await runPythonScript('login.py');
    
    // Step 2: Scrape viewing activity
    console.log('[Pipeline] Step 1/3: Scraping viewing activity...');
    results.viewingActivity = await runPythonScript('scrape_viewing_activity.py');
    
    // Step 3: Scrape browse page
    console.log('[Pipeline] Step 2/3: Scraping browse page...');
    results.browseScrape = await runPythonScript('scrape_browse_complete.py');
    
    // Step 4: Enrich with IMDb
    console.log('[Pipeline] Step 3/3: Enriching with IMDb data...');
    results.enrichment = await runPythonScript('enrich_with_imdb.py');
    
    res.json({
      success: true,
      message: 'Full pipeline completed successfully',
      results
    });
  } catch (error) {
    console.error('[Pipeline] Pipeline failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = path.join(__dirname, '../../data');
const INPUT_DIR = path.join(DATA_DIR, 'input');
const OUTPUT_DIR = path.join(DATA_DIR, 'output');

export async function ensureDirectories() {
  await fs.ensureDir(INPUT_DIR);
  await fs.ensureDir(OUTPUT_DIR);
}

export async function loadJSON(filename) {
  const filePath = path.join(OUTPUT_DIR, filename);
  try {
    const data = await fs.readJson(filePath);
    return data;
  } catch (error) {
    console.log(`File ${filename} not found, returning empty array`);
    return [];
  }
}

export async function saveJSON(filename, data) {
  const filePath = path.join(OUTPUT_DIR, filename);
  await fs.writeJson(filePath, data, { spaces: 2 });
}

export async function mergeMovieData(existingData, newData) {
  console.log(`[Merge] Existing movies: ${existingData.length}`);
  console.log(`[Merge] New movies: ${newData.length}`);

  // Create a map of existing movies by netflixId
  const existingMap = new Map();
  existingData.forEach(movie => {
    if (movie.netflixId) {
      existingMap.set(movie.netflixId, movie);
    }
  });

  let addedCount = 0;
  let updatedCount = 0;

  // Process new data
  newData.forEach(newMovie => {
    if (!newMovie.netflixId) {
      console.warn(`[Merge] Skipping movie without netflixId: ${newMovie.title}`);
      return;
    }

    if (existingMap.has(newMovie.netflixId)) {
      // Movie exists - merge categories and preserve watched status
      const existingMovie = existingMap.get(newMovie.netflixId);
      
      // Merge categories (unique values)
      const allCategories = [
        ...(existingMovie.categories || []),
        ...(newMovie.categories || [])
      ];
      const uniqueCategories = [...new Set(allCategories)];

      // Update with new data but preserve certain fields
      existingMap.set(newMovie.netflixId, {
        ...newMovie,
        categories: uniqueCategories,
        watched: existingMovie.watched || false, // Preserve watched status
        // Preserve IMDb data if it exists
        imdb_rating: existingMovie.imdb_rating || newMovie.imdb_rating,
        imdb_id: existingMovie.imdb_id || newMovie.imdb_id,
        year: existingMovie.year || newMovie.year,
        genres: existingMovie.genres || newMovie.genres,
        plot: existingMovie.plot || newMovie.plot,
      });

      updatedCount++;
    } else {
      // New movie - add it
      existingMap.set(newMovie.netflixId, {
        ...newMovie,
        watched: false
      });
      addedCount++;
    }
  });

  const mergedData = Array.from(existingMap.values());

  console.log(`[Merge] Added: ${addedCount}, Updated: ${updatedCount}`);
  console.log(`[Merge] Total after merge: ${mergedData.length}`);

  return mergedData;
}

export async function fileExists(filename) {
  const filePath = path.join(OUTPUT_DIR, filename);
  return fs.pathExists(filePath);
}
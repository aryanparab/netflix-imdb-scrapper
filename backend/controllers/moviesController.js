import { loadJSON, saveJSON } from '../utils/dataManager.js';

function getRatingValue(movie) {
  const rating = movie.imdb_rating;
  if (rating && rating !== 'N/A') {
    try {
      return parseFloat(rating);
    } catch {
      return 0;
    }
  }
  return 0;
}

export async function getMovies(req, res) {
  try {
    const movies = await loadJSON('high_rated_recommendations.json');
    
    const {
      category,
      min_rating = 0,
      max_rating = 10,
      search = '',
      genre,
      watched = 'all'
    } = req.query;

    let filtered = movies;

    if (category && category !== 'all') {
      filtered = filtered.filter(m => 
        m.categories && m.categories.includes(category)
      );
    }

    const minRating = parseFloat(min_rating);
    const maxRating = parseFloat(max_rating);
    filtered = filtered.filter(m => {
      const rating = getRatingValue(m);
      return rating >= minRating && rating <= maxRating;
    });

    if (search) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(m =>
        m.title && m.title.toLowerCase().includes(searchLower)
      );
    }

    if (genre && genre !== 'all') {
      filtered = filtered.filter(m =>
        m.genres && m.genres.toLowerCase().includes(genre.toLowerCase())
      );
    }

    if (watched === 'watched') {
      filtered = filtered.filter(m => m.watched === true);
    } else if (watched === 'unwatched') {
      filtered = filtered.filter(m => m.watched !== true);
    }

    res.json({
      movies: filtered,
      total: filtered.length
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to load movies' });
  }
}

export async function getCategories(req, res) {
  try {
    const movies = await loadJSON('high_rated_recommendations.json');
    const categories = new Set();
    
    movies.forEach(movie => {
      if (movie.categories) {
        movie.categories.forEach(cat => categories.add(cat));
      }
    });

    res.json(Array.from(categories).sort());
  } catch (error) {
    res.status(500).json({ error: 'Failed to load categories' });
  }
}

export async function getGenres(req, res) {
  try {
    const movies = await loadJSON('high_rated_recommendations.json');
    const genres = new Set();
    
    movies.forEach(movie => {
      if (movie.genres && movie.genres !== 'N/A') {
        movie.genres.split(',').forEach(genre => {
          const trimmed = genre.trim();
          if (trimmed) genres.add(trimmed);
        });
      }
    });

    res.json(Array.from(genres).sort());
  } catch (error) {
    res.status(500).json({ error: 'Failed to load genres' });
  }
}

export async function getStats(req, res) {
  try {
    const movies = await loadJSON('high_rated_recommendations.json');
    
    const total = movies.length;
    const watched = movies.filter(m => m.watched === true).length;
    const unwatched = total - watched;

    const ratings = movies
      .map(m => getRatingValue(m))
      .filter(r => r > 0);
    
    const avgRating = ratings.length > 0
      ? ratings.reduce((a, b) => a + b, 0) / ratings.length
      : 0;

    const genreCount = {};
    movies.forEach(movie => {
      if (movie.genres && movie.genres !== 'N/A') {
        movie.genres.split(',').forEach(genre => {
          const trimmed = genre.trim();
          if (trimmed) {
            genreCount[trimmed] = (genreCount[trimmed] || 0) + 1;
          }
        });
      }
    });

    const topGenres = Object.entries(genreCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {});

    res.json({
      total,
      watched,
      unwatched,
      avg_rating: Math.round(avgRating * 10) / 10,
      top_genres: topGenres
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to load stats' });
  }
}

export async function markWatched(req, res) {
  try {
    const { netflixId } = req.params;
    const { watched } = req.body;

    const movies = await loadJSON('high_rated_recommendations.json');
    const movie = movies.find(m => m.netflixId === netflixId);

    if (!movie) {
      return res.status(404).json({ error: 'Movie not found' });
    }

    movie.watched = watched;
    await saveJSON('high_rated_recommendations.json', movies);

    res.json({ success: true, watched });
  } catch (error) {
    res.status(500).json({ error: 'Failed to update movie' });
  }
}
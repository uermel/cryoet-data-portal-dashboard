"""Caching module for the dashboard."""
from flask_caching import Cache

# This cache will be initialized when the app is created
cache = None

def init_cache(server):
    """Initialize the cache with the Flask server instance.
    
    Args:
        server: Flask server instance from the Dash app
        
    Returns:
        The initialized cache object
    """
    global cache
    cache = Cache(server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'cache-directory',
        'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default cache timeout
    })
    return cache 
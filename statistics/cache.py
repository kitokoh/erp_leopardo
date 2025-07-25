from cachetools import TTLCache

# Cache with a 5 minute TTL and a max size of 100 entries
cache = TTLCache(maxsize=100, ttl=300)

import collections
import threading
import time

MAX_CACHE_SIZE = 100
TTL = 86400

class LRUCache:
    def __init__(self, maxsize=MAX_CACHE_SIZE):
        self.cache = collections.OrderedDict()  # Keeps track of the order of insertion/access
        self.maxsize = maxsize
        self.lock = threading.Lock()  # Lock to synchronize access to the cache

    def get(self, key):
        with self.lock:  # Ensure only one thread can access the cache at a time
            if key in self.cache:
                cached_obj = self.cache[key]
                self.cache.move_to_end(key)
                return cached_obj.value  
            return None

    def set(self, key, value, ttl=TTL):
        with self.lock:  
            if key in self.cache:
                # Update the existing item and move it to the end
                self.cache.move_to_end(key)
            else:
                # Insert a new item and check if eviction is needed
                if len(self.cache) >= self.maxsize:
                    # Evict the least recently used (first) item
                    self.cache.popitem(last=False)
            # Store the CachedObject 
            self.cache[key] = CachedObject(value)

class CachedObject:
    def __init__(self, value):
        self.value = value
 

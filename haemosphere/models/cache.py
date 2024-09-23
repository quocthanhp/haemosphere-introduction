import collections
import threading
import time

MAX_CACHE_SIZE = 50
TTL = 86400

import collections
import threading
import time

class LRUCache:
    def __init__(self, maxsize=MAX_CACHE_SIZE):
        self.cache = collections.OrderedDict()  # Keeps track of the order of insertion/access
        self.maxsize = maxsize
        self.lock = threading.Lock()  # Lock to synchronize access to the cache

    def get(self, key):
        with self.lock:  # Ensure only one thread can access the cache at a time
            if key in self.cache:
                cached_obj = self.cache[key]
                # if not cached_obj.is_expired():
                    # Move the accessed key to the end (most recently used)
                self.cache.move_to_end(key)
                return cached_obj.value  
                # else:
                    # If the cached item is expired, remove it from the cache
                    # del self.cache[key]
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
            # Store the CachedObject with the value and TTL
            self.cache[key] = CachedObject(value, ttl)

class CachedObject:
    def __init__(self, value, ttl):
        self.value = value
        # self.expired_at = time.time() + ttl  # Set the expiration time based on TTL

    # def is_expired(self):
    #     # Check if the current time is greater than the expiration time
    #     return time.time() > self.expired_at

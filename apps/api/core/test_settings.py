from .settings import *

# Use an in-memory channel layer for tests to avoid needing a Redis server.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Use a fast, non-hashing password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.UnsaltedMD5PasswordHasher",
]

# Use a local memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Make Celery tasks run synchronously for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

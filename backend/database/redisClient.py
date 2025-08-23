import redis
import os

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

try:
    redis_client.ping()
    print("✅ Connected to Redis")
except redis.exceptions.ConnectionError as e:
    print("❌ Redis connection error:", e)

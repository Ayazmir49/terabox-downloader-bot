import redis

# 🔧 Your Upstash Redis configuration
REDIS_HOST = 'settled-zebra-27081.upstash.io'
REDIS_PORT = 6379
REDIS_PASSWORD = 'AWnJAAIjcDE1MmU5ZjNiYjJjNjk0MzBjOGYxZDkxNjUyNTY0OGI4ZHAxMA'

# ✅ Connect to Redis
db = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    decode_responses=True
)

# ✅ Optional: Test the connection at startup
def check_redis_connection():
    try:
        db.ping()
        print("✅ Connected to Upstash Redis!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

# Call the test function (optional but useful for debugging)
check_redis_connection()

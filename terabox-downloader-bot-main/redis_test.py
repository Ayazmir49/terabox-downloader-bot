import redis

# Test connection
r = redis.StrictRedis(
    host="settled-zebra-27081.upstash.io",
    port=6379,
    password="AWnJAAIjcDE1MmU5ZjNiYjJjNjk0MzBjOGYxZDkxNjUyNTY0OGI4ZHAxMA",
    ssl=True
)

# Test ping
response = r.ping()
print("Redis Ping:", response)

# Test set/get
r.set("test_key", "hello world")
value = r.get("test_key")
print("Redis Value:", value)

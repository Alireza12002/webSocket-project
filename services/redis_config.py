from idna import decode
from redis.asyncio import Redis

redis = Redis(host="127.0.0.1", port=6379, db=0, socket_timeout=None, decode_responses=True)
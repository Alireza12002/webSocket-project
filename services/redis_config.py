from idna import decode
from redis.asyncio import Redis
import os
redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
import asyncio
import json
import os
from dotenv import load_dotenv, find_dotenv
from kafka import KafkaProducer

from lib.networkhandler import OddsAPIHandler

# Load environment variables from .env.local and .env as fallback
load_dotenv(find_dotenv('.env.local'))
load_dotenv(find_dotenv('.env'))

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
SPORT = os.getenv('SPORT', 'baseball_mlb')
REQUEST_LIMIT = int(os.getenv('REQUEST_LIMIT', 500))
FETCH_INTERVAL = float(os.getenv('FETCH_INTERVAL', 5))
TOPIC = 'odds_raw'

async def produce_odds():
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    api = OddsAPIHandler(SPORT)
    requests_made = 0
    while requests_made < REQUEST_LIMIT:
        try:
            odds_data = await asyncio.to_thread(api.fetch_from_api)
            producer.send(TOPIC, json.dumps(odds_data).encode('utf-8'))
            producer.flush()
            requests_made += 1
        except Exception as e:
            print(f"Error fetching or publishing odds: {e}")
        await asyncio.sleep(FETCH_INTERVAL)
    print("Request limit reached, stopping producer")

if __name__ == '__main__':
    asyncio.run(produce_odds())

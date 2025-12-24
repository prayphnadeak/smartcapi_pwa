import redis
import sys

def fix_redis():
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Check connection
        print("Ping Redis...", r.ping())
        
        # proper command to disable the stop-writes-on-bgsave-error
        print("Setting stop-writes-on-bgsave-error to no...")
        r.config_set('stop-writes-on-bgsave-error', 'no')
        
        print("SUCCESS! Redis configuration updated.")
        print("Your workers should recover automatically in a few seconds.")
        
    except Exception as e:
        print(f"Error fixing Redis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_redis()

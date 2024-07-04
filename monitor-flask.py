from flask import Flask, jsonify
import requests
from collections import deque
import threading
import time
import datetime
import logging
import os

logging.getLogger("werkzeug").disabled = True
app = Flask(__name__)

# Get the path to the API list file from the environment variable
API_LIST_PATH = os.getenv('API_LIST_PATH')

# Check if the API list file exists
if API_LIST_PATH and os.path.isfile(API_LIST_PATH):
    with open(API_LIST_PATH, 'r') as file:
        API_URLS = [line.strip() for line in file.readlines() if line.strip()]
else:
    # Default list of APIs to monitor
    API_URLS = [
        "https://thepdahoi.com",
        "https://1921992.xyz",
    ]



# Number of recent checks to store
CHECK_HISTORY_SIZE = 3600

# Dictionary to store check results and last up/down times for each API
api_status = {
    url: {
        'check_results': deque(maxlen=CHECK_HISTORY_SIZE),
        'last_down_time': None,
        'last_up_time': None
    }
    for url in API_URLS
}

status_lock = threading.Lock()

@app.route('/', methods=['GET'])
def monitor_apis():
    results = {}
    for url in API_URLS:
        status = api_status[url]
        if len(status['check_results']) == 0:
            results[url] = {'message': 'No checks performed yet.'}
        else:
            up_count = status['check_results'].count(True)
            down_count = status['check_results'].count(False)
            total_count = len(status['check_results'])
            up_ratio = up_count / total_count
            down_ratio = down_count / total_count

            results[url] = {
                'total_checks': total_count,
                'up_count': up_count,
                'down_count': down_count,
                'up_ratio': up_ratio,
                'down_ratio': down_ratio,
                'last_down_time': status['last_down_time'].strftime("%H:%M:%S %d-%m-%Y") if status['last_down_time'] else None,
                'last_up_time': status['last_up_time'].strftime("%H:%M:%S %d-%m-%Y") if status['last_up_time'] else None
            }
    return jsonify(results)

def check_api(url):
    global api_status
    try:
        response = requests.get(url)
        with status_lock:
            if response.ok:
                api_status[url]['check_results'].append(True)
                api_status[url]['last_up_time'] = datetime.datetime.now()
            else:
                api_status[url]['check_results'].append(False)
                api_status[url]['last_down_time'] = datetime.datetime.now()
                print(f"{datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')} - {url} - Status: Down")
    except requests.exceptions.RequestException:
        with status_lock:
            api_status[url]['check_results'].append(False)
            api_status[url]['last_down_time'] = datetime.datetime.now()
            print(f"{datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')} - {url} - Error")

def periodic_check():
    while True:
        threads = []
        for url in API_URLS:
            thread = threading.Thread(target=check_api, args=(url,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        time.sleep(60)  # Wait for 60 seconds before starting the next cycle

if __name__ == '__main__':
    # Start the periodic check thread
    checker_thread = threading.Thread(target=periodic_check)
    checker_thread.daemon = True
    checker_thread.start()

    app.run(host="0.0.0.0")
    

import requests
import json
import time
import datetime
import os

API_URLS = [
    "http://prometheus2.rke2.local:30080/"
]

LOG_DIR = "api_logs"
CHECK_HISTORY_SIZE = 864000

def send_telegram_message(message):
    token = "5568869659:AAEfOUmEs2-83bL5j4_LB0qFknu11rMgXXX"
    chat_id = "841284XXX"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    return response.json()
    
def load_history(api_name):
    log_file = os.path.join(LOG_DIR, f"{sanitize_filename(api_name)}_history.json")
    try:
        with open(log_file, 'r') as file:
            history = json.load(file)
    except FileNotFoundError:
        history = []
    return history

def save_history(api_name, history):
    log_file = os.path.join(LOG_DIR, f"{sanitize_filename(api_name)}_history.json")
   # print( log_file )    
    with open(log_file, 'w') as file:
        json.dump(history, file)

def sanitize_filename(filename):
    return filename.replace("/", "_").replace("\\", "_").replace("//", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")

def monitor_api(api_url):
    try:
        response = requests.get(api_url)
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()

        api_name = api_url.split("/")[2]

        history = load_history(api_name)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response.ok:
            history.append({'timestamp': timestamp, 'status': 'up', 'status_code': status_code, 'response_time': response_time})
        else:
            send_telegram_message("Down: " + timestamp)
            history.append({'timestamp': timestamp, 'status': 'down', 'status_code': status_code, 'response_time': response_time})

        if len(history) > CHECK_HISTORY_SIZE:
            history = history[-CHECK_HISTORY_SIZE:]

        save_history(api_name, history)

        return True if response.ok else False

    except requests.exceptions.RequestException as e:
        api_name = api_url.split("/")[-1]

        history = load_history(api_name)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append({'timestamp': timestamp, 'status': 'down', 'error': str(e)})

        if len(history) > CHECK_HISTORY_SIZE:
            history = history[-CHECK_HISTORY_SIZE:]

        save_history(api_name, history)

        return False

def periodic_check():
    while True:
        for api_url in API_URLS:
            monitor_api(api_url)
        time.sleep(60)

if __name__ == '__main__':
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    periodic_check()

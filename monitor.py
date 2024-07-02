import requests
import json
import time
import datetime
import os

# Danh sách các API mà bạn muốn giám sát
API_URLS = [
    "http://prometheus2.rke2.local:30080/"
]

# Thư mục lưu trữ log
LOG_DIR = "api_logs"

# Số lượng kiểm tra gần nhất để lưu trữ
CHECK_HISTORY_SIZE = 864000

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
    # Thay thế các ký tự đặc biệt trong tên file
    return filename.replace("/", "_").replace("\\", "_").replace("//", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")

def monitor_api(api_url):
    try:
        response = requests.get(api_url)
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()

        # Lấy tên API từ URL để đặt tên cho file log
        api_name = api_url.split("/")[2]

        # Đọc lịch sử từ file
        history = load_history(api_name)

        # Thêm kết quả mới vào lịch sử
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response.ok:
            history.append({'timestamp': timestamp, 'status': 'up', 'status_code': status_code, 'response_time': response_time})
        else:
            history.append({'timestamp': timestamp, 'status': 'down', 'status_code': status_code, 'response_time': response_time})

        # Giới hạn lịch sử chỉ lưu CHECK_HISTORY_SIZE mục
        if len(history) > CHECK_HISTORY_SIZE:
            history = history[-CHECK_HISTORY_SIZE:]

        # Lưu lịch sử vào file
        save_history(api_name, history)

        return True if response.ok else False

    except requests.exceptions.RequestException as e:
        # Lấy tên API từ URL để đặt tên cho file log
        api_name = api_url.split("/")[-1]

        # Đọc lịch sử từ file
        history = load_history(api_name)

        # Thêm kết quả mới vào lịch sử
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append({'timestamp': timestamp, 'status': 'down', 'error': str(e)})

        # Giới hạn lịch sử chỉ lưu CHECK_HISTORY_SIZE mục
        if len(history) > CHECK_HISTORY_SIZE:
            history = history[-CHECK_HISTORY_SIZE:]

        # Lưu lịch sử vào file
        save_history(api_name, history)

        return False

# Hàm chạy kiểm tra định kỳ
def periodic_check():
    while True:
        for api_url in API_URLS:
            monitor_api(api_url)
        time.sleep(60)  # Kiểm tra mỗi 60 giây

if __name__ == '__main__':
    # Tạo thư mục lưu trữ log nếu chưa tồn tại
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Bắt đầu kiểm tra định kỳ
    periodic_check()
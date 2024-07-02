from flask import Flask, jsonify
import requests
from collections import deque
import threading
import time
import datetime

app = Flask(__name__)

# Địa chỉ của API mà bạn muốn giám sátt
API_URL = "http://prometheus2.rke2.local:30080/"

# Số lượng kiểm tra gần nhất để lưu trữ
CHECK_HISTORY_SIZE = 86400

# Lưu trữ kết quả kiểm tra gần nhất (True: sống, False: chết)
check_results = deque(maxlen=CHECK_HISTORY_SIZE)

# Thời gian down cuối cùng
last_down_time = None

@app.route('/monitor', methods=['GET'])
def monitor_api():
    global last_down_time
    try:
        response = requests.get(API_URL)
        status_code = response.status_code
        response_time = response.elapsed.total_seconds()

        # Kiểm tra xem API có trả về mã trạng thái thành công hay không
        if response.ok:
            check_results.append(True)
            return jsonify({
                'status': 'up',
                'status_code': status_code,
                'response_time': response_time
            })
        else:
            check_results.append(False)
            last_down_time = datetime.datetime.now()
            return jsonify({
                'status': 'down',
                'status_code': status_code,
                'response_time': response_time,
                'last_down_time': last_down_time.strftime("%Y-%m-%d %H:%M:%S")
            }), 500

    except requests.exceptions.RequestException as e:
        check_results.append(False)
        last_down_time = datetime.datetime.now()
        return jsonify({
            'status': 'down',
            'error': str(e),
            'last_down_time': last_down_time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/status', methods=['GET'])
def api_status():
    if len(check_results) == 0:
        return jsonify({
            'message': 'No checks performed yet.'
        })

    up_count = check_results.count(True)
    down_count = check_results.count(False)
    total_count = len(check_results)
    up_ratio = up_count / total_count
    down_ratio = down_count / total_count

    status_response = {
        'total_checks': total_count,
        'up_count': up_count,
        'down_count': down_count,
        'up_ratio': up_ratio,
        'down_ratio': down_ratio
    }

    if last_down_time:
        status_response['last_down_time'] = last_down_time.strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(status_response)

# Chạy kiểm tra định kỳ
def periodic_check():
    global last_down_time
    while True:
        try:
            response = requests.get(API_URL)
            if response.ok:
                check_results.append(True)
            else:
                check_results.append(False)
                last_down_time = datetime.datetime.now()
        except requests.exceptions.RequestException:
            check_results.append(False)
            last_down_time = datetime.datetime.now()
        time.sleep(60)  # Kiểm tra mỗi 60 giây

if __name__ == '__main__':
    # Bắt đầu luồng kiểm tra định kỳ
    checker_thread = threading.Thread(target=periodic_check)
    checker_thread.daemon = True
    checker_thread.start()

    app.run(debug=True)
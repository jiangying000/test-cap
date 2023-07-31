from flask import Flask, request, jsonify
import threading
from queue import Queue

from main import _cross_encode

app = Flask(__name__)

API_KEY = "3bb1d1eb6c1bc3f5bf3e694f69bf1c76"  # Replace with your own API key
MAX_CONCURRENCY = 20

semaphore = threading.Semaphore(MAX_CONCURRENCY)

def process_request(q):
    with semaphore:
        item = q.get()
        _cross_encode(query=item['query'], texts=item['texts'])
        q.task_done()
@app.route('/process', methods=['POST'])
def process():
    api_key = request.headers.get('x-api-key')
    if api_key is None or api_key != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401

    query = request.json.get('query')
    texts = request.json.get('texts')

    if query is None or texts is None:
        return jsonify({'error': 'Missing query or texts parameters'}), 400

    q = Queue()
    q.put({'query': query, 'texts': texts})
    t = threading.Thread(target=process_request, args=(q,))
    t.start()

    return jsonify({'status': 'processing'}), 202


if __name__ == '__main__':
    app.run(debug=True, port=5000)

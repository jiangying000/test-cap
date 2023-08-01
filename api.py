from flask import Flask, Response, request, jsonify
import json
import threading
from queue import Queue

import numpy as np

from main import compute_similarity

# def convert_float32(response):
#     return {
#         key: self.encode_float32(value) for key, value in response.items()
#     }

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.float32):
            return float(obj)
        return super(CustomJSONEncoder, self).default(obj)

def validate_request(api_key, query, passages):
    if api_key is None or api_key != API_KEY:
        return False, jsonify({'error': 'Invalid API key'}), 401

    if query is None or passages is None:
        return False, jsonify({'error': 'Missing query or passages parameters'}), 400

    if not isinstance(query, str):
        return False, jsonify({'error': 'query must be a string'}), 400

    if not isinstance(passages, list) or not all(isinstance(text, str) for text in passages):
        return False, jsonify({'error': 'passages must be a list of strings'}), 400

    return True, None, None

def convert_float32(data):
    if isinstance(data, dict):
        return {k: convert_float32(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_float32(v) for v in data]
    elif isinstance(data, np.float32):
        return float(data)
    else:
        return data


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder


API_KEY = "ce-3bb1d1eb6c1bc3f5bf3e694f69bf1c76"  # Replace with your own API key
MAX_CONCURRENCY = 20

semaphore = threading.Semaphore(MAX_CONCURRENCY)

def process_request(q):
    with semaphore:
        item = q.get()
        _cross_encode(query=item['query'], texts=item['passages'])
        q.task_done()

@app.route('/cross-encode', methods=['POST'])
def process():
    api_key = request.headers.get('x-api-key')
    if api_key is None or api_key != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401

    query = request.json.get('query')
    passages = request.json.get('passages')

    if query is None or passages is None:
        return jsonify({'error': 'Missing query or passages parameters'}), 400

    if not isinstance(query, str):
        return jsonify({'error': 'query must be a string'}), 400

    if not isinstance(passages, list) or not all(isinstance(text, str) for text in passages):
        return jsonify({'error': 'passages must be a list of strings'}), 400

    # q = Queue()
    # q.put({'query': query, 'passages': passages})
    # t = threading.Thread(target=process_request, args=(q,))
    # t.start()
    # response = _cross_encode(query=query, texts=passages)
    response = compute_similarity(query=query, passages=passages)
    converted_response = convert_float32(response)

    # return jsonify(converted_response), 200
        # Serialize data using json.dumps()
    serialized_data = json.dumps(converted_response, cls=CustomJSONEncoder)

    # Return the serialized data using the Response class
    return Response(serialized_data, content_type="application/json", status=200)
    # return jsonify({'status': 'processing'}), 202

# @app.after_request
# def ensure_float32_serializability(response):
#     if response.content_type == "application/json":
#         data = json.loads(response.get_data())
#         custom_encoder = CustomJSONEncoder()
#         modified_data = custom_encoder.encode(data)
#         response.set_data(modified_data)
#     return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)

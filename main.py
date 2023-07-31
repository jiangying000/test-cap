from sentence_transformers import CrossEncoder

import torch

gpu = torch.cuda.is_available()
print("Is GPU available: ", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU Device Name: ", torch.cuda.get_device_name())
    cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1', device='cuda')
else:
    cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')


def timeit(f):
    t = time.time()
    res = f()
    print('t', time.time() - t)
    return res


def predict(timing=True):
    if timing:
        scores = timeit(
            lambda: cross_encoder.predict([['Query', 'Paragraph1'], ['Query', 'Paragraph2'], ['Query', 'Paragraph3']]))
    else:
        scores = cross_encoder.predict([['Query', 'Paragraph1'], ['Query', 'Paragraph2'], ['Query', 'Paragraph3']])
    print('score', scores)


def _cross_encode(query, texts, cross_encoder=cross_encoder):
    time2 = time.time()
    # if len(bm25_hits) > 0:
    scores = cross_encoder.predict([[query, text] for text in texts])
    print('t311 cross_encoder takes', time.time() - time2)

    result = [(item1, index, item2) for index, (item1, item2) in enumerate(zip(scores, texts), start=0)]
    sorted_result = sorted(result, key=lambda x: -x[0])
    final_result = [(item1, i, index, item2) for i, (item1, index, item2) in enumerate(sorted_result, start=0)]
    return final_result


query = "S4210-8GE2XF-I-AC 電源 電圧 範囲"
from texts import texts

# texts = texts[:10]

# len texts 30 46792
# t311 cross_encoder 15.972991943359375

print('len texts', len(texts), sum(len(s) for s in texts))
# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     # predict(timing=True)
#     _cross_encode(query=query, texts=texts)

import threading
from queue import Queue
import time

total_queries = 128
if gpu:
    from py3nvml.py3nvml import *
    nvmlInit()
    device_count = nvmlDeviceGetCount()

# Initialize GPU library and discover the number of GPUs

# Function to report GPU usage
def report_gpu_usage():
    print("GPU usage statistics:")
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        info = nvmlDeviceGetMemoryInfo(handle)
        util = nvmlDeviceGetUtilizationRates(handle)
        print(f"GPU {i} - Load: {util.gpu}% | Memory used: {info.used / (1024**2)} MB | Memory total: {info.total / (1024**2)} MB")


def process_batch(q, latencies):
    while not q.empty():
        item = q.get()
        start_time = time.time()
        _cross_encode(query=item['query'], texts=item['texts'])
        end_time = time.time()
        latency = end_time - start_time
        latencies.append(latency)
        q.task_done()
        # Adding code to track GPU usage
        # report_gpu_usage()


# Create a list of queries to be processed
query_list = [{"query": query, "texts": texts} for _ in range(total_queries)]

# Benchmark for different concurrency levels, 500m gpu mem per request
for num_threads in [1, 2, 4, 8, 16, 32]:
    # Put all queries in a queue
    q = Queue()
    for item in query_list:
        q.put(item)

    start_time = time.time()

    # Create threads to process the queries
    threads = []
    latencies = []
    for _ in range(num_threads):
        t = threading.Thread(target=process_batch, args=(q, latencies))
        t.start()
        threads.append(t)

    # Join the threads to wait for all of them to finish
    for t in threads:
        t.join()

    end_time = time.time()

    # Calculate latency and throughput
    total_time = end_time - start_time
    avg_latency = sum(latencies) / len(latencies)
    throughput = total_queries / total_time

    # Print GPU usage after each wrap-up
    if gpu:
        report_gpu_usage()
    print(f"Concurrency Level: {num_threads}, Avg. Latency: {avg_latency:.3f}s, Throughput: {throughput:.3f} queries/s\n")

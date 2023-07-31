from sentence_transformers import CrossEncoder

import torch

print("Is GPU available: ", torch.cuda.is_available())
print("GPU Device Name: ", torch.cuda.get_device_name())

if torch.cuda.is_available():
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
    # print('t311 cross_encoder', time.time() - time2)

    result = [(item1, index, item2) for index, (item1, item2) in enumerate(zip(scores, texts), start=0)]
    sorted_result = sorted(result, key=lambda x: -x[0])
    final_result = [(item1, i, index, item2) for i, (item1, index, item2) in enumerate(sorted_result, start=0)]
    return final_result


query = "S4210-8GE2XF-I-AC 電源 電圧 範囲"
from texts import texts

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

total_queries = 2048


# Define a function to process a batch of inputs
def process_batch(q):
    # while not q.empty():
    #     item = q.get()
    #     _cross_encode(query=item['query'], texts=item['texts'])
    #     q.task_done()
    while not q.empty():
        item = q.get()
        _cross_encode(query=item['query'], texts=item['texts'])
        q.task_done()

        # Adding code to track GPU usage
        stats = gpustat.GPUStatCollection.new_query()
        for gpu in stats:
            print(f"GPU {gpu.index} - Load: {gpu.load}% | Memory used: {gpu.memory_used} MB | Memory total: {gpu.memory_total} MB")



# Create a list of queries to be processed
query_list = [{"query": query, "texts": texts} for _ in range(total_queries)]

# Benchmark for different concurrency levels
for num_threads in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]:
    # Put all queries in a queue
    q = Queue()
    for item in query_list:
        q.put(item)

    start_time = time.time()

    # Create threads to process the queries
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=process_batch, args=(q,))
        t.start()
        threads.append(t)

    # Join the threads to wait for all of them to finish
    for t in threads:
        t.join()

    end_time = time.time()

    # Calculate latency and throughput
    total_time = end_time - start_time
    latency = total_time / total_queries
    throughput = total_queries / total_time

    # Print GPU usage after each wrap-up
    print("GPU usage statistics:")
    stats = gpustat.GPUStatCollection.new_query()
    for gpu in stats:
        print(f"GPU {gpu.index} - Load: {gpu.load}% | Memory used: {gpu.memory_used} MB | Memory total: {gpu.memory_total} MB")

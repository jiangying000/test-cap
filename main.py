import time

from sentence_transformers import CrossEncoder

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
    print('t311 cross_encoder', time.time() - time2)

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
if __name__ == '__main__':
    # predict(timing=True)
    _cross_encode(query=query, texts=texts)

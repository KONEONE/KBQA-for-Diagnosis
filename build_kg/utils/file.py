import os
import json

# 打印数据
def print_data_info(data_path):
    triples = []
    i = 0
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            data = json.loads(line)
            print(json.dumps(data, sort_keys=True, indent=4, separators=(', ', ': '), ensure_ascii=False))
            i += 1
            if i >= 5:
                break
    return triples

from tqdm import tqdm

import spider
from spider import save_pic

with open('pic_download_fail.txt', 'r') as f:
    data = f.readlines()
    for line in tqdm(data):
        line = line.strip()
        print(line)
        if line == '':
            print("continue")
            continue
        else:
            line_values = line.split(",")
            save_pic(line_values[0], line_values[1], line_values[2], line_values[3].replace(spider.FILE_PATH,''))
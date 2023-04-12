import os
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import pandas as pd
from tqdm import tqdm

from db.db import sql_execute, close_conn
from db.sqls import *

HOST = "https://meirentu.top"
FILE_PATH = "D:/MEITU/"


# 获取html内容
def get_one_page(url, is_file=False, referer=''):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
               'Referer': referer}
    try:
        response = requests.get(url, headers=headers)
        if (response.status_code == 200):
            return response.content if is_file else response.text
        else:
            return None
    except RequestException:
        return None


# 下载图片
def save_pic(url, referer, file_name, file_path):
    try:
        file_path = FILE_PATH + file_path
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            print(f'文件夹新建成功：{file_path}')

        pic = get_one_page(url, True, referer)

        with open(f'{file_path}/{file_name}', "wb") as f:
            f.write(pic)
            print(f"图片保存成功：{file_name}")
    except Exception as e:
        print(f"图片保存失败！！！！：{file_name}。", e)
        with open("pic_download_fail.txt", 'a+') as f:
            f.write(f'{url},{referer},{file_name},{file_path}\n')


global index_item, index_item_total
index_item = 0
index_item_total = 0

def print_log(text):
    global index_item, index_item_total
    print(pd.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), f'{index_item}/{index_item_total}', f'---------------- {text} ----------------')


# 解析index列表页面
def parse_index_page(page=1):
    global index_item, index_item_total

    url = HOST + f'/index/{page}.html'
    print_log(f"正在爬取第{page}页：{url}")
    html = get_one_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('.update_area .list_n2')
    index_item_total = len(items)
    for index, item in enumerate(items):
        # continue
        index_item  = index + 1
        info_link = item.select('a')[0].attrs.get('href')
        page_id = info_link.split('/')[-1].split(".")[0]

        # 判断数据库是否存在该写真
        if already_photo(page_id):
            print_log("跳过爬取~")
        else:
            # 保存封面图
            cover_pic = item.select('img')[0].attrs.get('src')
            save_pic(cover_pic, referer=url, file_name=f'0.{cover_pic.split(".")[-1]}', file_path=page_id)
            # 解析内容页
            parse_one_pic_info_page(HOST + info_link, index_page=page, page_id=page_id)

    next_page = soup.select('.update_area .page a')[-1].get_text()
    if next_page == '下页':
        print_log("存在下一页，继续爬取~")
        return page + 1
    return -1


# 解析美图info页面
def parse_one_pic_info_page(info_url, index_page, page_id=None, pic_index=1):
    """
    :param info_url: 详情页url，例如：https://meirentu.top/pic/114965040614.html
    :param page_id: 页面id：114965040614
    :param pic_index: 图片索引
    :return:
    """
    # if page_id is None:
    #     page_id = info_url.split('/')[-1].split(".")[0]
    html = get_one_page(info_url)
    soup = BeautifulSoup(html, 'html.parser')

    # 下载图片
    pic_items = soup.select('.content .content_left img')
    for item in pic_items:
        pic_link = item.attrs.get('src')
        save_pic(pic_link, referer=info_url, file_name=f'{pic_index}.{pic_link.split(".")[-1]}', file_path=page_id)
        pic_index += 1
        print(pic_link)

    # 检查页码信息
    pages = soup.select('.content .content_left a')
    next_page = pages[-1]
    if next_page.get_text() == '下页':
        next_page_link = HOST + next_page.attrs.get('href')
        print_log(f"存在下一页，继续~ index_page:{index_page}, info_pages:{pages[-2].get_text()}, {next_page_link}")
        # 继续访问下一页
        parse_one_pic_info_page(next_page_link, index_page, page_id, pic_index)
    else:
        print("没有下一页了~ 保存数据进数据库")

        # ----------------解析模特信息----------------
        title = soup.select('.main_inner .item_title h1')[0].get_text()
        source = soup.select('.main_inner .single-cat a')[-1].get_text()
        infos = soup.select('.main_inner article p')
        introduction = '-'
        name, birthday, figure, job, address, interest, description = '-', '-', '-', '-', '-', '-', '-'
        for i, info in enumerate(infos):
            info = info.get_text()
            if i == 0:
                if "。。" in info:
                    description = info.split("。。")[0] + "。"
                    introduction = info.split("。。")[1]
                else:
                    description = info
                continue
            if "生 日： " in info:
                birthday = info.replace('生 日： ', '')
                continue
            if "三 围： " in info:
                figure = info.replace('三 围： ', '')
                continue
            if "职 业： " in info:
                job = info.replace('职 业： ', '')
                continue
            if "出 生： " in info:
                address = info.replace('出 生： ', '')
                continue
            if "兴 趣： " in info:
                interest = info.replace('兴 趣： ', '')
                continue

        date = soup.select('.main_inner .item_info span')[1].get_text()
        tag_items = soup.select('.main_inner .item_info a')
        tags = ''
        for i, tag in enumerate(tag_items):
            tag = tag.get_text()
            if i == 0:
                # model's name
                name = tag
                continue
            else:
                if "/" + tag + '/' not in tags + '/':
                    tags += "/" + tag
        tags += '/'
        # ----------------模特信息解析完毕----------------

        model_id = get_model_id(name, birthday, figure, job, address, interest, introduction)
        folder = page_id
        count = pic_index - 1
        add_photo(model_id, title, description, folder, count, source, date, tags)
        print("\n================== 一组数据ok", title, folder, count, '==================\n')


# 获取模特id -> mysql
def get_model_id(name, birthday, figure, job, address, interest, introduction):
    loop = 0
    while loop < 3:
        result = sql_execute(get_model(name))
        if len(result) == 0:
            print("# Model不存在，进行添加~")
        else:
            return result[0][0]
        result = sql_execute(insert_model(name, birthday, figure, job, address, interest, introduction))
        if result == "()":
            print("√ model add success. ", name)
            # 断开连接，避免获取不到数据更新
            # close_conn()
            # return get_model_id(name, birthday, figure, job, address, interest, introduction)
        loop += 1
    print("!!!!!!!!!!!!!!!! model add fail!!!!!!!!!!!!!!!")


# 检查写真是否存在
def already_photo(folder):
    result = sql_execute(get_photo(folder))
    if len(result) > 0:
        print("# Photo已存在", folder)
        return True
    return False


# 添加写真 -> mysql
def add_photo(model_id, title, description, folder, count, source, date, tags):
    if already_photo(folder):
        return
    result = sql_execute(insert_photo(model_id, title, description, folder, count, source, date, tags))
    if result == "()":
        print("√ photo add success. ", title)


# def main():
#     parse_one_pic_info_page('https://meirentu.top/pic/337118595735.html')
#     return
#     url = 'https://meirentu.top/index/1.html'
#     html = get_one_page(url)
#     print(parse_one_page(html))
#
#     parse_one_pic_info_page(get_one_page(HOST + '/pic/114965040614.html'), '', 0)
#
#     return
#     urls = []
#     index = 1
#     for url in parse_one_page(html):
#         html = get_one_page(host + url)
#         hospitals, index = parse_one_hospital_page(html, hospitals, index)
#         print(index)
#
#     write_one_page(hospitals)


if __name__ == '__main__':
    start_page = 31
    end_page = 33
    while (start_page > 0 and start_page < end_page):
        try:
            start_page = parse_index_page(start_page)
        except Exception as e:
            print(start_page, e)
            print_log('报错了，休息10s')
            print_log('报错了，休息10s')
            print_log('报错了，休息10s')
            sleep(10)

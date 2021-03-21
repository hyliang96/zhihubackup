import requests
import json
import os
import re
from tqdm import tqdm

def act_api(username):
    return "https://www.zhihu.com/api/v3/moments/%s/activities?desktop=true" % username

def get_json(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75",
        "x-api-version": "3.0.91",
    }
    r = requests.get(url, headers=headers)
    return json.loads(r.text)

def makedirs(username, target_type):
    try:
        os.makedirs(os.path.join(username, target_type))
    except OSError:
        pass

def loop(username):
    api = read_record()
    if api is None:
        api = act_api(username)
    t = tqdm()
    while True:
        save_record(api)
        jdata = get_json(api)
        # data: ['target', 'action_text', 'is_sticky', 'actor', 'verb', 'created_time', 'type', 'id']
        for dd in jdata['data']:
            target = dd['target']
            if 'author' not in target or target["author"]["url_token"] != username:
                # skip others' content
                continue
            target_type = target['type']
            makedirs(username, target_type)
            saved = []
            if 'question' in target and 'title' in target['question']:
                saved.append(target['question']['title'])
            for saved_type in ('title', 'content', 'updated_time'):
                if saved_type in target:
                    if type(target[saved_type]) is not list:
                        raw = str(target[saved_type])
                        if saved_type == 'content':
                            # 显示图片
                            raw = show_img(raw)
                        saved.append(raw)
                    else:
                        for tt in target[saved_type]:
                            for saved_type2 in ('content', 'url'):
                                if saved_type2 in tt:
                                    saved.append(tt[saved_type2])
            # 文件名带标题
            if target_type == 'pin':
                title = ''
            elif target_type == 'answer':
                title = target['question']['title']
            else:
                title = target['title']
            title = '-' + validate_title(title) if title != '' else ''
            with open(os.path.join(username, target_type, "%s%s.html" % (target['id'], title)), 'w', encoding='utf-8') as f:
                f.write('\n'.join(saved))
            t.update(1)
        # paging: is_end next previous
        paging = jdata['paging']
        if paging['is_end']:
            break
        api = paging['next']

def save_record(current_api, record_file='record'):
    with open(record_file, 'w') as f:
        f.write(current_api)

def read_record(record_file='record'):
    if os.path.isfile(record_file):
        with open(record_file) as f:
            return f.read().strip()
    else:
        return None

def validate_title(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title

def show_img(raw):
    pattern = re.compile(r'(?<=</noscript>).*?(?=</figure>)')
    raw = pattern.sub('', raw)
    pattern = re.compile(r'</*noscript>')
    raw = pattern.sub('', raw)
    return raw

import os
import requests
import sqlite3
import time
import threading
from concurrent.futures import ThreadPoolExecutor

Id_list = []
lock = threading.Lock()

headers = {
    "Cookie":"xxx",   # 此处填入cookie
}

def get_conclusion(page):
    url = f"https://client.vpn.nuist.edu.cn/https/webvpn893ff9021738b0357186c0f23fc2aed6e24ca283e886022bc5d861ea12f03963/v1/problem/digest-partial?page={page}&tags=&todo=&enlink-vpn"
    resp = requests.get(url=url,headers=headers,timeout=3)
    content = resp.json()[0]
    resp.close()
    with open("conclusion.txt","a") as f:
        for each_subject in content:
            id = each_subject['id']
            submits = each_subject['submits']
            accepts = each_subject['accepts']
            prefix = each_subject['prefix']
            logicId = each_subject['logicId']
            userProblemStatus = each_subject['userProblemStatus']
            title = each_subject['title']
            if title.find('"') != -1:
                title = title.replace('"','\'')
            f.write(f'{logicId},{title},{submits},{accepts},{userProblemStatus},{id}\n')
            
            lock.acquire()
            Id_list.append({
                "Id":id,
                "submits":submits,
                "accepts":accepts,
                "logicId":logicId,
                "prefix":prefix,
                "userProblemStatus":userProblemStatus,
                "title":title
            })
            lock.release()

    print(f"Page {page} over!")
    time.sleep(1)

def get_details(logicId,prefix):
    url = f"https://client.vpn.nuist.edu.cn/https/webvpn893ff9021738b0357186c0f23fc2aed6e24ca283e886022bc5d861ea12f03963/v1/problem/logic?prefix={prefix}&logicId={logicId}&enlink-vpn"
    resp = requests.get(url=url,headers=headers,timeout=5)
    content = resp.json()['content']

    with open(f'details/{logicId}.md',"w") as f:
        f.write('API: '+url+'\n\n'+content)
        print(f"\033[32m[+] File 'details/{logicId}.md' save over!\033[01m")
    resp.close()
    time.sleep(1)

def save_to_db():
    print("Saving to database......")
    conn = sqlite3.connect("sub.db")
    cursor = conn.cursor()
    try:
        cursor.execute('DROP TABLE sub')
    except:
        print("\033[31m[!] Table 'sub' not exists!\033[01m\n")
    cursor.execute('''CREATE TABLE sub(
        id INT,
        logicId INT,
        submits INT,
        accepts INT,
        title TEXT,
        userProblemStatus INT,
        prefix TEXT
    );''')
    for each in Id_list:
        id = each['Id']
        logicId = each['logicId']
        submits = each['submits']
        accepts = each['accepts']
        title = each['title']
        userProblemStatus = each['userProblemStatus']
        prefix = each['prefix']
        sql = f'''INSERT INTO sub values({id},{logicId},{submits},{accepts},"{title}",{userProblemStatus},'{prefix}');'''
        try:
            cursor.execute(sql)
            conn.commit()
        except:
            continue

    conn.close()
    print("Over!")

def main():
    try:
        os.remove("conclusion.txt")
    except:
        print("\033[31m[!] File 'conclusion.txt' not exists!\033[01m")
    with ThreadPoolExecutor(50) as t:
        for i in range(1,336):
            t.submit(get_conclusion,page=i)

    try:
        os.mkdir("details")
    except:
        print("\033[31m[!] Directory 'details' exists!\033[01m")
    with ThreadPoolExecutor(50) as t:
        for each in Id_list:
            t.submit(get_details,logicId=each['logicId'],prefix=each['prefix'])
    
    save_to_db()

    
if __name__=="__main__":
    main()

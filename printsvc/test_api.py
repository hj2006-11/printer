import urllib.request
import json
import time

BASE = 'http://127.0.0.1:18210'

def submit(payload):
    req = urllib.request.Request(
        f'{BASE}/submit',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

def status(tid):
    resp = urllib.request.urlopen(f'{BASE}/status?id={tid}')
    return json.loads(resp.read().decode())

# 测试1：气球小票
t1 = submit({'type': 'ticket', 'team': 'Team A', 'problem': 'A', 'pass_time': '2026-08-20 10:23:45'})
print('Ticket submit:', t1)

# 测试2：代码打印
src = '#include <bits/stdc++.h>\nusing namespace std;\n// 中文注释测试\nint main() {\n    cout << "Hello" << endl;\n    return 0;\n}'
t2 = submit({'type': 'code', 'lang': 'cpp', 'source': src})
print('Code submit:', t2)

# 轮询两个任务（最多40秒）
for i in range(40):
    time.sleep(1)
    s1 = status(t1['task_id'])
    s2 = status(t2['task_id'])
    print(f'T{i+1}: ticket={s1["status"]} code={s2["status"]}')
    if s1['status'] in ('completed','failed') and s2['status'] in ('completed','failed'):
        print('All done!')
        print('Ticket output:', s1.get('output_path'))
        print('Code output:', s2.get('output_path'))
        break

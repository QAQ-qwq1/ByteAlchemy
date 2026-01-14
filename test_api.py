import requests
import json
import time

BASE_URL = "http://127.0.0.1:3337"
API_URL = f"{BASE_URL}/api/format"

def test_format(name, type_fmt, data):
    print(f"Testing {name} ({type_fmt})...")
    payload = {"data": data, "type": type_fmt}
    try:
        resp = requests.post(API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            print(f"  [OK] Result:\n{resp.json()['result'][:50]}...")
        else:
            print(f"  [FAIL] {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  [ERR] {e}")

def test():
    print("Waiting for server...")
    time.sleep(2)
    
    test_format("JSON", "json", '{"a":1}')
    test_format("XML", "xml", '<root><a>1</a></root>')
    test_format("SQL", "sql", 'select * from table')
    test_format("HTML", "html", '<div><span>hi</span></div>')
    test_format("CSS", "css", 'body{color:red}')
    test_format("Python", "python", 'def foo(): pass')

if __name__ == "__main__":
    
    test()

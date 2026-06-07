import urllib.request, json
req = urllib.request.Request('http://localhost:8000/predict', 
                             data=json.dumps({'sequence': [[0.0]*1662]*30}).encode('utf-8'), 
                             headers={'Content-Type': 'application/json'})
try:
    res = urllib.request.urlopen(req)
    print(res.read())
except Exception as e:
    print(e.read())

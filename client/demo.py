from client import report_instance_down

url = "http://localhost:8000/api/create_event/"
token = "15d42acb2fa8eec1bb43fd0a2c8a473d7f065879"
region_name = "cn-north-1"
instance_id = "i-00000000000000000"

resp = report_instance_down(url, token, region_name, instance_id, source='demo')
if resp.status_code == 200:
    print("Success.")
else:
    print("Failure.")
    
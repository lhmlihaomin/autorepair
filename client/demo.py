from client import report_instance_down

url = "http://localhost:20000/api/create_event/"
#token = "15d42acb2fa8eec1bb43fd0a2c8a473d7f065879"
token = "229ee70b0930983d36f4e00ce81a8fb97a530378"
#region_name = "cn-north-1"
region_name = "eu-west-1"
instance_id = "i-0939eecfbe55ef289"

resp = report_instance_down(url, token, region_name, instance_id, source='test')
if resp.status_code == 200:
    print("Success.")
else:
    print("Failure.")
    

import requests

def report_instance_down(url, token, region_name, instance_id, source='api'):
    """
    Report to AutoRepair about instance down.
    Params:
        url: str, AutoRepair URL to create a new event;
        token: str, API auth token;
        region_name: str, name of region;
        instance_id: str, EC2 instance id;
        source: str, which system created this event;
    Returns:
        resp: requests Response. Success if resp.status_code is 200.
    """
    # Post data:
    data = {
        "source": source,
        "resource_type": "ec2",
        "event_type": "instance-stop",
        "resource_id": instance_id,
        "detail": "none",
        "region_name": region_name,
    }
    # Set up API credentials:
    s = requests.Session()
    s.headers.update({
        "Authorization": "Token "+token
    })
    
    try:
        resp = s.post(url, data)
    except Exception as ex:
        print ex
        raise ex
        
    return resp

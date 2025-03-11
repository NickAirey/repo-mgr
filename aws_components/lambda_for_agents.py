import json
import urllib3

API_BASE_URL = 'http://URL:PORT/'

def get_file(file_name):
    http = urllib3.PoolManager()

    # Retrieves the content of a file from an external API given its name
    payload = json.dumps({"file": file_name})
    headers = {"Content-Type": "application/json"}
    print(payload)
    response = http.request("GET", API_BASE_URL+"code", body=payload, headers=headers)
    
    if response.status == 200:
        return response.data.decode("utf-8")
    else:
        return None

def get_all_files():
    http = urllib3.PoolManager()

    # Retrieves the content of a file from an external API given its name
    headers = {"Content-Type": "application/json"}
    response = http.request("GET", API_BASE_URL+"list", headers=headers)
    print(response.data)

    if response.status == 200:
        return response.data.decode("utf-8")
    else:
        return None

def put_file(file_name, content):
    http = urllib3.PoolManager()

    # Writes content to a specified file using an external API
    payload = json.dumps({"contents":content})
    headers = {"Content-Type": "application/json"}
    print(payload)

    response = http.request("POST", API_BASE_URL + "code", body=payload, headers=headers)

    return response.status == 200


def lambda_handler(event, context):
    print(event)
    
    file_name = next((p["value"] for p in event['parameters'] if p['name'] == 'file_name'), None)
    event_type = next((p["value"] for p in event['parameters'] if p['name'] == 'type'), None)

    if event_type == 'get':
        file_content = get_file(file_name)
        responseBody = {
            "TEXT": {
                "body": file_content if file_content else "File not found"
            }
        }
    elif event_type == 'post':
        file_content = next((p["value"] for p in event['parameters'] if p['name'] == 'content'), None)
        success = put_file(file_name, file_content)
        responseBody = {
            "TEXT": {
                "body": 'File written successfully!' if success else 'Failed to write file'
            }
        }
    elif event_type == 'getall':
       responseBody = {
            "TEXT": {
                "body": get_all_files()
            }
        }

    action_response = {
        'actionGroup': event['actionGroup'],
        'function': event['function'],
        'functionResponse': {
            'responseBody': responseBody
        }
    }

    lambda_response = {
        'response': action_response,
        'messageVersion': event['messageVersion']
    }

    return lambda_response

import json

def get_formatted_json(message, time = None):
    res = {}
    if message:
        res["message"] = message
    if time:
        res["time_taken_by_previous_step"] = time
    return json.dumps(res)
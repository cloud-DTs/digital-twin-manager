import json
import requests

def lambda_handler(event, context):
    # Example: event may contain entityId, componentName, propertyName, etc.
    api_url = "https://your-http-api.example.com/data"

    try:
        resp = requests.get(api_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        # Build TwinMaker response (customize per your schema)
        return {
            "value": data.get("desired_value"),
            "timestamp": data.get("timestamp"),
            # Include other required elements per TwinMaker's spec
        }
    except Exception as e:
        return {
            "error": str(e)
        }

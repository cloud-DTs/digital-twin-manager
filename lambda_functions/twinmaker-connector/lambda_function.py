import json
from datetime import datetime, timezone

def lambda_handler(event, context):
    # Example: event may contain entityId, componentName, propertyName, etc.
    # api_url = "https://your-http-api.example.com/data"

    # try:
    #     resp = requests.get(api_url, timeout=5)
    #     resp.raise_for_status()
    #     data = resp.json()

    #     # Build TwinMaker response (customize per your schema)
    #     return {
    #         "value": data.get("desired_value"),
    #         "timestamp": data.get("timestamp"),
    #         # Include other required elements per TwinMaker's spec
    #     }
    # except Exception as e:
    #     return {
    #         "error": str(e)
    #     }


    """
    TwinMaker connector Lambda for time-series properties.

    Event example:
    {
        "workspaceId": "MyWorkspace",
        "entityId": "MyEntity",
        "componentName": "TelemetryData",
        "selectedProperties": ["Temperature"],
        "startTime": "2022-08-25T00:00:00Z",
        "endTime": "2022-08-25T00:00:05Z",
        "maxResults": 3,
        "orderByTime": "ASCENDING",
        "properties": {
            "telemetryType": {
                "definition": {
                    "dataType": { "type": "STRING" },
                    "isExternalId": false,
                    "isFinal": false,
                    "isImported": false,
                    "isInherited": false,
                    "isRequiredInEntity": false,
                    "isStoredExternally": false,
                    "isTimeSeries": false
                },
                "value": {
                    "stringValue": "Mixer"
                }
            },
            "telemetryId": {
                "definition": {
                    "dataType": { "type": "STRING" },
                    "isExternalId": true,
                    "isFinal": true,
                    "isImported": false,
                    "isInherited": false,
                    "isRequiredInEntity": true,
                    "isStoredExternally": false,
                    "isTimeSeries": false
                },
                "value": {
                    "stringValue": "item_A001"
                }
            },
            "Temperature": {
                "definition": {
                    "dataType": { "type": "DOUBLE", },
                    "isExternalId": false,
                    "isFinal": false,
                    "isImported": true,
                    "isInherited": false,
                    "isRequiredInEntity": false,
                    "isStoredExternally": false,
                    "isTimeSeries": true
                }
            }
        }
    }
    """

    print("Hello from twinmaker connector!")

    return {
        # "propertyValues": [
        #     {
        #         "time": "2025-08-22T19:03:18+00:00",
        #         "value": {"doubleValue": 11.1}
        #     }
        # ]

        "propertyValues": [
            {
                "entityPropertyReference": {
                    # "entityId": "MyEntity",
                    # "componentName": "TelemetryData",
                    "propertyName": "density"
                },
                "values": [
                    {
                        "time": "2025-08-22T19:01:18+00:00",
                        "value": {
                            "doubleValue": 111.1
                        }
                    },
                    {
                        "time": "2025-08-22T19:02:18+00:00",
                        "value": {
                            "doubleValue": 222.2
                        }
                    },
                    {
                        "time": "2025-08-22T19:03:18+00:00",
                        "value": {
                            "doubleValue": 333.3
                        }
                    }
                ]
            }
        ],
    }

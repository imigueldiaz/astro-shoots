import json
from pyongc import ongc


def filter_none(d):
    """
    Filter out key-value pairs from a dictionary where the value is None.

    Parameters:
    - d: A dictionary containing key-value pairs.

    Returns:
    - A new dictionary with only the key-value pairs where the value is not None.
    """
    return {k: v for k, v in d.items() if v is not None}


objectList = []
jsonObjectList = []
dsoDict = {}


def initialize():
    """
    Initializes the global variables objectList, jsonObjectList, and dsoDict.

    Parameters:
    None

    Returns:
    None
    """
    global objectList, jsonObjectList, dsoDict
    objectList = ongc.listObjects()
    jsonObjectList = [
        json.loads(obj.to_json(), object_hook=filter_none) for obj in objectList
    ]
    initialize_dso_dict()


def initialize_dso_dict():
    """
    Initializes a dictionary with JSON objects as values and primary IDs as keys.

    This function iterates through the jsonObjectList and adds each JSON object to the dsoDict
    dictionary with its primary ID as the key. If the JSON object has "other identifiers" specified,
    it adds each identifier as a key in the dsoDict dictionary with the JSON object as the value.
    If the identifier is a list, each identifier in the list is added as a key in the dsoDict
    dictionary with the JSON object as the value.

    Parameters:
    - None

    Returns:
    - None
    """
    for json_obj in jsonObjectList:
        # Add primary ID first
        dsoDict[json_obj["id"]] = json_obj

        # Check for other identifiers
        if "other identifiers" in json_obj:
            # Add each identifier
            for id_type, id_value in json_obj["other identifiers"].items():
                if id_value is not None:
                    if isinstance(id_value, list):
                        for identifier in id_value:
                            if identifier is not None:
                                dsoDict[identifier] = json_obj
                    else:
                        dsoDict[id_value] = json_obj

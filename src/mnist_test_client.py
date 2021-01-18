import base64
import requests
import json  # for writing category data to file
import logging
import os
import errno

from shapeandshare.dicebox.config.dicebox_config import DiceboxConfig
from shapeandshare.dicebox.connectors.filesystem_connector import FileSystemConnector
from shapeandshare.dicebox.utils.helpers import make_sure_path_exists

config_file = "./projects/mnist/dicebox.config"
dicebox_config = DiceboxConfig(config_file=config_file)

###############################################################################
# Setup logging.
###############################################################################
make_sure_path_exists(dicebox_config.LOGS_DIR)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.DEBUG,
    filemode="w",
    filename="%s/mnist_test_client.%s.log" % (dicebox_config.LOGS_DIR, os.uname()[1]),
)


def get_category_map():
    jdata = {}
    response = make_api_call("api/category", None, "GET")
    if "category_map" in response:
        jdata = response["category_map"]
        print("loaded category map from server.")

    if len(jdata) == 0:
        with open(f"{dicebox_config.WEIGHTS_DIR}/category_map.json") as data_file:
            raw_cat_data = json.load(data_file)
        for d in raw_cat_data:
            jdata[str(raw_cat_data[d])] = str(d)
        print("loaded category map from file.")

    # print(jdata)
    return jdata


def make_api_call(end_point, json_data, call_type):
    headers = {
        "Content-Type": "application/json",
        "API-ACCESS-KEY": dicebox_config.API_ACCESS_KEY,
        "API-VERSION": dicebox_config.API_VERSION,
    }
    try:
        url = "%s%s:%i/%s" % (
            dicebox_config.CLASSIFICATION_SERVER_URI,
            dicebox_config.CLASSIFICATION_SERVER,
            dicebox_config.CLASSIFICATION_SERVER_PORT,
            end_point,
        )
        # print(f"calling {url}")
        response = None
        if call_type == "GET":
            response = requests.get(url, data=json_data, headers=headers)
        elif call_type == "POST":
            # print(json_data)
            response = requests.post(url, data=json_data, headers=headers)

        if response is not None:
            if response.status_code != 500:
                return response.json()
    except Exception as error:
        print(f"Error: {str(error)}")
        return {}
    return {}


###############################################################################
# prep our data sets
print("Creating FileSystem Data Connector")
fsc = FileSystemConnector(
    config=dicebox_config, data_directory=dicebox_config.DATA_DIRECTORY, disable_data_indexing=False
)
print("Loading Data Set")
network_input_index = fsc.get_data_set()
# print("Network Input Index: %s" % network_input_index)

# Get our classification categories
server_category_map = get_category_map()
print("Category Map: %s" % server_category_map)

##############################################################################
# Evaluate the Model
##############################################################################

summary_fail = 0
summary_success = 0

count = 0
for index in network_input_index:
    metadata = network_input_index[index]

    filename = "%s%s" % (dicebox_config.DATA_DIRECTORY, index)
    print(f"filename: {filename}")
    with open(filename, "rb") as file:
        file_content: bytes = file.read()

    base64_encoded_content: bytes = base64.b64encode(file_content)
    base64_encoded_string: str = base64_encoded_content.decode("utf-8")

    outjson = {}
    outjson["data"] = base64_encoded_string

    json_data = json.dumps(outjson)

    prediction = {}

    SERVER_ERROR = False
    response = make_api_call("api/classify", json_data, "POST")
    # print(f"response: {response}")
    if "classification" in response:
        prediction = response["classification"]
        if prediction != -1:
            category = server_category_map[str(prediction)]
        else:
            SERVER_ERROR = True
    else:
        SERVER_ERROR = True

    if SERVER_ERROR is False:
        if category == metadata[1]:
            print("correct!")
            summary_success += 1
        else:
            print(f"FAIL - Expected {metadata[1]}, but received {category}")
            summary_fail += 1
    else:
        print("SERVER ERROR!")

    if count >= 1999:
        count += 1
        break
    else:
        count += 1


success_percentage = (float(summary_success) / count) * 100
failure_percentage = (float(summary_fail) / count) * 100

print("summary")
print("success: (%i)" % summary_success)
print("failures: (%i)" % summary_fail)
print("total tests: (%i)" % count)
print("success rate: (%f)" % success_percentage)
print("failure rate: (%f)" % failure_percentage)
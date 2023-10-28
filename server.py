from flask import Flask, request
import logging
import json
import mimetypes
import re
import time
import os

app = Flask(__name__)

file_name = os.environ.get("file_name")
PDF_FILE = "../data/" + file_name
file_name = os.path.basename(PDF_FILE)
file_name = os.path.splitext(file_name)[0]
base_path = "./marking_form/" + file_name
base_path_images = base_path + "/images/"
base_path_annotations = base_path + "/annotations/"
base_path_questions = base_path + "/questions"
base_path_javascript = base_path + "/javascript"


@app.route("/", methods=["GET"])
def index():
    filepath = base_path + "/index.html"
    mimetype, _ = mimetypes.guess_type(str(filepath))
    with open(filepath, "rb") as fh:
        content = fh.read()
    return content, 200, {"Content-type": mimetype}


@app.route("/<path:path>", methods=["GET"])
def get_file(path):
    filepath = base_path + "/" + path
    mimetype, _ = mimetypes.guess_type(str(filepath))
    with open(filepath, "rb") as fh:
        content = fh.read()
    return content, 200, {"Content-type": mimetype}


@app.route("/questions/<question>/index.html", methods=["POST"])
def save_question_data(question):
    json_str = request.data.decode("utf-8")
    data = json.loads(json_str)
    prefix = ""
    if data["type"] == "mark":
        prefix = "mark"
    elif data["type"] == "control":
        prefix = "control"
    filepath = base_path_questions + "/" + question + "/" + prefix + ".json"

    json_str = json.dumps(data["data"])
    f = open(filepath, "w")
    f.write(json_str)
    f.close()

    timestr = time.strftime("%Y%m%d-%H%M%S")
    filepath = (
        base_path_questions
        + "/"
        + question
        + "/"
        + prefix
        + "-"
        + timestr
        + ".json"
    )

    f = open(filepath, "w")
    f.write(json_str)
    f.close()

    logging.info("Saved: " + str(filepath))

    return request.data, 200, {"Content-type": "text/html"}


if __name__ == "__main__":
    app.run()
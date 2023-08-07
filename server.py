#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import mimetypes
import re
import time
import os
from ai_grader import get_score_and_feedback

file_name = os.environ.get("file_name")
PDF_FILE = "../data/" + file_name
file_name = os.path.basename(PDF_FILE)
file_name = os.path.splitext(file_name)[0]
base_path = "./marking_form/" + file_name
base_path_images = base_path + "/images/"
base_path_annotations = base_path + "/annotations/"
base_path_questions = base_path + "/questions"
base_path_javascript = base_path + "/javascript"


class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)

        if self.path == "/":
            filepath = f"{base_path}/index.html"
        else:
            filepath = f"{base_path}/{self.path[1:]}"

        mimetype, _ = mimetypes.guess_type(filepath)
        self.send_header("Content-type", mimetype)
        self.end_headers()

        with open(filepath, "rb") as f:
            content = f.read()
        self.wfile.write(content)

        return

    def do_POST(self):
        logging.info(self.path)

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        result = re.search(r"\/questions\/(.*)\/(.*)", self.path)
        question = result.group(1)
        data = json.loads(post_data.decode("utf-8"))
        logging.info("New data: %s", json.dumps(data))

        if self.path.endswith("grade.json"):
            logging.info("prompt")
            prompt = data["prompt"]
            answer = data["answer"]
            page = data["page"]
            result = get_score_and_feedback(prompt, answer)
            result["page"] = page
            self._set_response()
            self.wfile.write(json.dumps(result).encode())
            return

        prefix = {"mark": "mark", "control": "control"}.get(data["type"], "")
        filepath = f"{base_path_questions}/{question}/{prefix}.json"

        with open(filepath, "w") as f:
            json.dump(data["data"], f)

        timestr = time.strftime("%Y%m%d-%H%M%S")
        filepath = f"{base_path_questions}/{question}/{prefix}-{timestr}.json"

        with open(filepath, "w") as f:
            json.dump(data["data"], f)

        logging.info(f"Saved: {filepath}")

        self._set_response()
        self.wfile.write(post_data)

    def log_message(self, format, *args):
        return


def run(server_class=HTTPServer, handler_class=Server, port=8080):
    logging.basicConfig(
        filename=base_path + "/server.log", filemode="w", level=logging.DEBUG
    )
    server_address = ("localhost", port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()

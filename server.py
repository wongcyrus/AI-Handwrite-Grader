#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import html
import json
import mimetypes
import re
import time
from pathlib import Path


class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)

        this_dir = Path(__file__).resolve().parent
        if self.path == "/":
            filepath = this_dir / "output/grading_form" / "index.html"
        else:
            filepath = this_dir / "output/grading_form" / self.path[1:]
        mimetype, _ = mimetypes.guess_type(str(filepath))
        self.send_header("Content-type", mimetype)
        self.end_headers()

        with open(filepath, "rb") as fh:
            content = fh.read()
        self.wfile.write(content)

        return

    def do_POST(self):
        content_length = int(
            self.headers["Content-Length"]
        )  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        result = re.search("\/questions\/(.*)\/index.html", self.path)
        question = result.group(1)
        this_dir = Path(__file__).resolve().parent

        json_str = post_data.decode("utf-8")
        data = json.loads(json_str)
        print("New data")
        print(json_str)
        print()
        print(data)
        print()
        prefix = ""
        if data["type"] == "mark":
            prefix = "mark"
        elif data["type"] == "control":
            prefix = "control"
        filepath = (
            this_dir / "output/grading_form/questions/" / question / (prefix + ".json")
        )

        json_str = json.dumps(data["data"])
        print(json_str)
        print()
        f = open(filepath, "w")
        f.write(json_str)
        f.close()

        timestr = time.strftime("%Y%m%d-%H%M%S")
        filepath = (
            this_dir
            / "output/grading_form/questions/"
            / question
            / (prefix + "-" + timestr + ".json")
        )
        f = open(filepath, "w")
        f.write(json_str)
        f.close()

        logging.info("Saveed: " + str(filepath))

        self._set_response()
        self.wfile.write(post_data)

    def log_message(self, format, *args):
        return


def run(server_class=HTTPServer, handler_class=Server, port=8080):
    logging.basicConfig(filename="output/server.log", filemode="w", level=logging.DEBUG)
    server_address = ("", port)
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

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from flask import abort, request, jsonify
import re


def getlogdata():
    def file_get_contents(filename):
        with open(filename) as f:
            return f.read()

    if (
        request.environ["REQUEST_METHOD"] is None
        or request.environ["REQUEST_METHOD"] != "POST"
    ):
        abort(400, "Bad Request")

    dir = "/var/log/bme280log/"

    # if not os.path.exists(dir):
    #    os.mkdir(dir)
    # os.chmod(dir, 0o755)

    result = []

    if request.form.get("TYPE") == "FILELIST":
        files = []
        for file in os.listdir(dir):
            if not os.path.isfile(os.path.join(dir, file)):
                continue
            if re.search("\\.log$", file):
                files.append(file)
        files.sort(reverse=True)
        for file in files:
            date = file[0:4] + "/" + file[4:6] + "/" + file[6:8]
            result.append(date)
    elif request.form.get("TYPE") == "LOGDATA":
        result = {}
        if request.form.get("DATE") is not None:
            file = dir + request.form.get("DATE") + ".log"
            try:
                with open(file, "r") as f:
                    logdata = f.read().splitlines()
                    logdata.pop(0)
                    for line in logdata:
                        if line == "":
                            continue
                        val = line.split("\t")
                        result[val[1]] = [float(val[2]), float(val[3]), float(val[4])]
            except Exception:
                pass
    elif request.form.get("TYPE") == "CURRENT":
        file = dir + "current"
        data = file_get_contents(file).strip()
        val = data.split("\t")
        result = {
            "datetime": val[0] + " " + val[1],
            "temp": val[2],
            "humid": val[3],
            "press": val[4],
        }
    print(result)
    return jsonify(result)

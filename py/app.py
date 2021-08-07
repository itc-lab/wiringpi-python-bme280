#!/usr/bin/ python3
# -*- coding: utf-8 -*-

from flask import Flask
import getlogdata
import secrets

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

secret = secrets.token_urlsafe(32)
app.secret_key = secret


@app.route("/getlogdata", methods=["GET", "POST"])
def get():
    return getlogdata.getlogdata()


if __name__ == "__main__":
    app.run()

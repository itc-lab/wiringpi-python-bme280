#!/usr/bin/ python3
# -*- coding: utf-8 -*-

from flask import Flask
import proxyproc
import secrets

app_relay = Flask(__name__)
app_relay.config["JSON_AS_ASCII"] = False

secret = secrets.token_urlsafe(32)
app_relay.secret_key = secret


@app_relay.route("/proxyproc", methods=["GET", "POST"])
def get():
    return proxyproc.proxyproc()


if __name__ == "__main__":
    app_relay.run()

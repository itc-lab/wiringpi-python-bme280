#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import request
from flask.helpers import make_response
import pycurl
import re
import sys
import io
from urllib.parse import urlencode


def proxyproc():
    def _relay_request(url):
        ch = pycurl.Curl()
        ch.setopt(pycurl.SSL_VERIFYPEER, False)
        ch.setopt(pycurl.URL, url)
        if request.environ["REQUEST_METHOD"].upper() == "POST":
            ch.setopt(pycurl.POST, True)
            parameters = request.form.to_dict()
            del parameters["REQUEST_URL"]
            postfields = urlencode(parameters)
            ch.setopt(pycurl.POSTFIELDS, postfields)
        else:
            ch.setopt(pycurl.HTTPGET, True)
        headers = []
        for name, value in request.headers:
            if re.search("^Content-Length", name, re.IGNORECASE):
                continue
            if re.search("^Content-Type", name, re.IGNORECASE):
                continue
            if re.search("^Host", name, re.IGNORECASE):
                headers.append(name + ": " + value)
        headers.append("REMOTE_ADDR_X: " + request.environ.get("REMOTE_ADDR"))
        headers.append("REQUEST_URL_X: " + url)
        ch.setopt(pycurl.HTTPHEADER, headers)
        if request.environ["HTTP_USER_AGENT"] is not None:
            ch.setopt(pycurl.USERAGENT, request.environ.get("HTTP_USER_AGENT"))
        if request.environ.get("HTTP_COOKIE") is not None:
            ch.setopt(pycurl.COOKIE, request.environ.get("HTTP_COOKIE"))

        resp_headers = {}
        global chunked_flag
        chunked_flag = False

        def static_vars(**kwargs):
            def decorate(func):
                for k in kwargs:
                    setattr(func, k, kwargs[k])
                return func

            return decorate

        @static_vars(start_head=False, start_body=False, save="".encode("utf-8"))
        def call_back(buffer):
            ln = len(buffer)
            global chunked_flag
            if call_back.start_body:
                if chunked_flag:
                    sys.stdout.write(("%x\r\n" % (len(buffer))).encode("utf-8"))
                sys.stdout.write(buffer)
                if chunked_flag:
                    sys.stdout.write("\r\n".encode("utf-8"))
                sys.stdout.flush()
                return ln
            buffer = call_back.save + buffer
            while True:
                pos = buffer.find("\r\n".encode("utf-8"))
                if pos < 0:
                    break
                head = buffer[:pos]
                buffer = buffer[pos + 2 :]
                if pos != 0:
                    if (
                        re.search(rb"^HTTP\/", head)
                        and head.find("Continue".encode("utf-8")) < 0
                    ):
                        call_back.start_head = True
                    if call_back.start_head:
                        if re.search(
                            rb"^Transfer\-Encoding\:\s+chunked", head, re.IGNORECASE
                        ):
                            chunked_flag = True
                        # sys.stdout.write(head)
                        # sys.stdout.write("\r\n".encode("utf-8"))
                        h = head.decode("utf-8")
                        h = h.split(": ")
                        if len(h) > 1:
                            field = h[0]
                            value = h[1]
                            resp_headers[field] = value
                elif call_back.start_head:
                    call_back.start_body = True
                    if buffer != "".encode("utf-8"):
                        if chunked_flag:
                            sys.stdout.write(("%x\r\n" % (len(buffer))).encode("utf-8"))
                        sys.stdout.write(buffer)
                        if chunked_flag:
                            sys.stdout.write("\r\n".encode("utf-8"))
                        sys.stdout.flush()
                if call_back.start_body:
                    break
            call_back.save = buffer
            return ln

        old_stdout = sys.stdout
        sys.stdout = mystdout = io.BytesIO()
        ch.setopt(pycurl.HEADER, True)
        ch.setopt(pycurl.WRITEFUNCTION, call_back)
        try:
            ch.perform()
        except Exception:
            sys.stdout = old_stdout
            ch.close()
            return (
                "Could not connect to server\n'" + url + "'\r\n",
                403,
            )
        if chunked_flag:
            sys.stdout.write("0\r\n".encode("utf-8"))
            sys.stdout.write("\r\n".encode("utf-8"))
        sys.stdout = old_stdout
        ch.close()
        resp = make_response(mystdout.getvalue())
        for field, value in resp_headers.items():
            resp.headers.set(field, value)
        return resp

    url = request.form.get("REQUEST_URL")
    return _relay_request(url)

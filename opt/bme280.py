#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import signal
from bme280_inc import Bme280
from lcd1602_inc import Lcd1602
import time
import datetime
import fcntl

PID_FILE = "/var/run/bme280.pid"
LOG_DIR = "/var/log/bme280log/"
CURRENT_INTERVAL = 1
LOG_INTERVAL = 300


def file_get_contents(filename):
    with open(filename) as f:
        return f.read()


def file_put_contents(filename, data):
    with open(filename, "w") as f:
        f.write(data)


def touch(filename):
    if os.path.exists(filename):
        # os.utime(fname, None)
        pass
    else:
        open(filename, "a").close()


def file_put_contents_ex(filename, data):
    touch(filename)
    with open(filename) as lockfile:
        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)
        try:
            file_put_contents(filename, data)
        finally:
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)


def daemonize():
    try:
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if pid > 0:  # first parent
        os._exit(0)

    # decouple from parent environment
    try:
        os.setsid()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    try:
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if pid > 0:  # second parent
        pid_file = open(PID_FILE, "w")
        pid_file.write(str(pid) + "\n")
        pid_file.close()
        os._exit(0)

    # child daemon
    try:
        os.chdir("/")
        os.umask(0)
        # close stdio
        os.close(sys.stdin.fileno())
        os.close(sys.stdout.fileno())
        os.close(sys.stderr.fileno())
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))


if len(sys.argv) > 1 and sys.argv[1].lower() == "stop":
    pid = int(file_get_contents(PID_FILE))
    os.kill(pid, signal.SIGTERM)
    print("stoped")
    exit(0)

if os.path.isfile(PID_FILE):
    print("already running")
    exit(0)

try:
    daemonize()
except Exception as e:
    print("error: could not daemonize: %s" % e)
    sys.exit()

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR, 755)
lcd = Lcd1602(0x27)

signal.signal(
    signal.SIGTERM,
    lambda _signo, _stack_frame: [
        lcd.lcdClear(),
        lcd.lcdDisplay(False),
        os.unlink(PID_FILE),
        sys.exit(),
    ],
)

bme280 = Bme280(0x76)
prev = -1
while True:
    tm = int(time.time())
    dt_now = datetime.datetime.now()
    if tm == prev:
        time.sleep(100000 / 1000000.0)
        continue
    prev = tm

    bme280.readData()

    lcd.lcdPosition(0, 0)
    lcd.lcdPuts(
        "{0:5.2f}{1}C   {2:5.2f}%".format(
            bme280.temperature + 0.005, b"\xdf".decode("sjis"), bme280.humidity + 0.005
        )
    )
    lcd.lcdPosition(0, 1)
    lcd.lcdPuts("{0:.2f}hPa".format(bme280.pressure + 0.005))

    text = ""
    text += dt_now.strftime("%Y/%m/%d\t")
    text += dt_now.strftime("%H:%M:%S\t")
    text += "{0:.2f}\t".format(bme280.temperature + 0.005)
    text += "{0:.2f}\t".format(bme280.humidity + 0.005)
    text += "{0:.2f}".format(bme280.pressure + 0.005)
    if tm % CURRENT_INTERVAL == 0:
        log_file = LOG_DIR + "current"
        file_put_contents_ex(log_file, text)
    if tm % LOG_INTERVAL == 0:
        log_file = LOG_DIR + dt_now.strftime("%Y%m%d") + ".log"
        with open(log_file, "a") as f:
            pos = f.tell()
            if pos == 0:
                f.write("date\ttime\ttemp\thumid\tpress\n")
            f.write(text + "\n")

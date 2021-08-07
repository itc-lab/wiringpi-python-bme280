#!/usr/bin/python3
# -*- coding: utf-8 -*-
import wiringpi
import time


def usleep(x):
    return time.sleep(x / 1000000.0)


class Lcd1602:
    RS = 0
    RW = 1
    STRB = 2
    LED = 3
    D4 = 4
    D5 = 5
    D6 = 6
    D7 = 7

    LCD_BLINK_CTRL = 0x01
    LCD_CURSOR_CTRL = 0x02
    LCD_DISPLAY_CTRL = 0x04

    LCD_CLEAR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY = 0x04
    LCD_CTRL = 0x08
    LCD_CDSHIFT = 0x10
    LCD_FUNC = 0x20
    LCD_CGRAM = 0x40
    LCD_DGRAM = 0x80

    LCD_FUNC_F = 0x04
    LCD_FUNC_N = 0x08
    LCD_FUNC_DL = 0x10

    LCD_CDSHIFT_RL = 0x04
    LCD_ENTRY_ID = 0x02

    _rows = 2
    _cols = 16
    _bits = 4
    _cx = 0
    _cy = 0
    _rowOff = [0x00, 0x40, 0x14, 0x54]
    _lcdControl = 0

    old = 0  # static variable

    def __init__(self, addr, rows=2, cols=16, bits=4):
        self.lcd1602(addr, rows, cols, bits)

    def lcd1602(self, addr, rows=2, cols=16, bits=4):
        self.fd = wiringpi.wiringPiI2CSetup(addr)

        self._rows = rows
        self._cols = cols
        self._bits = bits

        for i in range(8):
            self.digitalWrite(i, wiringpi.LOW)
        self.digitalWrite(self.LED, wiringpi.HIGH)  # turn on LCD backlight
        self.digitalWrite(self.RW, wiringpi.LOW)  # allow writing to LCD

        self.digitalWrite(self.RS, wiringpi.LOW)
        self.digitalWrite(self.RS, wiringpi.LOW)
        self.digitalWrite(self.STRB, wiringpi.LOW)
        self.digitalWrite(self.STRB, wiringpi.LOW)
        for i in range(self._bits):
            dataPin = self.D4 + i
            self.digitalWrite(dataPin + i, wiringpi.LOW)
            self.digitalWrite(dataPin + i, wiringpi.LOW)

        func = self.LCD_FUNC | self.LCD_FUNC_DL  # Set 8-bit mode 3 times
        self.put4Command(func >> 4)
        usleep(35000)
        self.put4Command(func >> 4)
        usleep(35000)
        self.put4Command(func >> 4)
        usleep(35000)
        func = self.LCD_FUNC  # 4th set: 4-bit mode
        self.put4Command(func >> 4)
        usleep(35000)
        func |= self.LCD_FUNC_N
        self.putCommand(func)
        usleep(35000)

        self.lcdDisplay(True)
        self.lcdCursor(False)
        self.lcdCursorBlink(False)
        self.lcdClear()

        self.putCommand(self.LCD_ENTRY | self.LCD_ENTRY_ID)
        self.putCommand(self.LCD_CDSHIFT | self.LCD_CDSHIFT_RL)

    def lcdPosition(self, x, y):
        if (x > self._cols) or (x < 0):
            return
        if (y > self._rows) or (y < 0):
            return
        self.putCommand(x + (self.LCD_DGRAM | self._rowOff[y]))
        self._cx = x
        self._cy = y

    def lcdPutchar(self, data):
        self.digitalWrite(self.RS, 1)
        self.sendDataCmd(data)
        self._cx += 1
        if self._cx >= self._cols:
            self._cx = 0
            self._cy += 1
            if self._cy >= self._rows:
                self._cy = 0
            self.putCommand(self._cx + (self.LCD_DGRAM | self._rowOff[self._cy]))

    def lcdPuts(self, string):
        chars = bytearray(string.encode("sjis"))
        for n in range(len(chars)):
            self.lcdPutchar(chars[n])

    def digitalWrite(self, pin, value):
        bit = 1 << (pin & 7)
        if value == wiringpi.LOW:
            self.old &= ~bit
        else:
            self.old |= bit
        wiringpi.wiringPiI2CWrite(self.fd, self.old)

    def lcdDisplay(self, state):
        if state:
            self._lcdControl |= self.LCD_DISPLAY_CTRL
        else:
            self._lcdControl &= ~self.LCD_DISPLAY_CTRL
            self.digitalWrite(self.LED, wiringpi.LOW)  # turn off LCD backlight
        self.putCommand(self.LCD_CTRL | self._lcdControl)

    def lcdCursor(self, state):
        if state:
            self._lcdControl |= self.LCD_CURSOR_CTRL
        else:
            self._lcdControl &= ~self.LCD_CURSOR_CTRL
        self.putCommand(self.LCD_CTRL | self._lcdControl)

    def lcdCursorBlink(self, state):
        if state:
            self._lcdControl |= self.LCD_BLINK_CTRL
        else:
            self._lcdControl &= ~self.LCD_BLINK_CTRL
        self.putCommand(self.LCD_CTRL | self._lcdControl)

    def lcdClear(self):
        self.putCommand(self.LCD_CLEAR)
        self.putCommand(self.LCD_HOME)
        self._cx = self._cy = 0
        usleep(5000)

    def strobe(self):
        self.digitalWrite(self.STRB, wiringpi.HIGH)
        usleep(50)
        self.digitalWrite(self.STRB, wiringpi.LOW)
        usleep(50)

    def sendDataCmd(self, data):
        for i in range(4):
            d = wiringpi.HIGH if (data & (0x10 << i)) else wiringpi.LOW
            self.digitalWrite(self.D4 + i, d)
        self.strobe()
        for i in range(4):
            d = wiringpi.HIGH if (data & (0x01 << i)) else wiringpi.LOW
            self.digitalWrite(self.D4 + i, d)
        self.strobe()

    def putCommand(self, command):
        self.digitalWrite(self.RS, wiringpi.LOW)
        self.sendDataCmd(command)
        usleep(2000)

    def put4Command(self, command):
        self.digitalWrite(self.RS, wiringpi.LOW)
        for i in range(4):
            self.digitalWrite(
                self.D4 + i, wiringpi.HIGH if (command & (1 << i)) else wiringpi.LOW
            )
        self.strobe()

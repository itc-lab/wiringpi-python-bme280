#!/usr/bin/python
# -*- coding: utf-8 -*-
import wiringpi


class Bme280:
    _t_fine = 0

    def __init__(self, addr):
        self._fd = wiringpi.wiringPiI2CSetup(addr)
        self.setup()

    def bme280(self, addr):
        self._fd = wiringpi.wiringPiI2CSetup(addr)
        self.setup()

    def readData(self):
        data = []
        for reg in range(0xF7, 0xFF + 1):
            data.append(wiringpi.wiringPiI2CReadReg8(self._fd, reg))
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]

        self.temperature = self.compensate_T_double(temp_raw)
        self.pressure = self.compensate_P_double(pres_raw)
        self.humidity = self.compensate_H_double(hum_raw)

    def compensate_T_double(self, adc_T):
        v1 = (adc_T / 16384.0 - self._dig_T1 / 1024.0) * self._dig_T2
        v2 = (
            (adc_T / 131072.0 - self._dig_T1 / 8192.0)
            * (adc_T / 131072.0 - self._dig_T1 / 8192.0)
            * self._dig_T3
        )
        self._t_fine = v1 + v2
        return self._t_fine / 5120.0

    def compensate_P_double(self, adc_P):
        v1 = (self._t_fine / 2.0) - 64000.0
        v2 = v1 * v1 * self._dig_P6 / 32768.0
        v2 = v2 + v1 * self._dig_P5 * 2.0
        v2 = (v2 / 4.0) + self._dig_P4 * 65536.0
        v1 = (self._dig_P3 * v1 * v1 / 524288.0 + self._dig_P2 * v1) / 524288.0
        v1 = (1 + v1 / 32768.0) * self._dig_P1
        if v1 == 0:
            return 0
        p = 1048576.0 - adc_P
        p = (p - (v2 / 4096.0)) * 6250.0 / v1
        v1 = self._dig_P9 * p * p / 2147483648.0
        v2 = p * self._dig_P8 / 32768.0
        p = p + (v1 + v2 + self._dig_P7) / 16.0
        return p / 100.0  # Pa -> hPa

    def compensate_H_double(self, adc_H):
        var_h = self._t_fine - 76800.0
        if var_h == 0:
            return 0
        var_h = (adc_H - (self._dig_H4 * 64.0 + self._dig_H5 / 16384.0 * var_h)) * (
            self._dig_H2
            / 65536.0
            * (
                1.0
                + self._dig_H6
                / 67108864.0
                * var_h
                * (1.0 + self._dig_H3 / 67108864.0 * var_h)
            )
        )
        var_h = var_h * (1.0 - self._dig_H1 * var_h / 524288.0)
        if var_h > 100.0:
            var_h = 100.0
        elif var_h < 0.0:
            var_h = 0.0
        return var_h

    def setup(self):
        self.calibrate()
        osrs_t = 2  # Temperature oversampling x 2
        osrs_p = 2  # Pressure oversampling x 2
        osrs_h = 2  # Humidity oversampling x 2
        mode = 3  # Normal mode
        t_sb = 5  # Tstandby 1000ms
        filter = 0  # Filter off
        spi3w_en = 0  # 3-wire SPI Disable
        ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
        config_reg = (t_sb << 5) | (filter << 2) | spi3w_en
        ctrl_hum_reg = osrs_h
        wiringpi.wiringPiI2CWriteReg8(self._fd, 0xF2, ctrl_hum_reg)
        wiringpi.wiringPiI2CWriteReg8(self._fd, 0xF4, ctrl_meas_reg)
        wiringpi.wiringPiI2CWriteReg8(self._fd, 0xF5, config_reg)

    def calibrate(self):
        self._dig_T1 = wiringpi.wiringPiI2CReadReg16(self._fd, 0x88)
        self._dig_T2 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x8A))
        self._dig_T3 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x8C))
        self._dig_P1 = wiringpi.wiringPiI2CReadReg16(self._fd, 0x8E)
        self._dig_P2 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x90))
        self._dig_P3 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x92))
        self._dig_P4 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x94))
        self._dig_P5 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x96))
        self._dig_P6 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x98))
        self._dig_P7 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x9A))
        self._dig_P8 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x9C))
        self._dig_P9 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0x9E))
        self._dig_H1 = wiringpi.wiringPiI2CReadReg8(self._fd, 0xA1)
        self._dig_H2 = self.signed16(wiringpi.wiringPiI2CReadReg16(self._fd, 0xE1))
        self._dig_H3 = wiringpi.wiringPiI2CReadReg8(self._fd, 0xE3)
        self._dig_H4 = self.signed16(
            wiringpi.wiringPiI2CReadReg8(self._fd, 0xE4) << 4
            | wiringpi.wiringPiI2CReadReg8(self._fd, 0xE5) & 0x0F
        )
        self._dig_H5 = self.signed16(
            wiringpi.wiringPiI2CReadReg8(self._fd, 0xE6) << 4
            | (wiringpi.wiringPiI2CReadReg8(self._fd, 0xE5) >> 4) & 0x0F
        )
        self._dig_H6 = self.signed8(wiringpi.wiringPiI2CReadReg8(self._fd, 0xE7))

    def signed16(self, val):
        if val & 0x8000:
            val = -((val ^ 0xFFFF) + 1)
        return val

    def signed8(self, val):
        if val & 0x80:
            val = -((val ^ 0xFF) + 1)
        return val

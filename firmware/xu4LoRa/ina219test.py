from ina219 import INA219
from ina219 import DeviceRangeError
import odroid_wiringpi as wpi

wpi.wiringPiSetup()
import time

SHUNT_OHMS = 0.1
MAX_EXPECTED_AMPS = 0.2


def read():
    try:
        batteryLevelRaw = wpi.analogRead(29)
        print(batteryLevelRaw)

        inaSolarOut   = INA219(SHUNT_OHMS, busnum=1)
        inaBatteryOut = INA219(SHUNT_OHMS, address=0x41, busnum=1)

        print("Adafruit_GPIO.I2C" in str(inaSolarOut._i2c))

        inaSolarOut.configure()
        inaBatteryOut.configure()

        print("Bus Voltage   : %.3f V" % inaSolarOut.voltage())
        print("Bus Current   : %.3f mA" % inaSolarOut.current())
        print("Power         : %.3f mW" % inaSolarOut.power())
        print("Shunt voltage : %.3f mV" % inaSolarOut.shunt_voltage())

        print("Bus Voltage   : %.3f V" % inaBatteryOut.voltage())
        print("Bus Current   : %.3f mA" % inaBatteryOut.current())
        print("Power         : %.3f mW" % inaBatteryOut.power())
        print("Shunt voltage : %.3f mV" % inaBatteryOut.shunt_voltage())
    
    except Exception as e:
        time.sleep(.5)
        print ("Error and type: %s - %s." % (e,type(e)))
        time.sleep(.5)
        print("Data Packet Not Sent for PM")
        time.sleep(.5)


if __name__ == "__main__":
    read()


#include <Arduino.h>
#include <Wire.h>
#include <devicesMints.h>
#include <jobsMints.h>

// bool PPD42NSOnline;

// uint8_t PPD42NSPinMid = 3;
// uint8_t PPD42NSPinPM10 = 4;

bool    LIBRADOnline;
uint8_t LIBRADPin   = 2;
long    LIBRADCount = 0;

bool BME680Online;


#define IIC_ADDR  uint8_t(0x77) // This needs to change on other central nodes - only for cn 4 
Seeed_BME680 bme680(IIC_ADDR); /* IIC PROTOCOL */


uint16_t initPeriod = 1500;

void setup() {
  initializeSerialMints();
  delay(initPeriod);
  BME680Online = initializeBME680Mints();
  delay(initPeriod);
  LIBRADOnline       = initializeLIBRADMints();
}


// the loop routine runs over and over again forever:
void loop() {

 if(BME680Online)
    {
      readBME680Mints();
    }

  if(LIBRADOnline)
      {
        readLIBRADMints(30);
      }

}

#include <Arduino.h>
#include <Wire.h>
//
// #include "DFRobot_AS3935_I2C.h"
// #include "Lib_I2C.h"


#include "devicesMints.h"
#include "jobsMints.h"

uint8_t SEN0232Pin = A1;


uint16_t sensingPeriod =2500;
uint16_t initPeriod =1500;

volatile int8_t AS3935IsrTrig = 0;

#define IRQ_PIN              2

// // Antenna tuning capcitance (must be integer multiple of 8, 8 - 120 pf)
// #define AS3935_CAPACITANCE   96
//

// // I2C address
// #define AS3935_I2C_ADDR       AS3935_ADD3

unsigned long startTime;

bool AS3935Online;
void AS3935_ISR();


DFRobot_AS3935_I2C  lightning0((uint8_t)IRQ_PIN);

void setup()
{
  delay(initPeriod);
  initializeSerialMints();

  delay(initPeriod);
  AS3935Online = initializeAS3935Mints();

  attachInterrupt(0, AS3935_ISR, RISING);
  startTime  = millis();
}


void loop()
{
  // It does nothing until an interrupt is detected on the IRQ pin.
  if(AS3935Online & AS3935IsrTrig == 1 ) {
    AS3935IsrTrig = 0;
    readAS3935Mints();
  }

  if(millis() - startTime > sensingPeriod) {
    startTime = millis();
    readSEN0232Mints(SEN0232Pin);
  }

}


// void readAS3935Mints(){

//     uint8_t     src   = lightning0.getInterruptSrc();
//     uint32_t energy   = lightning0.getStrikeEnergyRaw();
//     uint8_t  distance = lightning0.getLightningDistKm();

//     String readings[3] = { String(src), String(energy) , String(distance)};
//     sensorPrintMints("AS3935",readings,3);

// }

// bool initializeAS3935Mints(){

//   I2c.begin();
//   I2c.pullup(true);
//   I2c.setSpeed(1);

//   delay(2);

//   lightning0.setI2CAddress(AS3935_ADD3);

//   // Set registers to default


//   if(lightning0.defInit() == 0){
//     lightning0.powerUp();
//     lightning0.setOutdoors();
//     lightning0.disturberEn();
//     lightning0.setIRQOutputSource(0);
//     lightning0.setTuningCaps(AS3935_CAPACITANCE);
//     lightning0.setNoiseFloorLvl(2);
//     lightning0.setWatchdogThreshold(2);
//     lightning0.setSpikeRejection(2);
//     Serial.println("AS3935 initiated");
//     delay(1);
//     return true;
//   }
//   else{
//     Serial.println("AS3935 not found");
//     return false;
//   }
//   // Configure sensor

// }



//IRQ handler for AS3935 interrupts
void AS3935_ISR()
{
  AS3935IsrTrig = 1;
}

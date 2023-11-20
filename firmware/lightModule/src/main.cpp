
#include <Arduino.h>

#include <Wire.h>


#include "SI114X.h"
#include "TMG39931Mints.h"

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>

#include <Adafruit_AS726x.h>
#include "Adafruit_TSL2591.h"
#include <SparkFun_VEML6075_Arduino_Library.h>

#include "devicesMints.h"
#include "jobsMints.h"


// TMG39931 I2C address is 0x39(57)
bool TMG39931Online;
TMG39931Mints TMG(0x39);

bool SI114XOnline;
SI114X SI = SI114X();


//create the object
bool AS7262Online;
Adafruit_AS726x ams;

bool    TSL2591Online;
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591); // pass in a number for the sensor identifier (for your use later)

bool VEML6075Online;
VEML6075 veml ;

uint8_t groveLuminancePin = A0;
uint8_t groveLightPin = A1;
uint8_t groveUVPin = A2;


uint16_t sensingPeriod =1000;
uint16_t initPeriod = 1500;

unsigned long startTime;

void setup() {


  delay(initPeriod);
  initializeSerialMints();



  // SI1145.Begin();

  Serial.println("initializing AS7262");
  delay(initPeriod);
  AS7262Online = initializeAS7262Mints();

  Serial.println("initializing TSL2591");
  delay(initPeriod);
  TSL2591Online      = initializeTSL2591Mints();

  Serial.println("initializing VEML6075");
  delay(initPeriod);
  VEML6075Online      = initializeVEML6075Mints();

  Serial.println("initializing TMG39931");
  delay(initPeriod);
  TMG39931Online      = initializeTMG39931Mints();


  Serial.println("initializing SII4X");
  delay(initPeriod);
  SI114XOnline      = initializeSI114XMints();


}

// the loop routine runs over and over again forever:
void loop(){
    startTime  = millis();


  // delay(5000);


  delay(sensingPeriod);
   if(AS7262Online)
   {
     readAS7262Mints();
   }
   delay(sensingPeriod);

   if(TSL2591Online)
       {
         readTSL2591Mints();
       }

   delay(sensingPeriod);

   if(VEML6075Online)
       {
         readVEML6075Mints();
       }
     delay(sensingPeriod);

   if(TMG39931Online)
       {
         readTMG39931Mints();
       }
     delay(sensingPeriod);
  
   if(SI114XOnline)
       {
         readSI114XMints();
       }
     delay(sensingPeriod);
  

  delay(sensingPeriod);
     readGL001Mints(groveLightPin);


  delay(sensingPeriod);
     readGUV001Mints(groveUVPin);


  delay(sensingPeriod);
     readAPDS9002Mints(groveLuminancePin);

    delayMints(millis() - startTime,10000);
}









#include <Arduino.h>

// Touch pins mapped to GPIOs
const int pins[] = {2, 15, 13, 12, 32, 33, 27};  // TOUCH2,3,4,5,9,8,7
const int numPins = sizeof(pins)/sizeof(pins[0]);
const int threshold = 40;  // adjust if needed

bool prevStates[numPins] = {false,false,false,false,false,false,false};

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 TTGO Multi-Touch Test");
}

void loop() {
  for(int i=0;i<numPins;i++){
    int val = touchRead(pins[i]);
    bool isTouched = val < threshold;  // lower value = touch
    if(isTouched != prevStates[i]){
      Serial.print(pins[i]);
      Serial.print(",");
      Serial.println(isTouched ? "1":"0");
      prevStates[i] = isTouched;
    }
  }
  delay(20); // small delay to avoid flooding
}
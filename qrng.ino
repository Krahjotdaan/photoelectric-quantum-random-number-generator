const int sensorPin = A0;
bool isRunning = false;

void setup() {
  Serial.begin(500000);
  delay(100);
  
  while (Serial.available() > 0) {
    Serial.read();
  }
}

void loop() {
  if (!isRunning) {
    if (Serial.available() > 0) {
      char command = Serial.read();
      isRunning = true;
    }
    return; 
  }

  int val = analogRead(sensorPin);
  Serial.println(val);
}
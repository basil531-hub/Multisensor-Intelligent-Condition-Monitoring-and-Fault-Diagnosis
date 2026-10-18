/*
 * DrillSense — Condition Monitoring Firmware (Stable Version)
 * UET Lahore
 *
 * This is the tested working firmware version for the DrillSense system.
 *
 * Hardware:
 *  - Arduino Uno R3
 *  - ACS712 current sensor (A0)
 *  - LM35 temperature sensor (A1)
 *  - Piezoelectric vibration sensor (A2)
 *  - DHT11 humidity & temperature sensor (D4)
 *
 * Output Format (CSV over Serial @ 115200 baud):
 * Timestamp, Current_A, Power_W, LM35_Temp_C,
 * DHT_Temp_C, Humidity_%, Vibration_Detect, Vibration_Peak
 *
 * Sampling Rate:
 *  - 20 Hz (50 ms cycle time)
 */

#include <Arduino.h>
#include "DHT.h"

// ─────────────────────────────────────────────
// ACS712 Current Sensor Configuration
// ─────────────────────────────────────────────
#define ACS712_PIN          A0
#define ACS712_SENSITIVITY  0.066   // V/A for 30A module
#define ADC_VREF            5.0
#define ADC_RESOLUTION      1023.0
#define SAMPLES             50      // RMS sample window

// ─────────────────────────────────────────────
// LM35 Temperature Sensor
// ─────────────────────────────────────────────
#define LM35_PIN  A1

// ─────────────────────────────────────────────
// Piezo Vibration Sensor
// ─────────────────────────────────────────────
#define PIEZO_ANALOG_PIN    A2
#define VIBRATION_THRESHOLD 50

// ─────────────────────────────────────────────
// DHT11 Sensor Configuration
// ─────────────────────────────────────────────
#define DHTPIN   4
#define DHTTYPE  DHT11

DHT dht(DHTPIN, DHTTYPE);

// ─────────────────────────────────────────────
// Function: Read RMS Current from ACS712
// ─────────────────────────────────────────────
float readCurrentRMS() {
    float sumSquares = 0;

    for (int i = 0; i < SAMPLES; i++) {
        float raw     = analogRead(ACS712_PIN);
        float voltage = (raw / ADC_RESOLUTION) * ADC_VREF;
        float current = (voltage - 2.5) / ACS712_SENSITIVITY;

        sumSquares += current * current;
        delayMicroseconds(200);
    }

    return sqrt(sumSquares / SAMPLES);
}

// ─────────────────────────────────────────────
// Function: Read LM35 Temperature
// ─────────────────────────────────────────────
float readLM35() {
    int raw = analogRead(LM35_PIN);

    // Convert ADC reading → voltage → temperature (°C)
    float voltage = (raw / ADC_RESOLUTION) * ADC_VREF * 1000.0;

    return voltage / 10.0;
}

// ─────────────────────────────────────────────
// Function: Get Peak Vibration Value (Piezo)
// ─────────────────────────────────────────────
int readVibrationPeak() {
    int peak = 0;
    unsigned long start = millis();

    while (millis() - start < 30) {
        int val = analogRead(PIEZO_ANALOG_PIN);
        if (val > peak) peak = val;

        delayMicroseconds(200);
    }

    return peak;
}

// ─────────────────────────────────────────────
// Function: Generate Timestamp (HH:MM:SS.mmm)
// ─────────────────────────────────────────────
String getTimestamp() {
    unsigned long ms   = millis();
    unsigned long secs = ms / 1000;
    unsigned long mins = secs / 60;
    unsigned long hrs  = mins / 60;

    ms   %= 1000;
    secs %= 60;
    mins %= 60;

    char buf[16];
    sprintf(buf, "%02lu:%02lu:%02lu.%03lu", hrs, mins, secs, ms);

    return String(buf);
}

// ─────────────────────────────────────────────
// Setup Function
// ─────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    dht.begin();
}

// ─────────────────────────────────────────────
// Main Loop (Runs at ~20 Hz)
// ─────────────────────────────────────────────
void loop() {
    unsigned long loopStart = millis();

    // ── Timestamp ─────────────────────────────
    String timestamp = getTimestamp();

    // ── Sensor Readings ───────────────────────
    float current  = readCurrentRMS();
    float power    = 220.0 * current;

    float tempLM35 = readLM35();

    float humidity = dht.readHumidity();
    float tempDHT  = dht.readTemperature();

    int  vibStr    = readVibrationPeak();
    bool vibDetect = vibStr > VIBRATION_THRESHOLD;

    // ── CSV Output ─────────────────────────────
    Serial.print(timestamp); Serial.print(",");

    Serial.print(current, 3); Serial.print(",");
    Serial.print(power, 1);   Serial.print(",");
    Serial.print(tempLM35, 1); Serial.print(",");

    // Handle DHT sensor errors safely
    if (isnan(tempDHT)) Serial.print("NA");
    else Serial.print(tempDHT, 1);

    Serial.print(",");

    if (isnan(humidity)) Serial.print("NA");
    else Serial.print(humidity, 1);

    Serial.print(",");

    Serial.print(vibDetect ? "YES" : "NO");
    Serial.print(",");
    Serial.println(vibStr);

    // ── Maintain 50 ms cycle (20 Hz sampling) ──
    unsigned long elapsed = millis() - loopStart;
    if (elapsed < 50) delay(50 - elapsed);
}
/*
  ==============================================================================
  ROV NEMO - Sistema de Telemetría y Control Submarino
  ==============================================================================
  Sensores:
    - Temperatura : Sensor Dallas DS18B20 (Pin Digital 2)
    - Turbidez    : Sensor Analógico (Pin A0)
    - pH          : Sensor Analógico (Pin A1)
    
  Actuadores:
    - Bomba 1     : Relé / MOSFET (Pin Digital 9)
    - Bomba 2     : Relé / MOSFET (Pin Digital 10)
    - Diagnóstico : LED Integrado en Placa (Pin Digital 13)
    
  Comunicación:
    - Puerto Serie a 9600 Baudios (Formato JSON) mediante ServerBridgeX (USB OTG)
  ==============================================================================
*/

#include <OneWire.h>
#include <DallasTemperature.h>

// --- ASIGNACIÓN DE PINES ---
const int bomba1 = 9;
const int bomba2 = 10;
const int ledPlaca = 13; // LED integrado de diagnóstico

#define PIN_TURBIDEZ A0
#define PIN_PH        A1
#define PIN_ONE_WIRE  2  // Pin digital sensor DS18B20

// --- CONFIGURACIÓN DE LÓGICA DE RELÉS ---
// Cambia esto si tu módulo de relés activa con voltaje bajo (Active LOW):
//   Active HIGH : ON_RELAY = HIGH, OFF_RELAY = LOW  (Estándar MOSFET / Transistores)
//   Active LOW  : ON_RELAY = LOW,  OFF_RELAY = HIGH (La mayoría de módulos de relés de 2/4 canales)
const int ON_RELAY  = HIGH; 
const int OFF_RELAY = LOW;  

// --- OBJETOS Y VARIABLES DE CONTROL ---
OneWire oneWire(PIN_ONE_WIRE);
DallasTemperature sensorTemp(&oneWire);

unsigned long ultimoEnvio = 0;
const long intervaloEnvio = 3000; // Intervalo de envío de telemetría (3 segundos)

int estadoBomba1 = 0;
int estadoBomba2 = 0;

void setup() {
  Serial.begin(9600);

  // Configuración de pines de salida
  pinMode(bomba1, OUTPUT);
  pinMode(bomba2, OUTPUT);
  pinMode(ledPlaca, OUTPUT);

  // Estado inicial: Apagado
  digitalWrite(bomba1, OFF_RELAY);
  digitalWrite(bomba2, OFF_RELAY);
  digitalWrite(ledPlaca, LOW);

  // Inicializar sensor de temperatura
  sensorTemp.begin();
}

void loop() {
  // ==========================================================================
  // 1. RECEPCIÓN Y EJECUCIÓN DE COMANDOS (ServerBridgeX -> Arduino)
  // ==========================================================================
  if (Serial.available() > 0) {
    char comando = Serial.read();

    if (comando == '1') {
      digitalWrite(bomba1, ON_RELAY);
      digitalWrite(ledPlaca, HIGH);
      estadoBomba1 = 1;
    } 
    else if (comando == '2') {
      digitalWrite(bomba2, ON_RELAY);
      digitalWrite(ledPlaca, HIGH);
      estadoBomba2 = 1;
    } 
    else if (comando == '3') {
      digitalWrite(bomba1, ON_RELAY);
      digitalWrite(bomba2, ON_RELAY);
      digitalWrite(ledPlaca, HIGH);
      estadoBomba1 = 1;
      estadoBomba2 = 1;
    } 
    else if (comando == '4') {
      digitalWrite(bomba1, OFF_RELAY);
      estadoBomba1 = 0;
      if (estadoBomba2 == 0) digitalWrite(ledPlaca, LOW);
    } 
    else if (comando == '5') {
      digitalWrite(bomba2, OFF_RELAY);
      estadoBomba2 = 0;
      if (estadoBomba1 == 0) digitalWrite(ledPlaca, LOW);
    } 
    else if (comando == '0') {
      digitalWrite(bomba1, OFF_RELAY);
      digitalWrite(bomba2, OFF_RELAY);
      digitalWrite(ledPlaca, LOW);
      estadoBomba1 = 0;
      estadoBomba2 = 0;
    }
  }

  // ==========================================================================
  // 2. LECTURA DE SENSORES Y ENVÍO DE TELEMETRÍA (JSON)
  // ==========================================================================
  unsigned long tiempoActual = millis();
  if (tiempoActual - ultimoEnvio >= intervaloEnvio) {
    ultimoEnvio = tiempoActual;

    // Lectura Temperatura (°C)
    sensorTemp.requestTemperatures();
    float temperatura = sensorTemp.getTempCByIndex(0);
    if (temperatura < -55.0) temperatura = 0.0; // Corrección si el sensor está desconectado

    // Lectura Turbidez (%)
    int valTurb = analogRead(PIN_TURBIDEZ);
    float turbidez = map(valTurb, 0, 1023, 100, 0); 

    // Lectura pH
    int valPH = analogRead(PIN_PH);
    float ph = (valPH * (5.0 / 1023.0)) * 3.5; 

    // Construcción y envío de la trama JSON
    Serial.print("{\"turbidez\": ");
    Serial.print(turbidez, 1);
    Serial.print(", \"temperatura\": ");
    Serial.print(temperatura, 1);
    Serial.print(", \"ph\": ");
    Serial.print(ph, 2);
    Serial.print(", \"b1\": ");
    Serial.print(estadoBomba1);
    Serial.print(", \"b2\": ");
    Serial.print(estadoBomba2);
    Serial.println("}");
  }
}
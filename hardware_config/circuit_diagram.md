# Hardware Setup and Circuit Diagrams

## System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  ESP8266 Node   │         │  Raspberry Pi    │         │  Google Cloud   │
│  with Sensors   │◄───────►│  Server          │◄───────►│  Platform       │
│                 │  WiFi   │                  │ Internet│                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
      │                              │                           │
      ├─ MQ-135                     ├─ Flask API               ├─ Firestore
      ├─ DHT11/22                   ├─ SQLite DB               └─ Cloud Storage
      ├─ HC-SR04                    └─ Alert System
      └─ Status LED
```

## Components List

### ESP8266 Sensor Node (Per Room/Location)

#### Core Components
- **ESP8266 Development Board** (NodeMCU or Wemos D1 Mini) × 1
- **Breadboard** (830 points) × 1
- **Jumper Wires** (Male-to-Male, Male-to-Female) × 20+
- **USB Cable** (Micro USB for NodeMCU or USB-C for some boards) × 1
- **5V Power Supply** (minimum 1A) × 1

#### Sensors
1. **MQ-135 Air Quality Sensor** × 1
   - Detects: NH3, NOx, alcohol, benzene, smoke, CO2
   - Operating Voltage: 5V
   - Output: Analog (0-1023)
   - Price: ~$5-8

2. **DHT11 or DHT22 Temperature & Humidity Sensor** × 1
   - DHT11: Temperature: 0-50°C (±2°C), Humidity: 20-90% (±5%)
   - DHT22: Temperature: -40-80°C (±0.5°C), Humidity: 0-100% (±2-5%)
   - Operating Voltage: 3.3-5V
   - Recommended: DHT22 for better accuracy
   - Price: DHT11 ~$2-3, DHT22 ~$4-6

3. **HC-SR04 Ultrasonic Distance Sensor** × 1
   - Range: 2cm - 400cm
   - Operating Voltage: 5V
   - Accuracy: ±3mm
   - Price: ~$3-5

#### Additional Components
- **Status LED** (any color, 5mm) × 1
- **220Ω Resistor** (for LED) × 1
- **10kΩ Pull-up Resistor** (for DHT sensor if module doesn't have one) × 1
- **Capacitors**: 100µF electrolytic (optional, for power stabilization) × 1

### Raspberry Pi Server

#### Core Components
- **Raspberry Pi 4 Model B** (2GB RAM minimum, 4GB recommended) × 1
- **MicroSD Card** (32GB Class 10 or higher) × 1
- **Raspberry Pi Power Supply** (5V 3A USB-C) × 1
- **Ethernet Cable** or WiFi dongle (built-in WiFi for Pi 3/4) × 1
- **Case** (with cooling fan recommended) × 1

#### Optional Components
- **Heat Sinks** for CPU and RAM
- **Cooling Fan**
- **External SSD** (for better performance and reliability)
- **UPS/Battery Backup** (for continuous operation during power outages)

### Total Cost Estimate (Per Node + Server)
- ESP8266 Node: $25-40
- Raspberry Pi Setup: $60-100
- Additional materials: $10-20
- **Total: $95-160** (excluding Google Cloud costs)

## ESP8266 Circuit Diagram

### Pin Configuration

```
ESP8266 NodeMCU v1.0 (ESP-12E)
                    ┌─────────┐
                    │  ╔═══╗  │
                    │  ║USB║  │
                    │  ╚═══╝  │
                    │         │
         RESET  ────┤ RST  TX ├──── TX (Serial)
       GPIO16  ────┤ D0   RX ├──── RX (Serial)
       GPIO14  ────┤ D5   D1 ├──── GPIO5
       GPIO12  ────┤ D6   D2 ├──── GPIO4 (DHT Sensor)
       GPIO13  ────┤ D7   D3 ├──── GPIO0
       GPIO15  ────┤ D8   D4 ├──── GPIO2
                   │ 3V3  G  │
                   │ GND  5V │
                   └─────────┘
```

### MQ-135 Air Quality Sensor Connection

```
MQ-135 Module
┌──────────────┐
│   MQ-135     │
│              │
│  VCC ────────┼──── 5V (VIN on ESP8266)
│  GND ────────┼──── GND
│  AOUT ───────┼──── A0 (ESP8266)
│  DOUT ───────┼──── Not used
│              │
└──────────────┘

Note: MQ-135 requires 24-48 hours of initial heating for accurate readings.
Some modules have onboard comparator for digital output (DOUT).
```

### DHT11/DHT22 Temperature & Humidity Sensor Connection

```
DHT11/DHT22 Sensor (3-pin module)
┌──────────────┐
│    DHT22     │
│              │
│  + (VCC) ────┼──── 3.3V (ESP8266)
│  OUT ────────┼──── D4 (GPIO2)
│  - (GND) ────┼──── GND
│              │
└──────────────┘

DHT Sensor (4-pin component - if not using module)
     ┌──┐
     │  │
  ┌──┴──┴──┐
  │ DHT11  │
  │        │
  └─┬──┬──┬┘
    1  2  3  4
    │  │  │  │
    │  │  │  └──── Not connected
    │  │  └──────── GND
    │  └──────────── D4 (GPIO2) ──── [10kΩ resistor to VCC]
    └──────────────── 3.3V

Pin 1: VCC (3.3V)
Pin 2: DATA (to D4 with 10kΩ pull-up resistor to VCC)
Pin 3: Not connected
Pin 4: GND
```

### HC-SR04 Ultrasonic Sensor Connection

```
HC-SR04 Ultrasonic Sensor
┌──────────────┐
│   HC-SR04    │
│              │
│  VCC ────────┼──── 5V (VIN on ESP8266)
│  TRIG ───────┼──── D5 (GPIO14)
│  ECHO ───────┼──── D6 (GPIO12) [Use voltage divider if needed]
│  GND ────────┼──── GND
│              │
└──────────────┘

Important: HC-SR04 ECHO pin outputs 5V logic level.
ESP8266 is 3.3V tolerant, but for safety, use a voltage divider:

ECHO ─┬─[1kΩ]─┬─── D6 (GPIO12)
      │        │
    [2kΩ]    [GND]
      │
    [GND]

Output voltage = 5V × (2kΩ / (1kΩ + 2kΩ)) = 3.33V
```

### Status LED Connection

```
Status LED
         ┌─────┐
 D7 ─────┤ 220Ω├────┬──┤►├──┬─── GND
         └─────┘    │ LED  │
                    │      │
                    └──────┘

D7 (GPIO13) → 220Ω Resistor → LED Anode (+) → LED Cathode (-) → GND
```

## Complete Breadboard Layout

```
                    ESP8266 NodeMCU
                    ┌─────────────────┐
                    │     ┌─────┐     │
                    │     │ USB │     │
                    │     └─────┘     │
                    │                 │
                    │  RST      TX    │
                    │  D0       RX    │
                    │  D5       D1    │─── DHT22 (if using D1 alternative)
                    │  D6       D2    │
                    │  D7       D3    │
 LED+220Ω ──────────│  D8       D4    │─── DHT22 Data
                    │  3V3      GND   │─┬─── GND Rail
                    │  GND      5V    │─┼─── 5V Rail
                    └─────────────────┘ │
                                        │
Power Rails:                            │
[5V ] ─────────────────────────────────┴─┬── MQ-135 VCC
                                          ├── HC-SR04 VCC
                                          └── (from 5V pin)

[GND] ────────────────────────────────────┬── MQ-135 GND
                                           ├── HC-SR04 GND
                                           ├── DHT22 GND
                                           ├── LED GND
                                           └── (from GND pin)

[3.3V] (optional) ─────────────────────────── DHT22 VCC (alternative)


Connections Summary:
A0  ←──── MQ-135 AOUT
D4  ←──── DHT22 Data
D5  ────→ HC-SR04 Trigger
D6  ←──── HC-SR04 Echo (with voltage divider)
D7  ────→ LED (with 220Ω resistor)
```

## Sensor Placement Recommendations

### MQ-135 Air Quality Sensor
- **Location**: Mount at breathing height (1.2-1.5m from floor)
- **Orientation**: Keep sensor grid facing open area
- **Ventilation**: Ensure good air circulation
- **Away from**: Direct sunlight, heaters, air conditioners
- **Warm-up**: Allow 24-48 hours for initial calibration

### DHT11/DHT22 Temperature & Humidity
- **Location**: Away from windows, doors, direct sunlight
- **Height**: 1.5m from floor for ambient readings
- **Away from**: Heat sources, direct airflow from HVAC
- **Ventilation**: Good air circulation but not direct drafts

### HC-SR04 Ultrasonic Sensor (Door Monitoring)
- **Location**: Mounted above or beside door frame
- **Orientation**: Perpendicular to expected movement path
- **Height**: 1.5-2m from floor
- **Range**: Position for 50-200cm detection range
- **Angle**: Sensor has ~15° cone, center on detection area
- **Away from**: Soft/sound-absorbing materials

### Overall ESP8266 Node
- **Power**: Stable 5V power supply
- **WiFi**: Within good WiFi range
- **Enclosure**: Use ventilated case to protect from dust
- **Cable management**: Secure cables to prevent disconnection

## Assembly Instructions

### Step 1: Prepare Components
1. Gather all components listed above
2. Test ESP8266 board with simple blink sketch
3. Verify each sensor individually before integration

### Step 2: MQ-135 Connection
1. Connect VCC to 5V rail
2. Connect GND to ground rail
3. Connect AOUT to A0 pin
4. Power on and wait for sensor to heat (LED indicator will light)

### Step 3: DHT22 Connection
1. Identify pins (VCC, Data, GND)
2. Connect VCC to 3.3V (or 5V)
3. Connect Data to D4 (GPIO2)
4. Connect GND to ground rail
5. If using 4-pin component, add 10kΩ pull-up resistor between Data and VCC

### Step 4: HC-SR04 Connection
1. Connect VCC to 5V rail
2. Connect GND to ground rail
3. Connect Trigger to D5 (GPIO14)
4. Connect Echo to D6 (GPIO12) through voltage divider (optional but recommended)

### Step 5: Status LED
1. Connect anode (+, longer leg) to D7 through 220Ω resistor
2. Connect cathode (-, shorter leg) to ground rail

### Step 6: Power Connections
1. Connect all ground connections to common ground rail
2. Connect 5V devices to 5V rail
3. Connect 5V rail to VIN (or 5V) pin on ESP8266
4. Connect ground rail to GND pin on ESP8266

### Step 7: Final Checks
1. Double-check all connections
2. Ensure no short circuits
3. Verify correct voltage levels
4. Check for loose connections

### Step 8: Testing
1. Upload firmware (see esp8266_firmware/README.md)
2. Open Serial Monitor (115200 baud)
3. Verify sensor readings
4. Check WiFi connection
5. Test data transmission to server

## Enclosure Design

### Requirements
- Ventilated for air quality sensor
- Access to USB port for programming
- Indicator LED visible
- Wall-mountable
- Protection from dust/moisture

### Suggested Materials
- 3D printed case (STL files can be created)
- Plastic project box with ventilation holes
- Custom laser-cut acrylic case

### Ventilation
- Minimum 20% open area for air circulation
- Mesh/screen over openings for dust protection
- Ensure MQ-135 sensor exposed to air

## Power Considerations

### Power Consumption
- ESP8266: ~80mA (active WiFi)
- MQ-135: ~150mA (heating element)
- DHT22: ~1.5mA
- HC-SR04: ~15mA (during measurement)
- **Total: ~250mA @ 5V**

### Power Supply Options
1. **USB Power Adapter** (5V 1A minimum)
   - Recommended: 5V 2A for stability
   - Use quality adapter to avoid noise

2. **Battery Power** (for portable deployment)
   - 5V power bank (10,000mAh = ~40 hours)
   - Add deep sleep mode to firmware for longer life

3. **Solar Power** (for remote locations)
   - 5V solar panel (5W minimum)
   - Battery controller
   - Backup battery

### Power Stability
- Use decoupling capacitor (100µF) across power rails
- Short, thick power cables
- Avoid long cable runs
- Separate noisy components

## Troubleshooting Hardware

### ESP8266 Won't Boot
- Check power supply (minimum 5V 1A)
- Verify USB cable supports data
- Check for short circuits
- Try different USB port

### MQ-135 Always Reads High/Low
- Wait 24-48 hours for calibration
- Check 5V power supply
- Verify analog connection to A0
- Test in different environment

### DHT Sensor Returns NaN
- Check wiring (especially data pin)
- Add/check 10kΩ pull-up resistor
- Use 3.3V instead of 5V
- Try slower reading rate

### Ultrasonic Sensor No Reading
- Check voltage divider on Echo pin
- Verify trigger/echo not swapped
- Ensure clear path (no obstacles)
- Check operating distance (2-400cm)

### WiFi Connection Issues
- Check antenna (built-in, don't cover)
- Verify 2.4GHz network
- Reduce distance to router
- Check for interference

## Safety Warnings

⚠️ **Important Safety Notes:**

1. **Electrical Safety**
   - Never connect/disconnect while powered
   - Check polarity before powering on
   - Use proper voltage levels (3.3V vs 5V)
   - Avoid short circuits

2. **Sensor Safety**
   - MQ-135 gets HOT during operation
   - Keep away from flammable materials
   - Ensure proper ventilation
   - Don't touch during operation

3. **Data Accuracy**
   - Sensors require calibration period
   - Environmental factors affect readings
   - Not certified for medical/safety-critical use
   - Use as monitoring tool, not primary safety device

4. **Power Safety**
   - Use quality power supplies
   - Don't exceed current ratings
   - Avoid long-term battery operation without monitoring
   - Implement over-current protection for permanent installations

## Next Steps

1. ✅ Assemble hardware according to circuit diagram
2. ✅ Test each component individually
3. ✅ Upload firmware from esp8266_firmware directory
4. ✅ Configure WiFi and server settings
5. ✅ Mount in appropriate location
6. ✅ Set up Raspberry Pi server
7. ✅ Test end-to-end data flow
8. ✅ Monitor and calibrate thresholds

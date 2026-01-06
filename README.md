# PiPool 🏊

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Raspberry Pi-based pool automation system** for controlling pump, heater, and lights with real-time monitoring, safety features, and Home Assistant integration.

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [Raspberry Pi Setup](#raspberry-pi-setup)
  - [Software Installation](#software-installation)
  - [Database Setup](#database-setup)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Web Dashboard](#-web-dashboard)
- [MQTT Protocol](#-mqtt-protocol)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Hardware Build](#-hardware-build)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **🔌 Hardware Control**: 8-channel relay board for pump, heater, and light control via GPIO
- **🌡️ Temperature Monitoring**: DS18B20 1-Wire sensors for water and ambient temperature tracking
- **📡 Remote Control**: Full MQTT-based command/control interface with JSON payloads
- **🛡️ Safety Watchdogs**: Automatic heater shutoff if pump stops, network loss, or runtime limits exceeded
- **🏠 Home Assistant Integration**: Native MQTT discovery for seamless smart home integration
- **🖥️ Web Dashboard**: Professional Streamlit-based interface for monitoring and control
- **🧪 Hardware Abstraction**: Run on real hardware or in simulation mode for development/testing
- **📊 Data Logging**: PostgreSQL database for sensor data, events, and device runtime tracking
- **⚡ Real-time Updates**: 1-second control loop with instant MQTT status publishing
- **🎨 Light Control**: Support for Hayward ColorLogic 17-color/show library

---

## 📦 Prerequisites

### Hardware Requirements
- **Raspberry Pi 3 or higher** (tested on RPi 3B+)
- **8-channel relay board** (5V GPIO-controlled, active-LOW)
- **DS18B20 temperature sensors** (1-Wire, waterproof probes recommended)
- **Contactor module** for high-current pump control (relay → contactor → pump)
- **Weather-proof enclosure** for outdoor installation
- See [docs/hardware/Hardware-DIY.md](docs/hardware/Hardware-DIY.md) for detailed build guide

### Software Requirements
- **Raspberry Pi OS** (Desktop or Lite)
- **Python 3.12+**
- **PostgreSQL 13+**
- **Mosquitto MQTT Broker**
- **uv** (Python package manager)

> **Note**: `RPi.GPIO` comes pre-installed on Raspberry Pi OS. For development on non-Pi systems, it's not needed when using simulation mode (`PIPOOL_HARDWARE_MODE=simulated`).

---

## 🚀 Installation

### Raspberry Pi Setup

#### 1. Flash Raspberry Pi OS
Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash Raspberry Pi OS (Desktop or Lite).

#### 2. Initial Configuration
Boot the Raspberry Pi and configure the following (via desktop settings or `raspi-config`):

- **Network**: Configure WiFi credentials
- **Hostname**: Set a descriptive hostname (e.g., `pipool`)
- **Boot Mode**: Set to CLI (headless) or Desktop (with monitor)
- **Interfaces**:
  - ✅ SSH enabled
  - ✅ I2C enabled
  - ✅ 1-Wire enabled
- **Timezone**: Set to your local timezone (e.g., `America/Toronto`)
- **GPIO Access**: Add your user to the `gpio` group:
  ```bash
  sudo adduser $USER gpio
  ```

#### 3. Reboot
```bash
sudo reboot
```

### Software Installation

#### 1. Update System Packages
```bash
sudo apt update
sudo apt upgrade -y
```

#### 2. Install System Dependencies
```bash
# Install core dependencies
sudo apt install -y mosquitto mosquitto-clients postgresql make python3-pip

# Install Python package manager (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

#### 3. Install Python Dependencies
```bash
# Install pip dependencies
pip install pythonping paho-mqtt psycopg2

# Install project dependencies with uv
uv sync
```

#### 4. Configure MQTT Broker (Optional)
To enable timestamped logging, edit `/etc/mosquitto/mosquitto.conf`:
```conf
log_timestamp true
log_timestamp_format %Y-%m-%dT%H:%M:%S
```

Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

### Database Setup

#### 1. Create Database User
```bash
sudo su postgres
createuser pipool -P --interactive
# Enter password: pipool (or your custom password)
# Superuser: y
```

#### 2. Create Database
```bash
psql
CREATE DATABASE pipool;
\q
exit
```

#### 3. Configure PostgreSQL Authentication
Edit `/etc/postgresql/13/main/pg_hba.conf` (version number may vary):

Move the following lines **above** `local all all peer`:
```conf
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL:
```bash
sudo service postgresql restart
```

#### 4. Initialize Database Schema

**For fresh installations**, use `schema.sql` to create all tables at once:
```bash
sudo su postgres
cat schema.sql | psql pipool
exit
```

**For upgrading existing installations**, use Alembic for incremental migrations:
```bash
uv run alembic upgrade head
```

> **Recommendation**: For new users, `schema.sql` is simpler and creates the complete database schema in one step. Alembic is useful when upgrading from older versions or managing schema changes over time.

---

## 🏁 Quick Start

### Development (Any Platform)
Run in **simulation mode** - no physical hardware required:
```bash
PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py
```

### Production (Raspberry Pi)
Run with **real hardware**:
```bash
uv run python src/pipool.py
```

Or use the provided run script:
```bash
./run
```

### Monitor MQTT Messages
```bash
# Monitor sensor data
mosquitto_sub -h localhost -t "pipool/sensors"

# Or use the helper script
./mqtt_listen_to_pipool_sensors

# Monitor ALL topics (debugging)
mosquitto_sub -h localhost -t "#"
```

---

## ⚙️ Configuration

### Configuration Files

| File | Purpose | Version Control |
|------|---------|-----------------|
| `config.json` | Default configuration (committed) | ✅ Tracked |
| `config_custom.json` | Local overrides (production credentials) | ❌ Gitignored |
| `config.sim.json` | Simulation mode settings | ✅ Tracked |
| `config.json.example` | Template for custom configuration | ✅ Tracked |

### Configuration Priority
The system loads configuration in this order (later overrides earlier):
1. `config.json` (defaults)
2. `config_custom.json` (local overrides, if present)

### Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `PIPOOL_HARDWARE_MODE` | `real`, `simulated` | `real` (auto-detects RPi) | Hardware mode selection |

### Example Custom Configuration
Create `config_custom.json` to override defaults:
```json
{
  "database": {
    "host": "192.168.1.100",
    "user": "pipool",
    "password": "your_secure_password"
  },
  "mqttBroker": "192.168.1.50"
}
```

---

## 🌐 Web Dashboard

A professional **Streamlit-based web interface** for monitoring and controlling your pool system remotely.

### Quick Start

```bash
# Navigate to streamlit app
cd streamlit_app

# Install dependencies
uv sync

# Start the dashboard
./run_streamlit.sh
# OR: uv run streamlit run app.py

# Open browser to http://localhost:8501
```

### Custom MQTT Broker
```bash
MQTT_BROKER_HOST=192.168.1.100 streamlit run app.py
```

### Dashboard Features

- **📊 Real-time Monitoring**: 4 temperature sensors with live graphs
- **🎛️ Device Control**: Pump, heater, and light controls
- **⏱️ Pump Timer**: Run pump for 1-480 minutes
- **🔥 Smart Heating**: Heat to target temperature (20-40°C)
- **💡 Light Colors**: 17 Hayward ColorLogic colors/shows
- **🛡️ Safety**: Heater-pump interlock, temperature warnings

See [streamlit_app/README.md](streamlit_app/README.md) for detailed documentation.

---

## 📡 MQTT Protocol

### Topics

| Topic | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `pipool/sensors` | Publish | JSON | Sensor readings (temperatures, states) |
| `pipool/status` | Publish | `"online"` | Online status (LWT) |
| `pipool/control/pump_state` | Subscribe | `"ON"` / `"OFF"` | Set pump state |
| `pipool/control/heater_state` | Subscribe | `"ON"` / `"OFF"` | Set heater state |
| `pipool/control/light_state` | Subscribe | `"ON"` / `"OFF"` | Set light state |
| `pipool/control/pump_run_for_x_minutes` | Subscribe | JSON: `{"minutes": 60}` | Timed pump run |
| `pipool/control/heater_reach_and_stop` | Subscribe | JSON: `{"target": 28}` | Heat to target temp |
| `pipool/control/light_set_color` | Subscribe | `"0"` - `"16"` | Set light color index |

### Example Sensor Payload
```json
{
  "pool_temp": 24.5,
  "ambient_temp": 18.2,
  "pump_state": "ON",
  "heater_state": "OFF",
  "light_state": "OFF",
  "timestamp": "2026-01-06T12:34:56"
}
```

For complete MQTT protocol documentation, see [docs/research/mqtt-protocol-analysis-2025-12-27.md](docs/research/mqtt-protocol-analysis-2025-12-27.md).

---

## 🏗️ Architecture

### Directory Structure
```
pi-pool/
├── src/                    # All Python source code
│   ├── pipool.py           # Main entry point - orchestrates all components
│   ├── hal/                # Hardware Abstraction Layer
│   │   ├── interfaces/     # Abstract hardware interfaces
│   │   ├── real/           # RPi.GPIO, gpiozero wrappers
│   │   └── simulated/      # Mock implementations for testing
│   ├── Pump.py             # Pool pump control with timer and modes
│   ├── Heater.py           # Heater control with safety checks (requires pump)
│   ├── Light.py            # Pool light control
│   ├── Thermometer.py      # 1-Wire temperature sensor reader
│   ├── MessageBus.py       # MQTT client - subscribes/publishes
│   ├── Watchdog.py         # Safety monitoring (heater-pump interlock)
│   ├── DB.py               # PostgreSQL database singleton
│   └── Config.py           # Configuration loader singleton
├── tests/                  # Pytest test suite
│   ├── unit/              # Unit tests for components
│   ├── safety/            # Safety-critical tests
│   ├── integration/       # Integration tests
│   └── e2e/              # End-to-end tests
├── streamlit_app/         # Web dashboard
├── alembic/               # Database migrations
├── docs/                  # Documentation
│   ├── hardware/         # Hardware build guides
│   ├── HAL_SUMMARY.md    # Hardware abstraction overview
│   └── research/         # Technical research docs
├── config.json            # Default configuration
├── schema.sql             # PostgreSQL database schema
├── pyproject.toml         # Python project configuration (uv)
└── Makefile              # Common tasks (test, migrate, dev)
```

### System Flow
```
┌─────────────┐
│   pipool.py │  ← Main loop (1s interval)
└─────┬───────┘
      │
      ├──→ MessageBus (MQTT) ──→ Home Assistant / Web Dashboard
      │
      ├──→ Pump ──→ RelayBlock ──→ GPIO ──→ Contactor ──→ Pool Pump
      │
      ├──→ Heater ──→ RelayBlock ──→ GPIO ──→ Pool Heater
      │
      ├──→ Light ──→ RelayBlock ──→ GPIO ──→ Pool Light
      │
      ├──→ Thermometer ──→ 1-Wire ──→ DS18B20 Sensors
      │
      ├──→ Watchdog ──→ Safety Checks (heater-pump interlock)
      │
      └──→ DB (PostgreSQL) ──→ Sensor logs, events, runtime tracking
```

### Hardware Abstraction Layer (HAL)
The HAL enables development without physical hardware:
- **Interfaces**: Abstract hardware contracts (`IGPIOPin`, `ITemperatureSensor`)
- **Real**: Production implementations using `RPi.GPIO`, `gpiozero`
- **Simulated**: Mock implementations with state tracking and logging
- **Auto-detection**: `HardwareFactory` selects real/simulated based on environment

See [docs/HAL_SUMMARY.md](docs/HAL_SUMMARY.md) for detailed documentation.

---

## 🧪 Testing

PiPool includes a **comprehensive pytest test suite** with unit, safety, integration, and end-to-end tests.

### Run All Tests
```bash
make test
# OR
uv run pytest
```

### Run Specific Test Categories
```bash
uv run pytest tests/safety/      # Safety-critical tests only
uv run pytest tests/unit/        # Unit tests only
uv run pytest tests/integration/ # Integration tests only
uv run pytest tests/e2e/         # End-to-end tests only
```

### Test Coverage
```bash
uv run pytest --cov=src --cov-report=html
```

### Testing in Simulation Mode
All tests run in **simulation mode** by default (no hardware required):
```bash
PIPOOL_HARDWARE_MODE=simulated uv run pytest
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | **Developer guide** - coding standards, architecture, workflows |
| [docs/HAL_SUMMARY.md](docs/HAL_SUMMARY.md) | Hardware Abstraction Layer overview |
| [docs/HOMEASSISTANT.md](docs/HOMEASSISTANT.md) | Home Assistant integration guide |
| [docs/hardware/Hardware-DIY.md](docs/hardware/Hardware-DIY.md) | DIY hardware build guide |
| [docs/research/mqtt-protocol-analysis-2025-12-27.md](docs/research/mqtt-protocol-analysis-2025-12-27.md) | Complete MQTT protocol reference |
| [streamlit_app/README.md](streamlit_app/README.md) | Web dashboard documentation |

---

## 🔧 Hardware Build

This system requires a **DIY hardware build** consisting of:

### Components
- ✅ **Raspberry Pi 3+** (RPi 3B+ or higher recommended)
- ✅ **8-channel relay board** (5V, active-LOW, GPIO-controlled)
- ✅ **DS18B20 temperature sensors** (1-Wire, waterproof probes)
- ✅ **Contactor module** for high-current pump control
- ✅ **Weather-proof enclosure** for outdoor installation
- ✅ **Power supply** (5V for Raspberry Pi, appropriate voltage for relays/contactor)
- ✅ **Wiring and connectors** (terminal blocks, heat shrink, etc.)

### Build Guide
See [docs/hardware/Hardware-DIY.md](docs/hardware/Hardware-DIY.md) for detailed build instructions, wiring diagrams, and safety considerations.

⚠️ **WARNING**: This system controls high-voltage pool equipment. Improper installation can cause:
- Equipment damage
- Electric shock
- Fire hazard
- Drowning risk (malfunctioning heater/pump)

**Always consult a licensed electrician** for high-voltage connections and follow local electrical codes.

---

## 🤝 Contributing

### Development Workflow
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pi-pool
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Run in simulation mode**:
   ```bash
   PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py
   ```

5. **Make changes and test**:
   ```bash
   uv run pytest
   ```

6. **Commit with conventional commits**:
   ```bash
   git commit -m "feat: add new feature"
   # OR
   git commit -m "fix: resolve bug in heater control"
   ```

7. **Push and create a pull request**

### Coding Standards
- Follow **PEP 8** style guide
- Use **camelCase** for methods/variables, **PascalCase** for classes
- Write **tests** for new features (especially safety-critical code)
- Use **logging** module (never `print()`)
- Implement **hardStop()** for any new controllable device
- **Never commit** `config_custom.json` or `debug.log`

See [CLAUDE.md](CLAUDE.md) for complete development guidelines.

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

This is a personal project for pool automation. Use at your own risk. No warranty is provided for safety, reliability, or fitness for any purpose.

---

## 🙏 Acknowledgments

- Built with [Python](https://www.python.org/), [Paho MQTT](https://www.eclipse.org/paho/), [PostgreSQL](https://www.postgresql.org/), and [Streamlit](https://streamlit.io/)
- Designed for [Home Assistant](https://www.home-assistant.io/) integration
- Hardware abstraction inspired by modern embedded development practices

---

**Made with ❤️ for smarter pool automation**

# CLAUDE.md - Operating Manual for Claude Code

## Project Overview

PiPool is a Raspberry Pi-based pool automation system that controls pool pump, heater, and lights via GPIO relay blocks. It uses MQTT for real-time messaging and command/control, PostgreSQL for sensor data logging and event tracking, and 1-Wire temperature sensors for water temperature monitoring. The system runs as a single Python process in an infinite loop with 1-second intervals, implementing safety watchdogs to prevent dangerous conditions (e.g., heater running without pump).

This is embedded/IoT software designed to run on a Raspberry Pi with physical hardware connections. It is safety-critical: incorrect operation can damage pool equipment or create hazards.

## Recent Improvements (Last 30 Days)

The project has undergone significant enhancements to improve safety, testability, and developer experience:

- **🔒 Safety Enhancements**: Multiple critical safety fixes implemented including dual-locking for heater-pump race conditions, configurable heater runtime limits, and improved sensor error handling
- **🧪 Testing Infrastructure**: Comprehensive pytest test suite with unit, safety, integration, and e2e tests
- **🔧 Hardware Abstraction Layer (HAL)**: Full HAL implementation enabling development without physical hardware via simulation mode
- **📦 Dependency Management**: Migration to `uv` for modern Python dependency management with `pyproject.toml`
- **🗄️ Database Migrations**: Alembic integration for database schema versioning and migrations
- **🌐 Web Dashboard**: Streamlit-based web interface for remote pool monitoring and control
- **🏠 Home Assistant Integration**: Complete MQTT-based integration guide for Home Assistant
- **📚 Documentation**: Comprehensive documentation including hardware build guides, HAL diagrams, and coding guidelines
- **🔍 Code Quality**: Removal of issue tracker references from code, standardized comment practices

## Quickstart Commands

```bash
# Run the main application (uses uv for dependency management)
uv run python src/pipool.py

# Run in simulation mode (no hardware required)
PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py

# Legacy: Run without HAL simulation (deprecated)
NO_DEVICES=1 uv run python src/pipool.py

# Monitor MQTT sensor messages
./mqtt_listen_to_pipool_sensors
# OR
mosquitto_sub -h localhost -t "pipool/sensors"

# Monitor all MQTT messages
mosquitto_sub -h localhost -t "#"

# Initialize database schema (run as postgres user)
su postgres
cat schema.sql | psql pipool
```

**Required system packages** (install on Raspberry Pi):
```bash
apt install pip mosquitto mosquitto-clients postgresql
pip install pythonping paho-mqtt psycopg2
```

## Architecture & Key Directories

```
pi-pool/
├── src/                    # All Python source code
│   ├── pipool.py           # Main entry point - orchestrates all components
│   ├── Config.py           # Singleton configuration loader (JSON-based)
│   ├── MessageBus.py       # MQTT client - subscribes to control topics, publishes status
│   ├── Pump.py             # Pool pump control with timer and modes
│   ├── Heater.py           # Heater control with safety checks (requires pump)
│   ├── Light.py            # Pool light control
│   ├── LightColorLogic.py  # Light color cycling logic
│   ├── RelayBlock.py       # GPIO relay interface (8-channel relay board)
│   ├── Sensor.py/Sensors.py # Sensor abstraction and collection
│   ├── Thermometer.py      # 1-Wire temperature sensor reader
│   ├── RpiTemperature.py   # Raspberry Pi CPU temperature reader
│   ├── DB.py               # PostgreSQL database singleton
│   ├── Event.py            # Event logging to database
│   ├── Timer.py            # Runtime tracking for devices
│   ├── Pinger.py           # Network connectivity monitor
│   ├── Watchdog.py         # Safety watchdog (stops heater if pump off)
│   ├── Automations.py      # High-level automation commands
│   ├── *State.py/*Mode.py  # Enum definitions for device states/modes
│   ├── hal/                # Hardware Abstraction Layer (HAL)
│   │   ├── interfaces/     # Abstract hardware interfaces
│   │   ├── real/           # Real hardware implementations (RPi.GPIO)
│   │   ├── simulated/      # Simulated hardware for testing
│   │   └── HardwareFactory.py # Factory for creating hardware instances
│   └── db/                 # Database models and migrations
├── tests/                  # Pytest test suite
│   ├── unit/              # Unit tests for components
│   ├── safety/            # Safety-critical tests
│   ├── integration/       # Integration tests
│   └── e2e/              # End-to-end tests
├── streamlit_app/         # Web dashboard for pool control
├── alembic/               # Database migrations (Alembic)
├── docs/                  # Documentation
│   ├── HAL_*.md          # Hardware Abstraction Layer docs
│   ├── HOMEASSISTANT.md  # Home Assistant integration guide
│   └── hardware/         # Hardware build documentation
├── config.json            # Default configuration (committed)
├── config_custom.json     # Local overrides (gitignored)
├── config*.json.example   # Configuration templates
├── schema.sql             # PostgreSQL database schema
├── pyproject.toml         # Python project configuration (uv)
├── Makefile              # Common tasks (test, migrate, dev)
├── run                    # Shell script to start the application
└── mqtt_listen_to_pipool_sensors  # Helper script to monitor MQTT
```

## Coding Standards

### Naming Conventions
- **Classes**: PascalCase (`Pump`, `MessageBus`, `LightColorLogic`)
- **Files**: PascalCase matching class name (`Pump.py`, `MessageBus.py`)
- **Methods**: camelCase (`runOneLoop`, `setStateMessageHandler`)
- **Variables**: camelCase (`inputTemp`, `relayBlockPort`)
- **Constants**: UPPER_SNAKE_CASE (`MQTT_STATUS_TOPIC`)
- **Enums**: PascalCase class, UPPER_SNAKE_CASE members (`PumpState.ON`)

### Architecture Patterns
- **Singletons**: `Config`, `DB` use singleton pattern with `getInstance()` static method
- **Message handlers**: Methods named `*MessageHandler` receive MQTT payload as string
- **State machines**: Devices have `state` (ON/OFF) and `mode` (operational mode)
- **Main loop**: All devices implement `runOneLoop()` called every iteration

### Error Handling
- Use `logging` module (not print statements)
- Log levels: `logging.info()` for normal operations, `logging.error()` for failures
- Safety-critical errors trigger `hardStop()` on affected devices
- Database operations use try/except with rollback on failure

### Logging Format
```python
logging.info("ComponentName: Action - details")
logging.error(f"ComponentName: Error description: {e}", exc_info=True)
```

### GPIO / Hardware
- GPIO uses BCM numbering mode (`GPIO.setmode(GPIO.BCM)`)
- Relays are active-LOW (GPIO.LOW = relay ON)
- Always use `RelayBlock` abstraction, never direct GPIO in device classes
- **Hardware Abstraction Layer (HAL)**: All hardware access goes through HAL interfaces
  - `src/hal/interfaces/` - Abstract interfaces for hardware
  - `src/hal/real/` - Real hardware implementations using RPi.GPIO
  - `src/hal/simulated/` - Simulated hardware for testing/development
  - `HardwareFactory` automatically selects implementation based on `PIPOOL_HARDWARE_MODE`
- Support `PIPOOL_HARDWARE_MODE=simulated` for development without hardware
- Legacy: `NO_DEVICES=1` environment variable (deprecated, use HAL simulation)

### MQTT Topics
- Status published to: `pipool/status`, `pipool/sensors`
- Control subscriptions: `pipool/control/{device}_{action}`
- Payload is typically a string (`"ON"`, `"OFF"`) or JSON

### Database
- All timestamps use PostgreSQL `NOW()` default (server time)
- Use context managers (`with self.conn.cursor() as cur:`) for cursors
- Always commit after successful operations, rollback on failure

## Testing Standards

**Comprehensive pytest test suite is available** in the `tests/` directory.

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── safety/         # Safety-critical tests (race conditions, heater runtime, watchdog)
├── integration/    # Integration tests (automations, database)
└── e2e/           # End-to-end tests
```

### Running Tests
```bash
# Run all tests
make test
# OR
uv run pytest

# Run specific test categories
uv run pytest tests/safety/     # Safety-critical tests only
uv run pytest tests/unit/       # Unit tests only
uv run pytest tests/integration/ # Integration tests only
```

### Before Submitting Changes
1. Run full test suite: `make test` or `uv run pytest`
2. Verify hardware compatibility: `PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py`
3. Check logs for unexpected errors
4. Verify MQTT message handling if touching MessageBus
5. Test on actual Raspberry Pi hardware for GPIO/sensor changes

## Dependency & Build Rules

### Dependencies (managed with uv)
PiPool uses **uv** for dependency management. All dependencies are defined in `pyproject.toml`.

**Core Dependencies:**
- `paho-mqtt>=2.1.0` - MQTT client library
- `psycopg2>=2.9.11` - PostgreSQL adapter
- `pythonping>=1.1.4` - Network ping utility
- `alembic>=1.17.2` - Database migrations
- `sqlalchemy>=2.0.0` - ORM for database operations
- `pytest>=9.0.2` - Testing framework

**Optional Dependencies:**
- `test` - Comprehensive pytest testing suite with coverage, mocking, and reporting tools

**Hardware Dependencies (on Raspberry Pi):**
- `RPi.GPIO` - Raspberry Pi GPIO (pre-installed on Raspberry Pi OS, not in pyproject.toml)

### Python Version
- Python 3.12+ (specified in pyproject.toml: `requires-python = ">=3.12"`)

### Configuration Files
- `config.json` - Default configuration (committed to repo)
- `config_custom.json` - Local overrides (gitignored, takes precedence)
- `config.json.example` - Template for custom configuration setup
- `config.sim.json` - Simulation mode configuration
- `config.sim.json.example` - Template for simulation mode setup

### Environment Variables
- `PIPOOL_HARDWARE_MODE=simulated` - Run in simulation mode (no GPIO hardware required)
- `NO_DEVICES=1` - Legacy flag to run without GPIO hardware (deprecated, use HAL simulation)

## Git & PR Workflow

### Branching
- `main` branch is the primary branch
- Create feature branches for changes: `feature/description` or `fix/description`

### Commit Messages
- Use imperative mood: "Add heater safety check", not "Added heater safety check"
- Prefix with component if specific: "Heater: Add pump dependency check"

### Before Committing
1. Verify no syntax errors: `uv run python -m py_compile src/*.py`
2. Verify imports work: `PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py` (let it start, then Ctrl+C)
3. Do not commit `config_custom.json` or `debug.log`

## Security & Secrets

### Never Commit
- `config_custom.json` - Contains local/production database credentials
- `debug.log` - May contain sensitive operational data
- Any `.env` files
- Database passwords in plain text (use config_custom.json)

### Credentials Handling
- Database credentials in `config.json` are defaults for development
- Production credentials should be in `config_custom.json` (gitignored)
- MQTT broker address is configurable via `mqttBroker` in config.json

### GPIO Security
- Application requires GPIO access (user must be in `gpio` group)
- Runs as root in production for hardware access (see `run` script)

## "When Editing Code" Checklist

- [ ] Does this change affect safety-critical code (Heater, Pump, Watchdog)?
- [ ] If adding new device control, is there a hardStop() method?
- [ ] Is the new code compatible with `PIPOOL_HARDWARE_MODE=simulated`?
- [ ] Are database operations wrapped in try/except with rollback?
- [ ] Does logging follow the project format?
- [ ] If adding MQTT handlers, is the subscription added in `addSubscriptions()`?
- [ ] If touching GPIO, does it use HAL abstraction (not direct GPIO)?
- [ ] Is the singleton pattern preserved for Config/DB classes?
- [ ] Are state changes logged via `Event.logStateEvent()` or `Event.logOpaqueEvent()`?
- [ ] Have you added/updated tests in the appropriate test directory?
- [ ] Does the code work in both real and simulated hardware modes?
- [ ] Are there no issue tracker references in code comments (e.g., CRITICAL-1, JIRA-123)?

## Do / Don't

### Do
- Use `logging` module for all output
- Implement `hardStop()` for any new controllable device
- Use `RelayBlock` for all GPIO relay operations
- Validate sensor readings before acting on them
- Test with `PIPOOL_HARDWARE_MODE=simulated` before deploying
- Keep the main loop fast (< 1 second per iteration)
- Log state transitions for debugging

### Don't
- Never run heater without pump running (safety hazard)
- Never use `print()` - use `logging` instead
- Never commit database credentials to config.json
- Never access GPIO directly outside RelayBlock
- Never block the main loop with long-running operations
- Never ignore exceptions in safety-critical code paths
- Never hardcode IP addresses (use config.json)
- Never put issue tracker references in code comments (e.g., `CRITICAL-1`, `JIRA-123`, `#456`)
  - Comments should describe *what* and *why*, not reference external trackers
  - Bad: `# CRITICAL-1: Fix race condition`
  - Good: `# Acquire state lock to prevent race conditions with heater`

# CLAUDE.md - Operating Manual for Claude Code

## Project Context

Safety-critical embedded/IoT system. Controls pool pump, heater, and lights via GPIO relay blocks on a Raspberry Pi. Incorrect operation can damage equipment or create hazards. Single Python process, 1-second main loop, MQTT messaging, PostgreSQL logging.

## Commands

Use `make` targets for common tasks (see `Makefile`). Key non-make commands:

```bash
PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py  # run without hardware
uv run python -m py_compile src/*.py                        # syntax check before commit
```

## Source Layout

```
src/
  pipool.py           # main entry point, orchestrates all components
  hal/
    interfaces/       # abstract hardware interfaces (IGPIOPin, etc.)
    real/             # RPi.GPIO production implementations
    simulated/        # mock implementations for dev/test
    HardwareFactory.py
  Config.py, DB.py    # singletons (getInstance())
  Pump.py, Heater.py, Light.py, Watchdog.py  # device control
  MessageBus.py       # MQTT subscribe/publish
  RelayBlock.py       # only GPIO interface device classes may use
  *State.py, *Mode.py # enums for device states/modes
  db/                 # SQLAlchemy models and Alembic migrations
tests/
  unit/ safety/ integration/ e2e/
```

## Coding Standards

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Classes / Files | PascalCase | `Pump`, `MessageBus.py` |
| Methods / Variables | camelCase | `runOneLoop`, `inputTemp` |
| Constants | UPPER_SNAKE_CASE | `MQTT_STATUS_TOPIC` |
| Enum members | UPPER_SNAKE_CASE | `PumpState.ON` |

### Architecture Patterns

- **Singletons**: `Config`, `DB` — always access via `getInstance()`
- **Main loop**: every device implements `runOneLoop()` called each iteration; keep it fast (< 1 s total)
- **Message handlers**: named `*MessageHandler`, receive MQTT payload as `str`
- **State/mode split**: devices have `state` (ON/OFF) and `mode` (operational mode enum)
- **New device control**: must implement `hardStop()`

### Logging

```python
logging.info("ComponentName: Action - details")
logging.error(f"ComponentName: Error description: {e}", exc_info=True)
```

Use `logging` module only — never `print()`. Log all state transitions.

### GPIO / HAL

- All hardware access goes through `src/hal/` interfaces — never call RPi.GPIO directly in device classes
- All GPIO relay access goes through `RelayBlock` — never raw GPIO in `Pump`, `Heater`, `Light`, etc.
- Relays are active-LOW (`GPIO.LOW` = relay ON), BCM numbering
- `HardwareFactory` selects real vs. simulated based on `PIPOOL_HARDWARE_MODE`
- Always support `PIPOOL_HARDWARE_MODE=simulated`; `NO_DEVICES=1` is deprecated

### MQTT Topics

| Direction | Topic | Payload |
|-----------|-------|---------|
| Publish | `pipool/status` | `"online"` |
| Publish | `pipool/sensors` | JSON |
| Subscribe | `pipool/control/{device}_{action}` | `"ON"` / `"OFF"` or JSON |

New subscriptions must be registered in `addSubscriptions()`.

### Database

- Timestamps: PostgreSQL `NOW()` default (server time)
- Cursors: `with self.conn.cursor() as cur:`
- Always commit on success, rollback on failure; wrap in try/except

## Testing

```bash
make test                          # all tests
uv run pytest tests/safety/        # safety-critical only (run after touching Heater/Pump/Watchdog)
uv run pytest tests/unit/
uv run pytest tests/integration/
```

## Configuration & Secrets

- `config.json` — committed defaults
- `config_custom.json` — local overrides, gitignored, takes precedence; contains production credentials
- Never commit `config_custom.json`, `debug.log`, or `.env` files
- No hardcoded IPs or passwords; use `config.json` keys

## Git Conventions

- Branch names: `feature/description` or `fix/description`
- Commit messages: imperative mood, component-prefixed when specific
  - `Heater: Add pump dependency check`
  - `fix: resolve race condition in async handler`

## Pre-Commit Checklist

- [ ] Safety-critical code touched (Heater, Pump, Watchdog)? Run `uv run pytest tests/safety/`
- [ ] New device control has `hardStop()`?
- [ ] Works with `PIPOOL_HARDWARE_MODE=simulated`?
- [ ] Database ops wrapped in try/except with rollback?
- [ ] Logging follows project format (no `print()`)?
- [ ] New MQTT handlers registered in `addSubscriptions()`?
- [ ] GPIO access only via HAL/RelayBlock?
- [ ] Singletons (`Config`, `DB`) accessed via `getInstance()`?
- [ ] State changes logged via `Event.logStateEvent()` or `Event.logOpaqueEvent()`?
- [ ] No issue tracker references in comments (e.g., `CRITICAL-1`, `JIRA-123`) — describe *what/why* instead
- [ ] Syntax check: `uv run python -m py_compile src/*.py`

## Safety Rules (Non-Negotiable)

- Never run heater without pump running
- Never block the main loop with long-running operations
- Never ignore exceptions in safety-critical code paths
- Never bypass HAL or access GPIO directly outside `RelayBlock`

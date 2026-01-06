# PiPool Documentation

## Overview

This directory contains comprehensive documentation for the PiPool project.

## Documentation Files

### SQLAlchemy & Database

- **[SQLALCHEMY_QUICKSTART.md](SQLALCHEMY_QUICKSTART.md)** - Quick start guide for database migrations
  - Installation and setup
  - Common tasks (migrate, create migrations, etc.)
  - Usage examples
  - Troubleshooting

- **[SQLALCHEMY_MIGRATION.md](SQLALCHEMY_MIGRATION.md)** - Comprehensive migration guide
  - Architecture overview
  - Package structure details
  - Migration workflows
  - Advanced usage

- **[SQLALCHEMY_IMPLEMENTATION_SUMMARY.md](SQLALCHEMY_IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
  - All files created/modified
  - Architecture decisions
  - Testing results
  - Benefits and next steps

### Project Analysis

- **[PROJECT_CRITIQUE.md](PROJECT_CRITIQUE.md)** - Project analysis and recommendations
  - Code quality assessment
  - Architectural patterns
  - Improvement suggestions

## Quick Start

### For New Users

1. Read [SQLALCHEMY_QUICKSTART.md](SQLALCHEMY_QUICKSTART.md) for database setup
2. For existing database: `make migrate-stamp`
3. For new database: `make migrate`

### For Developers

1. Review [SQLALCHEMY_MIGRATION.md](SQLALCHEMY_MIGRATION.md) for architecture
2. Check [SQLALCHEMY_IMPLEMENTATION_SUMMARY.md](SQLALCHEMY_IMPLEMENTATION_SUMMARY.md) for implementation details
3. See main [CLAUDE.md](../CLAUDE.md) for project conventions

## Database Migrations

The project uses SQLAlchemy ORM with Alembic for migrations:

```bash
# Common commands
make migrate              # Run pending migrations
make migrate-status       # Check current version
make migrate-new MSG="description"  # Create new migration
make help                 # Show all commands
```

See [SQLALCHEMY_QUICKSTART.md](SQLALCHEMY_QUICKSTART.md) for details.

## Key Features

- **SQLAlchemy 2.0**: Modern ORM with type safety
- **Alembic Migrations**: Version-controlled schema changes
- **Backward Compatible**: Zero breaking changes to existing code
- **Connection Pooling**: Automatic via SQLAlchemy
- **Safe Migrations**: Initial migration safe for existing databases

## Contributing

When making changes:

1. Follow naming conventions (PascalCase classes, camelCase methods)
2. Update models in `src/db/models/`
3. Generate migration: `make migrate-new MSG="description"`
4. Test migration on dev database
5. Commit migration file with code changes

## Testing

```bash
# Test SQLAlchemy implementation
PIPOOL_HARDWARE_MODE=simulated uv run python test_sqlalchemy.py

# Test application startup
PIPOOL_HARDWARE_MODE=simulated uv run python src/pipool.py
```

## Help

For questions or issues:
- Check [SQLALCHEMY_QUICKSTART.md](SQLALCHEMY_QUICKSTART.md) troubleshooting section
- Review [SQLALCHEMY_MIGRATION.md](SQLALCHEMY_MIGRATION.md) for detailed info
- See main [CLAUDE.md](../CLAUDE.md) for project guidelines

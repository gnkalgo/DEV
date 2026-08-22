TimescaleDB is enabled by the `timescale/timescaledb` image.

Alembic Phase 2 creates OLTP tables and hypertables (`0002_phase2_oltp`, `0003_phase2_timescale`). Do not publish this service to the public internet in production.

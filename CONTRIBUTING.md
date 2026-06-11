# Contributing

Read `documentation/19_code_style_and_contribution.md` before making changes.

## Testing note: loggers and `caplog`

Infrastructure loggers created via `iva.infrastructure.logging.app_logger.get_logger`
set `propagate = False`, so pytest's `caplog` fixture (which attaches to the
root logger) will not capture their records. To assert on these log messages,
patch the module-level `logger` object with `unittest.mock.patch` and inspect
the mock's calls instead of relying on `caplog`.

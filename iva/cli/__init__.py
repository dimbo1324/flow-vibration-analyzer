"""CLI entry point package for the Industrial Vibration Analyzer.

Run the analyzer from the command line::

    python -m iva.cli.main analyze --data path/to/data.csv \\
        --config config/example_config.json --output reports/run_001

Architecture rule: this package must NOT import from ``iva.ui`` or ``PySide6``.
"""

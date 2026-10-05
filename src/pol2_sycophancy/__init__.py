"""Third-Party Condition Test for Sycophancy: data selection, answer generation and validation.

Modules
-------
env_load         explicit .env loading and secret redaction
select_records   cluster-aware sampling of the Perez et al. (2022) sycophancy data
generate         paired answer generation (aligned / opposed) with budget caps
validate_answers format, length-ratio and refusal checks on frozen answers
"""

__version__ = "0.2.0"

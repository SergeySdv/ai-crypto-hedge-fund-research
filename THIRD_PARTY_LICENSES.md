# Third-Party License Inventory

Generated for Stage 13 release audit from the locked `uv` environment on
2026-06-21. This inventory summarizes package metadata exposed by installed
distributions; it is not legal advice. Re-check license metadata before any
commercial or institutional reuse.

The project source code is MIT licensed. The default reproducible run uses the
packages locked in `uv.lock`; no external LLM service, exchange credentials, or paid
data service is required.

## Installed Dependencies

| Package | Version | License metadata |
| --- | ---: | --- |
| aiodns | 4.0.4 | MIT |
| aiohappyeyeballs | 2.6.2 | Python Software Foundation License |
| aiohttp | 3.14.1 | Apache-2.0 AND MIT |
| aiosignal | 1.4.0 | Apache Software License |
| annotated-types | 0.7.0 | MIT License |
| arch | 8.0.0 | NCSA |
| attrs | 26.1.0 | MIT |
| beautifulsoup4 | 4.15.0 | MIT License |
| bleach | 6.4.0 | Apache Software License |
| ccxt | 4.5.59 | MIT License |
| certifi | 2026.6.17 | Mozilla Public License 2.0 (MPL 2.0) |
| cffi | 2.0.0 | MIT |
| charset-normalizer | 3.4.7 | MIT |
| coincurve | 21.0.0 | MIT OR Apache-2.0 |
| contourpy | 1.3.3 | BSD License |
| cryptography | 49.0.0 | Apache-2.0 OR BSD-3-Clause |
| cycler | 0.12.1 | BSD License |
| defusedxml | 0.7.1 | Python Software Foundation License |
| fastjsonschema | 2.21.2 | BSD License |
| fonttools | 4.63.0 | MIT |
| frozenlist | 1.8.0 | Apache-2.0 |
| idna | 3.18 | BSD-3-Clause |
| iniconfig | 2.3.0 | MIT |
| Jinja2 | 3.1.6 | BSD License |
| joblib | 1.5.3 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| jupyter_client | 8.9.1 | BSD License |
| jupyter_core | 5.9.1 | BSD-3-Clause |
| jupyterlab_pygments | 0.3.0 | BSD License |
| kiwisolver | 1.5.0 | BSD License |
| MarkupSafe | 3.0.3 | BSD-3-Clause |
| matplotlib | 3.11.0 | Matplotlib license, BSD-style |
| mistune | 3.2.1 | BSD License |
| multidict | 6.7.1 | Apache License 2.0 |
| narwhals | 2.22.1 | MIT |
| nbclient | 0.11.0 | BSD License |
| nbconvert | 7.17.1 | BSD License |
| nbformat | 5.10.4 | BSD License |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| packaging | 26.2 | Apache-2.0 OR BSD-2-Clause |
| pandas | 3.0.3 | BSD License |
| pandocfilters | 1.5.1 | BSD License |
| patsy | 1.0.2 | BSD License |
| pillow | 12.2.0 | MIT-CMU |
| platformdirs | 4.10.0 | MIT |
| pluggy | 1.6.0 | MIT License |
| propcache | 0.5.2 | Apache Software License |
| pyarrow | 24.0.0 | Apache-2.0 |
| pycares | 5.0.1 | MIT |
| pycparser | 3.0 | BSD-3-Clause |
| pydantic | 2.13.4 | MIT |
| pydantic_core | 2.46.4 | MIT |
| Pygments | 2.20.0 | BSD-2-Clause |
| pyparsing | 3.3.2 | MIT |
| pytest | 9.1.1 | MIT |
| python-dateutil | 2.9.0.post0 | BSD License; Apache Software License |
| PyYAML | 6.0.3 | MIT License |
| pyzmq | 27.1.0 | BSD License |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache Software License |
| rpds-py | 2026.5.1 | MIT |
| ruff | 0.15.18 | MIT |
| scikit-learn | 1.9.0 | BSD-3-Clause |
| scipy | 1.17.1 | BSD License |
| setuptools | 82.0.1 | MIT |
| six | 1.17.0 | MIT License |
| soupsieve | 2.8.4 | MIT |
| statsmodels | 0.14.6 | BSD License |
| threadpoolctl | 3.6.0 | BSD License |
| tinycss2 | 1.5.1 | BSD License |
| tornado | 6.5.7 | Apache Software License |
| traitlets | 5.15.1 | BSD License |
| typing-inspection | 0.4.2 | MIT |
| typing_extensions | 4.15.0 | PSF-2.0 |
| urllib3 | 2.7.0 | MIT |
| webencodings | 0.5.1 | BSD License |
| yarl | 1.24.2 | Apache-2.0 |

## Reference Projects

See `docs/07_LIMITATIONS_AND_ATTRIBUTION.md` for non-dependency references and
copying constraints. In particular:

- `denisalpino/autofin` was treated as conceptual reading only because it is all
  rights reserved at the time of review.
- Freqtrade/FreqAI was treated as GPL-3.0 reference material only, not as a linked
  project dependency.
- CCXT is used for the optional public market-data downloader path; the default
  release run reads frozen Parquet files.

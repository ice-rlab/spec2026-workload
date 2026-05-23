SPEC CPU 2026 Workload
======================

Requirements
------------

- SPEC CPU 2026 installed with the `SPEC_26_DIR` environment variable pointing to the installation

Getting Started
---------------

When you first install this repository, update all submodules:

    git submodule update --init --recursive spec2026

After that, use FireMarshal as normal and point to the `json` workload configs:

    # Assuming marshal is on your $PATH
    marshal build ./marshal-configs/spec26-intrate.json

See https://firemarshal.readthedocs.io/en/latest/index.html for FireMarshal
documentation.
# Cowan Runner

WARNING:
The Cowan code must be obtained separately.
This tool only automates execution and parsing.


Python automation tool for running the Cowan atomic structure code
and parsing results (Slater integrals, spin–orbit constants) for a given atomic configuration and respective XAS final state

This project does NOT include the Cowan code itself.

------------------------------------------------------------

## Installation

Install directly from GitHub:

    pip install git+https://github.com/miguemcarvalhojr-cmd/cowan-runner.git

Requirements:

- Python >= 3.8
- Cowan executables available in PATH:
    - rcn
    - rcn2
    - rcg

Verify Cowan is accessible by running:

    rcn

in your terminal.

------------------------------------------------------------

WHAT THIS TOOL DOES

- Automatically generates IN36
- Runs Cowan (rcn, rcn2, rcg)
- Parses the results
- Extracts:
    • Fk (same-shell)
    • Fk (cross-shell)
    • Gk (exchange)
    • Zeta (spin–orbit)
- Converts all values to eV

------------------------------------------------------------

USAGE

Run:

    python cowan_runner.py

The script will prompt for the required atomic and configuration parameters.

------------------------------------------------------------

EXAMPLE

For Ni²⁺ 3d⁸ with a 2p core hole, run:

    python cowan_runner.py

The script will ask:

    Atomic number (Z): 28
    Element symbol (e.g. Co, Ni, Ce,...): Ni
    Ionization (e.g. 3+): 2+
    Open subshell (e.g. 3d,4d,4f): 3d
    Shell to create a hole (e.g. 2p,3d): 2p
    Occupation number n (e.g. 7 for 3d7): 8

    Select Cowan control mesh:
     90  = non-relativistic
    190 = relativistic (standard)
    290 = relativistic (recommended for heavy atoms / f systems)

    Mesh [290 default]: 290


Example output:

    Time spent: 0 hr 0 min 0.4 sec

    --- Ni2+  3d8 ---
    zeta_3d      = 0.0826 eV
    F2           = 12.2328 eV
    F4           = 7.5969 eV

    --- Ni2+  2p5 3d9 ---
    zeta_2p      = 11.5070 eV
    zeta_3d      = 0.1022 eV
    G1pd         = 5.7829 eV
    F2pd         = 7.7204 eV
    G3pd         = 3.2898 eV
    F2           = 13.0052 eV
    F4           = 8.0836 eV

------------------------------------------------------------

NOTES

- The Cowan CODE directory must be accessible via PATH
- This repository does NOT distribute Cowan binaries
- Designed for atomic multiplet and spectroscopy calculations
- The mesh details can be found on COWAN documentation
------------------------------------------------------------


## Citation

If you use this tool in published work, please cite both this repository and the original Cowan code.

Cowan code:

R. D. Cowan,
"The Theory of Atomic Structure and Spectra",
University of California Press, 1981.

BibTeX:

@book{cowan1981theory,
  title={The Theory of Atomic Structure and Spectra},
  author={Cowan, Robert D.},
  year={1981},
  publisher={University of California Press}
}



LICENSE

MIT License

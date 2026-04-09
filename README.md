# MixedSignalIDE

A ngspice based mixed signal IDE that operates on top of Standard ARM and embedded cores.

## Analog circuit definition library

The `src/analog.py` module provides a simple way to define analog circuits without writing raw SPICE netlists.

Example usage:

```python
from PyMd import AnalogCircuit
from PySpice.Unit import *

circuit = AnalogCircuit('RC Circuit Transient')
out_node = circuit.create_node('out')

circuit.add_voltage_source(
    'input',
    positive_node='input',
    negative_node='0',
    pulse='PULSE(0 1 1u 1u 1u 10m 20m)',
)
circuit.add_resistor('1', 'input', out_node, 1@u_kOhm)
circuit.add_capacitor('1', out_node, '0', 1@u_uF)

# You can access the node as a Python object:
print(out_node.voltage)
print(out_node.current)

circuit.add_raw_spice('''
.tran 1u 5m uic
.control
run
wrdata results.txt v(out) v(input)
quit
.endcontrol
''')

circuit.save_netlist('circuit.lib')
```

This gives you a lightweight circuit definition layer; the actual simulation plumbing can be performed by `pymd.analog`, `PySpice`, or `ngspice`.

## Installation

A helper script and a local virtual environment are provided under `installation/`.

Steps:

1. From the repo root, run:
   - `bash installation/install.sh`
2. Activate the environment after installation:
   - `source installation/venv/bin/activate`
3. Run the sample node flow:
   - `python unit-tests/rc.py`

The installer creates `installation/venv/`, installs dependencies from `installation/requirements.txt`, and displays an animated "MixedSignalIDE" banner while installing.

## SDK Installation

Use the installer and manager scripts under `installation/` for a professional setup flow.

Steps:

1. Run the installer:
   - `bash installation/install.sh`
2. Use the SDK manager:
   - `bash installation/manage.sh`
   - choose option `2` to enter the virtual environment through the UI.
3. Alternatively, activate directly:
   - `source installation/venv/bin/activate`
4. Run the sample node flow:
   - `python unit-tests/rc.py`

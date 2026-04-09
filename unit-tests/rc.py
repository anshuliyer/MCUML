import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure the repository root is on sys.path so the PyMd package can be found
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PyMd import AnalogCircuit
from PySpice.Unit import *


def node_flow():
    circuit = AnalogCircuit('NodeFlow')

    output_node = circuit.create_node('out')

    circuit.add_voltage_source(
        'input',
        positive_node='input',
        negative_node='0',
        pulse='PULSE(0 1 1u 1u 1u 10m 20m)',
    )

    circuit.add_resistor('1', 'input', output_node, 1@u_kOhm)
    circuit.add_capacitor('1', output_node, '0', 1@u_uF)

    circuit.configure_transient(step='10m', stop_time='10m', uic=True)
    circuit.add_current_probes(output_node)
    circuit.set_netlist_path('node_flow.lib')
    circuit.set_results_path('node_flow.txt')

    data = circuit.simulate()
    voltage_values = circuit.get_node_voltage(output_node, data)
    current_values = circuit.get_node_current(output_node, data)
    latest_voltage = circuit.get_node_latest_voltage(output_node, data)
    latest_current = circuit.get_node_latest_current(output_node, data)

    print(f'Node object: {output_node}')
    print(f'Voltage probe name: {output_node.voltage}')
    print(f'Current probe name: {output_node.current}')
    print(f'Minimal sampled voltage values: {voltage_values.tolist()}')
    print(f'Minimal sampled current values: {current_values.tolist()}')
    print(f'Latest voltage at node {output_node.name}: {latest_voltage}')
    print(f'Latest current at node {output_node.name}: {latest_current}')

    # Plot only if desired; not required for minimal sampling.
    plt.figure(figsize=(6, 4))
    plt.plot(data[:, 0] * 1000, voltage_values, marker='o')
    plt.title('Node Flow Voltage')
    plt.xlabel('Time (ms)')
    plt.ylabel('Voltage (V)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('node_flow_voltage.png')
    print("Saved 'node_flow_voltage.png'.")

    return output_node, data


if __name__ == '__main__':
    node_flow()

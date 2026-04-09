import os
import subprocess
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Union

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

@dataclass
class AnalogElement:
    element_type: str
    name: str
    nodes: List[str]
    value: str

@dataclass
class AnalogNode:
    name: str
    voltage: str = ''
    current: str = ''

    def __post_init__(self):
        self.voltage = f'v({self.name})'
        self.current = ''

NodeLike = Union[str, AnalogNode]

class AnalogCircuit:
    """A lightweight analog circuit definition wrapper.

    Use this object to define the circuit and configure simulation plumbing.
    All netlist generation, file paths, and Ngspice invocation can be
    controlled via method calls so the user only defines components.
    """
    def __init__(self, name: str = 'AnalogCircuit'):
        self.name = name
        self.elements: List[AnalogElement] = []
        self.raw_spice: str = ''
        self.transient_line: str = ''
        self.control_commands: List[str] = []
        self.probe_voltages: List[str] = []
        self.probe_currents: List[str] = []
        self.netlist_path: str = 'circuit.lib'
        self.results_path: str = 'results.txt'
        self.simulator: str = 'ngspice'
        self.simulator_options: List[str] = ['-b']

    def _normalize_node(self, node: NodeLike, circuit: Circuit):
        if isinstance(node, AnalogNode):
            node = node.name
        if str(node).lower() in {'0', 'gnd'}:
            return circuit.gnd
        return node

    def _node_name(self, node: NodeLike) -> str:
        return node.name if isinstance(node, AnalogNode) else str(node)

    def _format_value(self, value) -> str:
        if isinstance(value, str):
            return value
        try:
            return str(float(value))
        except (TypeError, ValueError):
            return str(value)

    def _assign_current_probe(self, node: NodeLike, element_name: str):
        if isinstance(node, AnalogNode) and not node.current:
            node.current = f'i({element_name})'

    def add_resistor(self, name: str, node1: NodeLike, node2: NodeLike, value):
        self._assign_current_probe(node1, name)
        self._assign_current_probe(node2, name)
        self.elements.append(
            AnalogElement('R', name, [self._node_name(node1), self._node_name(node2)], self._format_value(value))
        )

    def add_capacitor(self, name: str, node1: NodeLike, node2: NodeLike, value):
        self._assign_current_probe(node1, name)
        self._assign_current_probe(node2, name)
        self.elements.append(
            AnalogElement('C', name, [self._node_name(node1), self._node_name(node2)], self._format_value(value))
        )

    def add_inductor(self, name: str, node1: NodeLike, node2: NodeLike, value):
        self._assign_current_probe(node1, name)
        self._assign_current_probe(node2, name)
        self.elements.append(
            AnalogElement('L', name, [self._node_name(node1), self._node_name(node2)], self._format_value(value))
        )

    def add_voltage_source(
        self,
        name: str,
        positive_node: NodeLike,
        negative_node: NodeLike,
        voltage: Optional[float] = None,
        pulse: Optional[str] = None,
    ):
        self._assign_current_probe(positive_node, name)
        self._assign_current_probe(negative_node, name)
        value = pulse if pulse is not None else self._format_value(voltage if voltage is not None else 0)
        self.elements.append(
            AnalogElement('V', name, [self._node_name(positive_node), self._node_name(negative_node)], value)
        )

    def add_current_source(self, name: str, positive_node: NodeLike, negative_node: NodeLike, current: float):
        self._assign_current_probe(positive_node, name)
        self._assign_current_probe(negative_node, name)
        self.elements.append(
            AnalogElement('I', name, [self._node_name(positive_node), self._node_name(negative_node)], self._format_value(current))
        )

    def create_node(self, name: str) -> AnalogNode:
        node = AnalogNode(name)
        self.add_probe_nodes(node)
        return node

    def add_raw_spice(self, raw_text: str):
        self.raw_spice += raw_text

    def get_node_voltage(self, node: NodeLike, data: Optional[np.ndarray] = None) -> np.ndarray:
        data = data if data is not None else self.load_results()
        node_name = self._node_name(node)
        if node_name not in self.probe_voltages:
            raise ValueError(f'Node {node_name} is not being voltage-probed')
        index = self.probe_voltages.index(node_name) + 1
        return data[:, index]

    def get_node_latest_voltage(self, node: NodeLike, data: Optional[np.ndarray] = None) -> float:
        voltages = self.get_node_voltage(node, data)
        return float(voltages[-1])

    def get_node_current(self, node: NodeLike, data: Optional[np.ndarray] = None) -> np.ndarray:
        data = data if data is not None else self.load_results()
        if isinstance(node, AnalogNode):
            expression = node.current
            if not expression:
                raise ValueError(f"Node {node.name} has no current probe assigned.")
        else:
            expression = self._node_name(node)

        if expression not in self.probe_currents:
            raise ValueError(f'Node {expression} is not being current-probed')
        index = len(self.probe_voltages) + self.probe_currents.index(expression) + 1
        return data[:, index]

    def get_node_latest_current(self, node: NodeLike, data: Optional[np.ndarray] = None) -> float:
        currents = self.get_node_current(node, data)
        return float(currents[-1])

    def set_netlist_path(self, path: str):
        self.netlist_path = path

    def set_results_path(self, path: str):
        self.results_path = path

    def set_simulator(self, simulator: str, options: Optional[List[str]] = None):
        self.simulator = simulator
        if options is not None:
            self.simulator_options = options

    def configure_transient(self, step: str, stop_time: str, uic: bool = False):
        uic_option = ' uic' if uic else ''
        self.transient_line = f'.tran {step} {stop_time}{uic_option}'

    def add_probe_nodes(self, *nodes: NodeLike):
        for node in nodes:
            name = self._node_name(node)
            if name not in self.probe_voltages:
                self.probe_voltages.append(name)

    def add_current_probes(self, *nodes: NodeLike):
        for node in nodes:
            if isinstance(node, AnalogNode):
                if not node.current:
                    raise ValueError(f"Current probe not assigned for node '{node.name}'. Add an element connection first.")
                if node.current not in self.probe_currents:
                    self.probe_currents.append(node.current)
            else:
                name = self._node_name(node)
                if name not in self.probe_currents:
                    self.probe_currents.append(name)

    def add_control_command(self, command: str):
        self.control_commands.append(command)

    def _build_simulation_directives(self) -> str:
        directives: List[str] = []
        if self.transient_line:
            directives.append(self.transient_line)

        if self.control_commands or self.probe_voltages or self.probe_currents:
            directives.append('.control')
            for command in self.control_commands:
                directives.append(command)

            probes = []
            probes.extend(f'v({node})' for node in self.probe_voltages)
            for probe in self.probe_currents:
                if probe.startswith('i(') and probe.endswith(')'):
                    probes.append(probe)
                else:
                    probes.append(f'i({probe})')

            if probes:
                directives.append('run')
                directives.append(f"wrdata {self.results_path} {' '.join(probes)}")

            directives.append('quit')
            directives.append('.endcontrol')

        if self.raw_spice:
            directives.append(self.raw_spice.strip())

        return '\n'.join(directives).strip()

    def build_pyspice_circuit(self) -> Circuit:
        circuit = Circuit(self.name)
        for element in self.elements:
            nodes = [self._normalize_node(node, circuit) for node in element.nodes]
            if element.element_type == 'R':
                circuit.R(element.name, nodes[0], nodes[1], element.value)
            elif element.element_type == 'C':
                circuit.C(element.name, nodes[0], nodes[1], element.value)
            elif element.element_type == 'L':
                circuit.L(element.name, nodes[0], nodes[1], element.value)
            elif element.element_type == 'V':
                circuit.V(element.name, nodes[0], nodes[1], element.value)
            elif element.element_type == 'I':
                circuit.I(element.name, nodes[0], nodes[1], element.value)
            else:
                raise ValueError(f'Unsupported element type: {element.element_type}')

        full_raw = self._build_simulation_directives()
        if full_raw:
            circuit.raw_spice += full_raw

        return circuit

    def to_netlist(self) -> str:
        return str(self.build_pyspice_circuit())

    def save_netlist(self, path: Optional[str] = None) -> None:
        path = path or self.netlist_path
        with open(path, 'w') as netlist_file:
            netlist_file.write(self.to_netlist())

    def run(self, netlist_path: Optional[str] = None, results_path: Optional[str] = None, simulator: Optional[str] = None) -> None:
        netlist_path = netlist_path or self.netlist_path
        results_path = results_path or self.results_path
        simulator = simulator or self.simulator

        self.set_netlist_path(netlist_path)
        self.set_results_path(results_path)

        self.save_netlist(netlist_path)

        if simulator.lower() != 'ngspice':
            raise ValueError(f"Unsupported simulator: {simulator}")

        args = [simulator] + self.simulator_options + [netlist_path]
        subprocess.run(args, check=True, capture_output=True)

    def load_results(self, path: Optional[str] = None):
        path = path or self.results_path
        if not os.path.exists(path):
            raise FileNotFoundError(f'Results file not found: {path}')

        return np.loadtxt(path)

    def simulate(self, netlist_path: Optional[str] = None, results_path: Optional[str] = None):
        self.run(netlist_path=netlist_path, results_path=results_path)
        return self.load_results(results_path)

    def __repr__(self) -> str:
        return f'<AnalogCircuit name={self.name} elements={len(self.elements)}>'

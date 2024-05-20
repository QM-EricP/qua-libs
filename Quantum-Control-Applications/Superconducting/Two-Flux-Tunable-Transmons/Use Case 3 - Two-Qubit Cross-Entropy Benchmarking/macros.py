"""
This script contains useful QUA macros for the two-qubit cross-entropy benchmarking use case.

Author: Arthur Strauss - Quantum Machines
Last updated: 2024-04-30
"""

import pandas as pd
from matplotlib import pyplot as plt, colors
from qm.qua import *
from qualang_tools.addons.variables import assign_variables_to_element
import numpy as np
from scipy import optimize
from scipy.stats import stats
from quam.components import Channel


def assign_amplitude_matrix(gate, amp_matrix, gate_dict: dict):
    """
    QUA Macro for assigning the amplitude matrix arguments for a given gate index.
    :param gate: Gate index
    :param amp_matrix: Amplitude matrix arguments
    :param gate_dict: Dictionary of gates
    """
    with switch_(gate):
        for i in range(len(gate_dict)):
            with case_(i):
                for j in range(4):
                    assign(amp_matrix[j], gate_dict[i]["amp_matrix"][j])


def qua_declaration(n_qubits: int, readout_elements: list):
    """
    Macro to declare the necessary QUA variables

    :param n_qubits: Number of qubits used in this experiment
    :param readout_elements: List of readout elements
    :return:
    """
    I, Q = [[declare(fixed) for _ in range(n_qubits)] for _ in range(2)]
    I_st, Q_st = [[declare_stream() for _ in range(n_qubits)] for _ in range(2)]
    # Workaround to manually assign the results variables to the readout elements
    for i in range(n_qubits):
        assign_variables_to_element(readout_elements[i].name, I[i], Q[i])
    return I, I_st, Q, Q_st


def play_T_gate_set(gate, amp_matrix, qubit_el: Channel, baseline_op: str):
    """
    QUA Macro for the T gate set
    The two first cases will focus on the X90 and Y90 gates, while the last case will focus on the T gate.
    :param gate: Gate index
    :param amp_matrix: Amplitude matrix
    :param qubit_el: Qubit element
    """
    with switch_(gate, unsafe=True):
        for j in range(2):  # X90, Y90
            with case_(j):
                qubit_el.play(baseline_op, amp(*amp_matrix))
        with case_(2):  # T gate
            frame_rotation_2pi(0.125, qubit_el.name)


def play_SW_gate_set(gate, amp_matrix, qubit_el: Channel, baseline_op: str):
    """
    QUA Macro for the SW gate set
    The two first cases will focus on the X90 and Y90 gates, while the last case will focus on the SW gate.
    :param gate: Gate index
    :param amp_matrix: Amplitude matrix
    :param qubit_el: Qubit element
    :param baseline_op: Baseline operation (default "sx")
    """
    with switch_(gate, unsafe=True):
        for j in range(3):  # X90, Y90, SW
            with case_(j):
                qubit_el.play(baseline_op, amp(*amp_matrix))


def play_random_sq_gate(gate, amp_matrix, qubit_el: Channel, gate_dict: dict, baseline_op: str):
    """
    QUA Macro for playing a random single-qubit gate. This macro is built through amplitude matrix modulation of a provided
    baseline pulse implementing the pi/2 rotation around the x-axis.
    :param gate: Gate index
    :param amp_matrix: Amplitude matrix
    :param qubit_el: Qubit element
    :param gate_dict: Dictionary of gates
    :param baseline_op: Baseline operation (default "sx") implementing the pi/2 rotation around the x-axis
    """

    if gate_dict[2]["gate"].name == "t":  # T gate involves frame rotation
        play_T_gate_set(gate, amp_matrix, qubit_el, baseline_op)
    elif gate_dict[2]["gate"].label == "sw":
        play_SW_gate_set(gate, amp_matrix, qubit_el, baseline_op)
    else:
        qubit_el.play(baseline_op, amp(*amp_matrix))


def reset_qubit(method: str, qubit: str, resonator: str, **kwargs):
    """
    Macro to reset the qubit state.

    If method is 'cooldown', then the variable cooldown_time (in clock cycles) must be provided as a python integer > 4.

    **Example**: reset_qubit('cooldown', cooldown_times=500)

    If method is 'active', then 3 parameters are available as listed below.

    **Example**: reset_qubit('active', threshold=-0.003, max_tries=3)

    :param method: Method the reset the qubit state. Can be either 'cooldown' or 'active'.
    :param qubit: The qubit element. Must be defined in the config.
    :param resonator: The resonator element. Must be defined in the config.
    :key cooldown_time: qubit relaxation time in clock cycle, needed if method is 'cooldown'. Must be an integer > 4.
    :key threshold: threshold to discriminate between the ground and excited state, needed if method is 'active'.
    :key max_tries: python integer for the maximum number of tries used to perform active reset,
        needed if method is 'active'. Must be an integer > 0 and default value is 1.
    :key Ig: A QUA variable for the information in the `I` quadrature used for active reset. If not given, a new
        variable will be created. Must be of type `Fixed`.
    :return:
    """
    if method == "cooldown":
        # Check cooldown_time
        cooldown_time = kwargs.get("cooldown_time", None)
        if (cooldown_time is None) or (cooldown_time < 4):
            raise Exception("'cooldown_time' must be an integer > 4 clock cycles")
        # Reset qubit state
        wait(cooldown_time, qubit)
    elif method == "active":
        # Check threshold
        threshold = kwargs.get("threshold", None)
        if threshold is None:
            raise Exception("'threshold' must be specified for active reset.")
        # Check max_tries
        max_tries = kwargs.get("max_tries", 1)
        if (max_tries is None) or (not float(max_tries).is_integer()) or (max_tries < 1):
            raise Exception("'max_tries' must be an integer > 0.")
        # Check Ig
        Ig = kwargs.get("Ig", None)
        # Reset qubit state
        return active_reset(threshold, qubit, resonator, max_tries=max_tries, Ig=Ig)


# Macro for performing active reset until successful for a given number of tries.
def active_reset(threshold: float, qubit: str, resonator: str, max_tries=1, Ig=None):
    """Macro for performing active reset until successful for a given number of tries.

    :param threshold: threshold for the 'I' quadrature discriminating between ground and excited state.
    :param qubit: The qubit element. Must be defined in the config.
    :param resonator: The resonator element. Must be defined in the config.
    :param max_tries: python integer for the maximum number of tries used to perform active reset. Must >= 1.
    :param Ig: A QUA variable for the information in the `I` quadrature. Should be of type `Fixed`. If not given, a new
        variable will be created
    :return: A QUA variable for the information in the `I` quadrature and the number of tries after success.
    """
    if Ig is None:
        Ig = declare(fixed)
    if (max_tries < 1) or (not float(max_tries).is_integer()):
        raise Exception("max_count must be an integer >= 1.")
    # Initialize Ig to be > threshold
    assign(Ig, threshold + 2**-28)
    # Number of tries for active reset
    counter = declare(int)
    # Reset the number of tries
    assign(counter, 0)

    # Perform active feedback
    align(qubit, resonator)
    # Use a while loop and counter for other protocols and tests
    with while_((Ig > threshold) & (counter < max_tries)):
        # Measure the resonator
        measure(
            "readout",
            resonator,
            None,
            dual_demod.full("rotated_cos", "out1", "rotated_sin", "out2", Ig),
        )
        # Play a pi pulse to get back to the ground state
        play("x180", qubit, condition=(Ig > threshold))
        # Increment the number of tries
        assign(counter, counter + 1)
    return Ig, counter


def cz_gate(control, target, CZ_operations: dict):
    """
    QUA Macro for the CZ gate
    :param control: Control qubit index
    :param target: Target qubit index
    :param CZ_operations: Dictionary of CZ operations (control, target) -> (cz_el, cz_op)
    """
    cz_el, cz_op = CZ_operations[(control, target)]
    play(cz_op, cz_el)


def binary(n, length):
    """
    Convert an integer to a binary string of a given length
    :param n: Integer to convert
    :param length: Length of the output string
    :return: Binary string corresponding to integer n
    """
    return bin(n)[2:].zfill(length)


def cross_entropy(p, q, epsilon=1e-15):
    """
    Calculate cross entropy between two probability distributions.

    Parameters:
    - p: numpy array, the true probability distribution
    - q: numpy array, the predicted probability distribution
    - epsilon: small value to avoid taking the logarithm of zero

    Returns:
    - Cross entropy between p and q
    """
    q = np.maximum(q, epsilon)  # Avoid taking the logarithm of zero
    x_entropy = -np.sum(p * np.log(q))
    return x_entropy


def create_subplot(data, subplot_number, title, depths, seqs):
    print(title)
    print("data: %s" % data)
    print(subplot_number)
    plt.subplot(subplot_number)
    # plt.pcolor(depths, range(seqs), np.abs(data), vmin=0., vmax=1.)
    plt.pcolor(depths, range(seqs), np.abs(data))
    ax = plt.gca()
    ax.set_title(title)
    if subplot_number > 244:
        ax.set_xlabel("Circuit depth")
    ax.set_ylabel("Sequences")
    ax.set_xticks(depths)
    ax.set_yticks(np.arange(1, seqs + 1))
    plt.colorbar()


# Define Cirq functions for fitting (redefined here for avoiding additional dependencies)
# Those functions are slightly adapted to deal with possible singularities and outliers in the data
def exponential_decay(cycle_depths: np.ndarray, a: float, layer_fid: float) -> np.ndarray:
    """An exponential decay for fitting.

    This computes `a * layer_fid**cycle_depths`

    Args:
        cycle_depths: The various depths at which fidelity was estimated. This is the independent
            variable in the exponential function.
        a: A scale parameter in the exponential function.
        layer_fid: The base of the exponent in the exponential function.
    """
    return a * layer_fid**cycle_depths


def fit_exponential_decay(cycle_depths: np.ndarray, fidelities: np.ndarray) -> tuple[float, float, float, float]:
    """Fit an exponential model fidelity = a * layer_fid**x using nonlinear least squares.

    This uses `exponential_decay` as the function to fit with parameters `a` and `layer_fid`.
    This function is taken from the following Cirq code: https://github.com/quantumlib/Cirq/blob/main/cirq-core/cirq/experiments/xeb_fitting.py

    Args:
        cycle_depths: The various depths at which fidelity was estimated. Each element is `x`
            in the fit expression.
        fidelities: The estimated fidelities for each cycle depth. Each element is `fidelity`
            in the fit expression.

    Returns:
        a: The first fit parameter that scales the exponential function, perhaps accounting for
            state prep and measurement (SPAM) error.
        layer_fid: The second fit parameters which serves as the base of the exponential.
        a_std: The standard deviation of the `a` parameter estimate.
        layer_fid_std: The standard deviation of the `layer_fid` parameter estimate.
    """
    cycle_depths = np.asarray(cycle_depths)
    fidelities = np.asarray(fidelities)
    mask = (fidelities > 0) & (fidelities < 1)
    print()
    masked_cycle_depths = cycle_depths[mask]
    masked_fidelities = fidelities[mask]

    log_fidelities = np.log(masked_fidelities)

    slope, intercept, _, _, _ = stats.linregress(masked_cycle_depths, log_fidelities)
    layer_fid_0 = np.clip(np.exp(slope), 0, 1)
    a_0 = np.clip(np.exp(intercept), 0, 1)

    try:
        (a, layer_fid), pcov = optimize.curve_fit(
            exponential_decay,
            masked_cycle_depths,
            masked_fidelities,
            p0=(a_0, layer_fid_0),
            bounds=((0, 0), (1, 1)),
            nan_policy="omit",
        )
    except ValueError:  # pragma: no cover
        return 0, 0, np.inf, np.inf

    a_std, layer_fid_std = np.sqrt(np.diag(pcov))
    return a, layer_fid, a_std, layer_fid_std

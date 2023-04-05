import numpy as np
from scipy.signal.windows import gaussian
from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms
from qualang_tools.units import unit
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import progress_counter, fetching_tool
from qm.qua import *

#######################
# AUXILIARY FUNCTIONS #
#######################

# IQ imbalance matrix
def IQ_imbalance(g, phi):
    """
    Creates the correction matrix for the mixer imbalance caused by the gain and phase imbalances, more information can
    be seen here:
    https://docs.qualang.io/libs/examples/mixer-calibration/#non-ideal-mixer

    :param g: relative gain imbalance between the I & Q ports (unit-less). Set to 0 for no gain imbalance.
    :param phi: relative phase imbalance between the I & Q ports (radians). Set to 0 for no phase imbalance.
    """
    c = np.cos(phi)
    s = np.sin(phi)
    N = 1 / ((1 - g**2) * (2 * c**2 - 1))
    return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]


##########
# macros #
##########


def measure_qubit_0(qubit):
    I = declare(fixed)
    Q = declare(fixed)
    measure(
        "readout",
        "rr0",
        None,
        dual_demod.full("cos", "out1", "sin", "out2", I),
        dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
    )
    assign(qubit, I > 0)
    return Q


def measure_qubit_1(qubit):
    I = declare(fixed)
    Q = declare(fixed)
    measure(
        "readout",
        "rr1",
        None,
        dual_demod.full("cos", "out1", "sin", "out2", I),
        dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
    )
    assign(qubit, I > 0)
    return Q


#############
# VARIABLES #
#############
qubit0_qe = "qe0"
qubit1_qe = "qe1"
qubit0_x_pulse = "x180"
qubit1_x_pulse = "x180"
qubit0_flux_qe = "qubit0_flux_qe"
iswap_pulse = "iswap_pulse"
u = unit()
qop_ip = "127.0.0.1"

# qe0s
qe0_IF = 50 * u.MHz
qe0_LO = 7 * u.GHz
mixer_qe0_g = 0.0
mixer_qe0_phi = 0.0
qe1_IF = 50 * u.MHz
qe1_LO = 7 * u.GHz
mixer_qe1_g = 0.0
mixer_qe1_phi = 0.0

qe0_T1 = int(10 * u.us)

saturation_len = 1000
saturation_amp = 0.1
const_len = 100
const_amp = 0.1
square_pi_len = 100
square_pi_amp = 0.1

drag_coef = 0
anharmonicity = -200 * u.MHz
AC_stark_detuning = 0 * u.MHz

gauss_len = 200
gauss_sigma = gauss_len / 5
gauss_amp = 0.25
gauss_wf = gauss_amp * gaussian(gauss_len, gauss_sigma)

displace_len = 40
displace_sigma = displace_len / 5
displace_amp = 0.35
displace_wf = displace_amp * gaussian(displace_len, displace_sigma)

x180_len = 40
x180_sigma = x180_len / 5
x180_amp = 0.35
x180_wf, x180_der_wf = np.array(
    drag_gaussian_pulse_waveforms(x180_amp, x180_len, x180_sigma, drag_coef, anharmonicity, AC_stark_detuning)
)
x180_I_wf = x180_wf
x180_Q_wf = x180_der_wf
# No DRAG when alpha=0, it's just a gaussian.

x90_len = x180_len
x90_sigma = x90_len / 5
x90_amp = x180_amp / 2
x90_wf, x90_der_wf = np.array(
    drag_gaussian_pulse_waveforms(x90_amp, x90_len, x90_sigma, drag_coef, anharmonicity, AC_stark_detuning)
)
x90_I_wf = x90_wf
x90_Q_wf = x90_der_wf
# No DRAG when alpha=0, it's just a gaussian.

minus_x90_len = x180_len
minus_x90_sigma = minus_x90_len / 5
minus_x90_amp = -x90_amp
minus_x90_wf, minus_x90_der_wf = np.array(
    drag_gaussian_pulse_waveforms(
        minus_x90_amp,
        minus_x90_len,
        minus_x90_sigma,
        drag_coef,
        anharmonicity,
        AC_stark_detuning,
    )
)
minus_x90_I_wf = minus_x90_wf
minus_x90_Q_wf = minus_x90_der_wf
# No DRAG when alpha=0, it's just a gaussian.

y180_len = x180_len
y180_sigma = y180_len / 5
y180_amp = x180_amp
y180_wf, y180_der_wf = np.array(
    drag_gaussian_pulse_waveforms(y180_amp, y180_len, y180_sigma, drag_coef, anharmonicity, AC_stark_detuning)
)
y180_I_wf = (-1) * y180_der_wf
y180_Q_wf = y180_wf
# No DRAG when alpha=0, it's just a gaussian.

y90_len = x180_len
y90_sigma = y90_len / 5
y90_amp = y180_amp / 2
y90_wf, y90_der_wf = np.array(
    drag_gaussian_pulse_waveforms(y90_amp, y90_len, y90_sigma, drag_coef, anharmonicity, AC_stark_detuning)
)
y90_I_wf = (-1) * y90_der_wf
y90_Q_wf = y90_wf
# No DRAG when alpha=0, it's just a gaussian.

minus_y90_len = y180_len
minus_y90_sigma = minus_y90_len / 5
minus_y90_amp = -y90_amp
minus_y90_wf, minus_y90_der_wf = np.array(
    drag_gaussian_pulse_waveforms(
        minus_y90_amp,
        minus_y90_len,
        minus_y90_sigma,
        drag_coef,
        anharmonicity,
        AC_stark_detuning,
    )
)
minus_y90_I_wf = (-1) * minus_y90_der_wf
minus_y90_Q_wf = minus_y90_wf
# No DRAG when alpha=0, it's just a gaussian.

# rr0
rr0_IF = 60 * u.MHz
rr0_LO = 5.5 * u.GHz
mixer_rr0_g = 0.0
mixer_rr0_phi = 0.0
rr1_IF = 60 * u.MHz
rr1_LO = 5.5 * u.GHz
mixer_rr1_g = 0.0
mixer_rr1_phi = 0.0

time_of_flight = 180

short_readout_len = 500
short_readout_amp = 0.4
readout_len = 500
readout_amp = 0.1
long_readout_len = 50000
long_readout_amp = 0.1

# IQ Plane
rotation_angle = (0.0 / 180) * np.pi
ge_threshold = 0.0

# Flux line
const_flux_len = 612
const_flux_amp = 0.05

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0},  # I qe0
                2: {"offset": 0.0},  # Q qe0
                3: {"offset": 0.0},  # I rr0
                4: {"offset": 0.0},  # Q rr0
                5: {"offset": 0.0},
                6: {"offset": 0.0},
                7: {"offset": 0.0},
            },
            "digital_outputs": {},
            "analog_inputs": {
                1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
            },
        },
    },
    "elements": {
        "qe0": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": qe0_LO,
                "mixer": "mixer_qe0",
            },
            "intermediate_frequency": qe0_IF,
            "operations": {
                "cw": "const_pulse",
                "saturation": "saturation_pulse",
                "gauss": "gaussian_pulse",
                "pi": "x180_pulse",
                "pi_half": "x90_pulse",
                "x90": "x90_pulse",
                "x180": "x180_pulse",
                "-x90": "-x90_pulse",
                "y90": "y90_pulse",
                "y180": "y180_pulse",
                "-y90": "-y90_pulse",
            },
        },
        "qe1": {
            "mixInputs": {
                "I": ("con1", 5),
                "Q": ("con1", 6),
                "lo_frequency": qe1_LO,
                "mixer": "mixer_qe1",
            },
            "intermediate_frequency": qe1_IF,
            "operations": {
                "cw": "const_pulse",
                "saturation": "saturation_pulse",
                "gauss": "gaussian_pulse",
                "pi": "x180_pulse",
                "pi_half": "x90_pulse",
                "x90": "x90_pulse",
                "x180": "x180_pulse",
                "-x90": "-x90_pulse",
                "y90": "y90_pulse",
                "y180": "y180_pulse",
                "-y90": "-y90_pulse",
            },
        },
        "crtqe1cqe0": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": qe0_LO,
                "mixer": "mixer_qe1",
            },
            "intermediate_frequency": qe1_IF,
            "operations": {
                "cw": "const_pulse",
            },
        },
        "rr0": {
            "mixInputs": {
                "I": ("con1", 3),
                "Q": ("con1", 4),
                "lo_frequency": rr0_LO,
                "mixer": "mixer_rr0",
            },
            "intermediate_frequency": rr0_IF,
            "operations": {
                "cw": "const_pulse",
                "displace": "displace_pulse",
                "short_readout": "short_readout_pulse",
                "readout": "readout_pulse",
                "long_readout": "long_readout_pulse",
            },
            "outputs": {
                "out1": ("con1", 1),
                "out2": ("con1", 2),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "rr1": {
            "mixInputs": {
                "I": ("con1", 3),
                "Q": ("con1", 4),
                "lo_frequency": rr1_LO,
                "mixer": "mixer_rr1",
            },
            "intermediate_frequency": rr1_IF,
            "operations": {
                "cw": "const_pulse",
                "displace": "displace_pulse",
                "short_readout": "short_readout_pulse",
                "readout": "readout_pulse",
                "long_readout": "long_readout_pulse",
            },
            "outputs": {
                "out1": ("con1", 1),
                "out2": ("con1", 2),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "qubit0_flux_qe": {
            "singleInput": {
                "port": ("con1", 7),
            },
            "operations": {
                "iswap_pulse": "const_flux_pulse",
            },
        },
    },
    "pulses": {
        "const_flux_pulse": {
            "operation": "control",
            "length": const_flux_len,
            "waveforms": {
                "single": "const_flux_wf",
            },
        },
        "const_pulse": {
            "operation": "control",
            "length": const_len,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
        "square_pi_pulse": {
            "operation": "control",
            "length": square_pi_len,
            "waveforms": {
                "I": "square_pi_wf",
                "Q": "zero_wf",
            },
        },
        "saturation_pulse": {
            "operation": "control",
            "length": saturation_len,
            "waveforms": {"I": "saturation_drive_wf", "Q": "zero_wf"},
        },
        "gaussian_pulse": {
            "operation": "control",
            "length": gauss_len,
            "waveforms": {
                "I": "gauss_wf",
                "Q": "zero_wf",
            },
        },
        "displace_pulse": {
            "operation": "control",
            "length": displace_len,
            "waveforms": {
                "I": "displace_wf",
                "Q": "displace_wf",
            },
        },
        "x90_pulse": {
            "operation": "control",
            "length": x90_len,
            "waveforms": {
                "I": "x90_I_wf",
                "Q": "x90_Q_wf",
            },
        },
        "x180_pulse": {
            "operation": "control",
            "length": x180_len,
            "waveforms": {
                "I": "x180_I_wf",
                "Q": "x180_Q_wf",
            },
        },
        "-x90_pulse": {
            "operation": "control",
            "length": minus_x90_len,
            "waveforms": {
                "I": "minus_x90_I_wf",
                "Q": "minus_x90_Q_wf",
            },
        },
        "y90_pulse": {
            "operation": "control",
            "length": y90_len,
            "waveforms": {
                "I": "y90_I_wf",
                "Q": "y90_Q_wf",
            },
        },
        "y180_pulse": {
            "operation": "control",
            "length": y180_len,
            "waveforms": {
                "I": "y180_I_wf",
                "Q": "y180_Q_wf",
            },
        },
        "-y90_pulse": {
            "operation": "control",
            "length": minus_y90_len,
            "waveforms": {
                "I": "minus_y90_I_wf",
                "Q": "minus_y90_Q_wf",
            },
        },
        "short_readout_pulse": {
            "operation": "measurement",
            "length": short_readout_len,
            "waveforms": {
                "I": "short_readout_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "short_cosine_weights",
                "sin": "short_sine_weights",
                "minus_sin": "short_minus_sine_weights",
                "rotated_cos": "short_rotated_cosine_weights",
                "rotated_sin": "short_rotated_sine_weights",
                "rotated_minus_sin": "short_rotated_minus_sine_weights",
            },
            "digital_marker": "ON",
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": readout_len,
            "waveforms": {
                "I": "readout_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
                "rotated_cos": "rotated_cosine_weights",
                "rotated_sin": "rotated_sine_weights",
                "rotated_minus_sin": "rotated_minus_sine_weights",
            },
            "digital_marker": "ON",
        },
        "long_readout_pulse": {
            "operation": "measurement",
            "length": long_readout_len,
            "waveforms": {
                "I": "long_readout_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "long_cosine_weights",
                "sin": "long_sine_weights",
                "minus_sin": "long_minus_sine_weights",
                "rotated_cos": "long_rotated_cosine_weights",
                "rotated_sin": "long_rotated_sine_weights",
                "rotated_minus_sin": "long_rotated_minus_sine_weights",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "const_flux_wf": {"type": "constant", "sample": const_flux_amp},
        "const_wf": {"type": "constant", "sample": const_amp},
        "saturation_drive_wf": {"type": "constant", "sample": saturation_amp},
        "square_pi_wf": {"type": "constant", "sample": square_pi_amp},
        "displace_wf": {"type": "arbitrary", "samples": displace_wf.tolist()},
        "zero_wf": {"type": "constant", "sample": 0.0},
        "gauss_wf": {"type": "arbitrary", "samples": gauss_wf.tolist()},
        "x90_I_wf": {"type": "arbitrary", "samples": x90_I_wf.tolist()},
        "x90_Q_wf": {"type": "arbitrary", "samples": x90_Q_wf.tolist()},
        "x180_I_wf": {"type": "arbitrary", "samples": x180_I_wf.tolist()},
        "x180_Q_wf": {"type": "arbitrary", "samples": x180_Q_wf.tolist()},
        "minus_x90_I_wf": {"type": "arbitrary", "samples": minus_x90_I_wf.tolist()},
        "minus_x90_Q_wf": {"type": "arbitrary", "samples": minus_x90_Q_wf.tolist()},
        "y90_Q_wf": {"type": "arbitrary", "samples": y90_Q_wf.tolist()},
        "y90_I_wf": {"type": "arbitrary", "samples": y90_I_wf.tolist()},
        "y180_Q_wf": {"type": "arbitrary", "samples": y180_Q_wf.tolist()},
        "y180_I_wf": {"type": "arbitrary", "samples": y180_I_wf.tolist()},
        "minus_y90_Q_wf": {"type": "arbitrary", "samples": minus_y90_Q_wf.tolist()},
        "minus_y90_I_wf": {"type": "arbitrary", "samples": minus_y90_I_wf.tolist()},
        "short_readout_wf": {"type": "constant", "sample": short_readout_amp},
        "readout_wf": {"type": "constant", "sample": readout_amp},
        "long_readout_wf": {"type": "constant", "sample": long_readout_amp},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "integration_weights": {
        "short_cosine_weights": {
            "cosine": [(1.0, short_readout_len)],
            "sine": [(0.0, short_readout_len)],
        },
        "short_sine_weights": {
            "cosine": [(0.0, short_readout_len)],
            "sine": [(1.0, short_readout_len)],
        },
        "short_minus_sine_weights": {
            "cosine": [(0.0, short_readout_len)],
            "sine": [(-1.0, short_readout_len)],
        },
        "short_rotated_cosine_weights": {
            "cosine": [(np.cos(rotation_angle), short_readout_len)],
            "sine": [(-np.sin(rotation_angle), short_readout_len)],
        },
        "short_rotated_sine_weights": {
            "cosine": [(np.sin(rotation_angle), short_readout_len)],
            "sine": [(np.cos(rotation_angle), short_readout_len)],
        },
        "short_rotated_minus_sine_weights": {
            "cosine": [(-np.sin(rotation_angle), short_readout_len)],
            "sine": [(-np.cos(rotation_angle), short_readout_len)],
        },
        "cosine_weights": {
            "cosine": [(1.0, readout_len)],
            "sine": [(0.0, readout_len)],
        },
        "sine_weights": {
            "cosine": [(0.0, readout_len)],
            "sine": [(1.0, readout_len)],
        },
        "minus_sine_weights": {
            "cosine": [(0.0, readout_len)],
            "sine": [(-1.0, readout_len)],
        },
        "rotated_cosine_weights": {
            "cosine": [(np.cos(rotation_angle), readout_len)],
            "sine": [(-np.sin(rotation_angle), readout_len)],
        },
        "rotated_sine_weights": {
            "cosine": [(np.sin(rotation_angle), readout_len)],
            "sine": [(np.cos(rotation_angle), readout_len)],
        },
        "rotated_minus_sine_weights": {
            "cosine": [(-np.sin(rotation_angle), readout_len)],
            "sine": [(-np.cos(rotation_angle), readout_len)],
        },
        "long_cosine_weights": {
            "cosine": [(1.0, long_readout_len)],
            "sine": [(0.0, long_readout_len)],
        },
        "long_sine_weights": {
            "cosine": [(0.0, long_readout_len)],
            "sine": [(1.0, long_readout_len)],
        },
        "long_minus_sine_weights": {
            "cosine": [(0.0, long_readout_len)],
            "sine": [(-1.0, long_readout_len)],
        },
        "long_rotated_cosine_weights": {
            "cosine": [(np.cos(rotation_angle), long_readout_len)],
            "sine": [(-np.sin(rotation_angle), long_readout_len)],
        },
        "long_rotated_sine_weights": {
            "cosine": [(np.sin(rotation_angle), long_readout_len)],
            "sine": [(np.cos(rotation_angle), long_readout_len)],
        },
        "long_rotated_minus_sine_weights": {
            "cosine": [(-np.sin(rotation_angle), long_readout_len)],
            "sine": [(-np.cos(rotation_angle), long_readout_len)],
        },
    },
    "mixers": {
        "mixer_qe0": [
            {
                "intermediate_frequency": qe0_IF,
                "lo_frequency": qe0_LO,
                "correction": IQ_imbalance(mixer_qe0_g, mixer_qe0_phi),
            }
        ],
        "mixer_qe1": [
            {
                "intermediate_frequency": qe1_IF,
                "lo_frequency": qe1_LO,
                "correction": IQ_imbalance(mixer_qe1_g, mixer_qe1_phi),
            }
        ],
        "mixer_rr0": [
            {
                "intermediate_frequency": rr0_IF,
                "lo_frequency": rr0_LO,
                "correction": IQ_imbalance(mixer_rr0_g, mixer_rr0_phi),
            }
        ],
        "mixer_rr1": [
            {
                "intermediate_frequency": rr1_IF,
                "lo_frequency": rr1_LO,
                "correction": IQ_imbalance(mixer_rr1_g, mixer_rr1_phi),
            }
        ],
    },
}
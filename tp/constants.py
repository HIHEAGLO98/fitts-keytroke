import math

# Experiment Settings
NUM_TARGETS: int = 5
TARGET_MIN_SIZE: int = 30
TARGET_MAX_SIZE: int = 70

# Default regression coefficients for Fitts' law: T = a + b * log2(D/W + 1)
DEFAULT_A: float = 0.2
DEFAULT_B: float = 0.1

# GOMS/Keystroke default operator times (ms)
# Reference values from Card, Moran & Newell (1983)
DEFAULT_K_MS: float = 200.0   # K : time to press one key (ms)
DEFAULT_H_MS: float = 400.0   # H : time to move hand between keyboard and mouse (ms)
DEFAULT_P_MS: float = 1100.0  # P : time for one mouse pointer movement (ms)
DEFAULT_M_MS: float = 1300.0  # M : mental preparation time (ms)



def calculate_expected_time(d: float, w: float) -> float:
    """
    Calculate expected time using Fitts' Law: T = a + b * log2(D/W + 1).

    Args:
        d (float): Distance from the previous target's center.
        w (float): Width of the current target.

    Returns:
        float: Expected time to acquire the target.
    """
    return DEFAULT_A + DEFAULT_B * math.log2(d / w + 1) if w > 0 else 0.0


# Application settings (can be modified in settings screen)
class Settings:
    """
    Class to store application settings.
    """
    num_targets: int = NUM_TARGETS
    target_min_size: int = TARGET_MIN_SIZE
    target_max_size: int = TARGET_MAX_SIZE
    a_coefficient: float = DEFAULT_A
    b_coefficient: float = DEFAULT_B

    # GOMS/Keystroke empirical operator times (updated by experiments)
    K: float = DEFAULT_K_MS  # Keystroke time (ms)
    H: float = DEFAULT_H_MS  # Hand movement time (ms)
    P: float = DEFAULT_P_MS  # Pointing time (ms)
    M: float = DEFAULT_M_MS  # Mental time (ms)

    @classmethod
    def reset_to_defaults(cls) -> None:
        cls.num_targets = NUM_TARGETS
        cls.target_min_size = TARGET_MIN_SIZE
        cls.target_max_size = TARGET_MAX_SIZE
        cls.a_coefficient = DEFAULT_A
        cls.b_coefficient = DEFAULT_B

        cls.K = DEFAULT_K_MS
        cls.H = DEFAULT_H_MS
        cls.P = DEFAULT_P_MS
        cls.M = DEFAULT_M_MS
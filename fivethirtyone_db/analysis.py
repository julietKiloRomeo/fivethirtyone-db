import numpy as np
from . import to_add_pr_cycle

def one_rm_brzycki(weight, reps):
    """calculate 1rm max from several reps
    of a submaximal weight

    https://www.athlegan.com/calculate-1rm

    """
    return weight * 36 / (37 - reps)


def one_rm_lombardi(weight, reps):
    """calculate 1rm max from several reps
    of a submaximal weight

    https://www.athlegan.com/calculate-1rm

    """
    return weight * reps**0.1


def one_rm_fusion(weight, reps):
    """calculate 1rm max from several reps
    of a submaximal weight

    https://www.athlegan.com/calculate-1rm

    """
    return 0.5 * (one_rm_lombardi(weight, reps) + one_rm_brzycki(weight, reps))


def iso_brzycki(w_1):
    """
    return reps and weights for a specific 1rm max

    """
    n = np.linspace(1, 15, 100)

    return n, (37 - n) * w_1 / 36


def iso_fusion(w_1):
    """
    return reps and weights for a specific 1rm max

    """
    n = np.linspace(1, 15, 100)

    return n, 2 * w_1 / (n**0.1 + 36 / (37 - n))


def compile(athlete, lift, worksets, program, cycle=0):
    """given previous lifts and a base-program
    calculate a program for a specific lifter and
    exercise

    lifter (str):
    exercise (str):
    lifts (dataframe):
    program (dataframe): 

    """
    
    train_max = (
        worksets.query(f'athlete_name == "{athlete}" and lift_name == "{lift}" and is_max')
        .sort_values("date")
        .iloc[-1]["train_max"]
    )
    train_max += to_add_pr_cycle[lift] * cycle

    weight = (
        ((program["pct"] / 100 * train_max) // SMALLEST_W_INC) * SMALLEST_W_INC
    ).astype(int)
    to_lift = program.assign(weight=weight)[["reps", "weight"]].T
    to_lift.name = lifter

    return to_lift



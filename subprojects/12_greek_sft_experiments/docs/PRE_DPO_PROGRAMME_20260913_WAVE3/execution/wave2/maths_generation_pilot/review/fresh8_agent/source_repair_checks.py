#!/usr/bin/env python3
"""Independent arithmetic/numerical checks for root's two source repairs."""
from fractions import Fraction
from math import cos, pi, sin

meet_probability = 1 - Fraction(2) * Fraction(1, 2) * Fraction(45**2, 60**2)
print("1950", {"sample_space_area": 60**2, "nonmeet_area": 45**2,
               "meet_probability": meet_probability})

def original_left(x):
    return sum(sin(n*x)**2 for n in (1, 2, 3, 4)) - 2

def factor_left(x):
    return -2*cos(x)*cos(2*x)*cos(5*x)

grid = [j/17 for j in range(-40, 41)]
identity_error = max(abs(original_left(t)-factor_left(t)) for t in grid)
subset_error = max(abs(cos(5*((2*j+1)*pi/2))) for j in range(-10, 11))
print("6930", {"max_numeric_identity_error": identity_error,
               "max_cos5x_on_cosx_zero_grid": subset_error,
               "valid_triple_1": (1, 2, 5), "sum_1": 8,
               "same_zero_set_triple": (2, 5, 5), "sum_2": 12})

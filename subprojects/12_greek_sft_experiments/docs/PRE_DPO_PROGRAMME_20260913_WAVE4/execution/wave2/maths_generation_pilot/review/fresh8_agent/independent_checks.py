#!/usr/bin/env python3
"""Exact, local checks for the eight fresh Level-5 adjudication rows."""
from fractions import Fraction
from math import isqrt

def solve_linear_fraction(matrix):
    """Gauss-Jordan solve of an augmented square system over Fraction."""
    a = [[Fraction(v) for v in row] for row in matrix]
    n = len(a)
    for col in range(n):
        pivot = next(i for i in range(col, n) if a[i][col])
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [v / scale for v in a[col]]
        for i in range(n):
            if i == col:
                continue
            scale = a[i][col]
            a[i] = [u - scale*v for u, v in zip(a[i], a[col])]
    return [a[i][-1] for i in range(n)]

def polyval(coeffs, z):
    total = Fraction(0)
    for c in coeffs:
        total = total*z + c
    return total

# 1334: intercepts and triangle area.
y0 = (0 - 3) ** 2 * (0 + 2)
area_1334 = Fraction(1, 2) * (3 - (-2)) * y0
print("1334", {"x_intercepts": [-2, 3], "y_intercept": y0, "area": area_1334})

# 1379: injectivity reduces the intersection equation to x^2=x^4.
roots_1379 = [-1, 0, 1]  # x^2(x-1)(x+1)=0
print("1379", {"real_roots": roots_1379, "count": len(roots_1379)})

# 3775: transformed polynomial, discriminant, and the excluded double root.
forbidden_denominator = Fraction(-1, 2) * (-2) - 1
print("3775", {"polynomial": "k*x^2-2*x-2", "discriminant": "4+8k",
               "k=0_solution": [Fraction(-1)],
               "k=-1/2_factor": "-(x+2)^2/2",
               "denominator_at_double_root": forbidden_denominator})

# 4646: reconstruct the unique circle through the three stated points,
# then factor its intersection polynomial with xy=1.
points = [(Fraction(2), Fraction(1, 2)),
          (Fraction(-5), Fraction(-1, 5)),
          (Fraction(1, 3), Fraction(3))]
system = [[px, py, 1, -(px*px + py*py)] for px, py in points]
A, B, C = solve_linear_fraction(system)
circle_coeffs = {"A": A, "B": B, "C": C}
quartic_coeffs = [Fraction(1), A, C, B, Fraction(1)]
roots_4646 = [Fraction(2), Fraction(-5), Fraction(1, 3), Fraction(-3, 10)]
quartic_residuals = [polyval(quartic_coeffs, r) for r in roots_4646]
fourth_x = Fraction(-3, 10)
fourth_y = 1/fourth_x
circle_residual = fourth_x**2 + fourth_y**2 + A*fourth_x + B*fourth_y + C
print("4646", {"circle_coefficients": circle_coeffs,
               "quartic_coefficients": quartic_coeffs,
               "x_roots": roots_4646, "quartic_residuals": quartic_residuals,
               "root_product": roots_4646[0]*roots_4646[1]*roots_4646[2]*roots_4646[3],
               "fourth_point": (fourth_x, fourth_y),
               "circle_residual": circle_residual})

# 2676: equality of two base-height area expressions.
ce_2676 = Fraction(5 * 8, 4)
print("2676", {"area_from_AE_CD": Fraction(5 * 8, 2), "CE": ce_2676})

# 3093: inradius-to-altitude ratio and similarity-scaled perimeter.
perimeter_abc = 12 + 24 + 18
r_over_h = Fraction(24, perimeter_abc)
scale_3093 = 1 - r_over_h
print("3093", {"perimeter_ABC": perimeter_abc, "r_over_h": r_over_h,
               "similarity_scale": scale_3093, "perimeter_AMN": scale_3093 * perimeter_abc})

# 3125: an oblique plane z=mx+c gives semiaxes sqrt(1+m^2) and 1;
# the stated 3:2 axis ratio therefore takes minor diameter 2 to major 3.
minor_3125 = 2
major_3125 = Fraction(3, 2) * minor_3125
print("3125", {"minor_axis": minor_3125, "major_to_minor": Fraction(3, 2),
               "major_axis": major_3125})

# 5977: for the ordinary simple quadrilateral, A and D lie on the same
# side of BC; the perpendicular offset is 20-5 and the horizontal offset is 8.
square_5977 = 8**2 + (20 - 5)**2
print("5977", {"AD_squared": square_5977, "AD": isqrt(square_5977),
               "is_exact_square": isqrt(square_5977)**2 == square_5977})

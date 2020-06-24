# 3blue1brown - Overview of differential equations
import numpy as np
import argparse

# Physics constants
# Gravity
g = 9.8
# length
L = 2
# Air resistance
mu = 0.1

# Initial conditions
THETA = np.pi / 3 # 60 degrees
THETA_DOT = 0 # starting angular velocity

# Definition of ODE
def get_theta_double_dot(theta, theta_dot):
    return -mu * theta_dot - (g / L) * np.sin(theta)

# Solution to the differential equation
def theta(t):
    theta = THETA
    theta_dot = THETA_DOT
    delta_t = 0.01
    for time in np.arange(0, t, delta_t):
        theta_double_dot = get_theta_double_dot(theta, theta_dot)
        theta += theta_dot * delta_t
        theta_dot += theta_double_dot * delta_t
    return theta

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solve diff equation.')
    parser.add_argument(
        '-t',
        '--time',
        type=int,
        help='Sample time.',
        default=10
        )
    args = parser.parse_args()
    print(theta(args.time))
import numpy as np

class Fourier(object):
    """docstring for Fourier"""
    def __init__(self, time):
        self.rate = -1 * 2 * np.pi
        self.time = time

    def Series(self):
        pass

    def Transform(self):
        pass

    def Discrete(self, x):
        N = len(x)
        k = np.arange(N)
        e = np.cos(self.rate * k * self.time / N) + 1j*np.sin(self.rate * k * self.time / N)
        return (x * e)

    def complex_to_linear(self, x, d=3):
        return np.around(np.sqrt((x.real ** 2) + (x.imag ** 2)), d)
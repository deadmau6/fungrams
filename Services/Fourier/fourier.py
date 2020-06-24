import numpy as np
import math

class Fourier(object):
    """docstring for Fourier"""
    def __init__(self):
        self.rate = -2j * np.pi

    def Series(self):
        pass

    def Transform(self):
        pass

    def Discrete(self, x):
        N = x.shape[0]
        n = np.arange(N)
        k = n.reshape((N, 1))
        M = np.exp(self.rate * k * n / N)
        return np.dot(M, x)

    def Fast(self, x, vect=True):
        # Size of x.
        N = x.shape[0]
        # Find the nearest power of 2.
        lim = 2 ** int(math.log2(N))
        if vect:
            return self._fast_vectorization(x[:lim])
        else:
            return self._fast_recursion(x[:lim])

    def _fast_vectorization(self, x):
        N = min(x.shape[0], 16)

        n = np.arange(N)
        k = n[:, None]
        M = np.exp(self.rate * k * n / N)
        X = np.dot(M, x.reshape((N, -1)))

        while X.shape[0] < N:
            X_even = X[:, :X.shape[1] / 2]
            X_odd = X[:, X.shape[1] / 2:]
            factor = np.exp(-1j* np.pi * np.arange(X.shape[0]) / X.shape[0])[:, None]
            X = np.vstack([X_even + factor * X_odd, X_even - factor * X_odd])

        return X.ravel()

    def _fast_recursion(self, x):
        N = x.shape[0]
        if N <= 8:
            return self.Discrete(x)
        else:
            x_even = self._fast_recursion(x[::2])
            x_odd = self._fast_recursion(x[1::2])
            factor = np.exp(self.rate * np.arange(N) / N)
            return np.concatenate([x_even + factor[:N >> 1] * x_odd, x_even + factor[N >> 1:] * x_odd])

    def complex_to_linear(self, x, d=3):
        return np.around(np.sqrt((x.real ** 2) + (x.imag ** 2)), d)
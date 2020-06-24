import matplotlib.pyplot as pt
from fourier import Fourier
import numpy as np

t = np.arange(0.0, 8, 0.01)

print(t.shape[0])

s1 = np.sin(2 * np.pi * t)
s2 = np.cos(4 * np.pi * t) + s1
s3 = np.random.random(128)

jf = Fourier()

#f_s1 = jf.Fast(s1)
#f_s2 = jf.Fast(s2)
#f_s3 = jf.Fast(s3)
f_s1 = np.fft.fft(s1)
#f_s2 = np.fft.fft(s2)
f_s2 = jf.Fast(s2, vect=False)
f_s3 = np.fft.fft(s3)

m_s1 = jf.complex_to_linear(f_s1)
m_s2 = jf.complex_to_linear(f_s2)
m_s3 = jf.complex_to_linear(f_s3)

fig, ax = pt.subplots(3, 3)

ax[0, 0].plot(t, s1)

ax[0, 1].plot(t, s2)

ax[0, 2].plot(np.arange(s3.shape[0]), s3)

ax[1, 0].plot(f_s1.real, f_s1.imag)
ax[1, 0].set_aspect('equal', 'box')

ax[1, 1].plot(f_s2.real, f_s2.imag)
ax[1, 1].set_aspect('equal', 'box')

ax[1, 2].plot(f_s3.real, f_s3.imag)
ax[1, 2].set_aspect('equal', 'box')

ax[2, 0].plot(np.arange(m_s1.shape[0]), m_s1)
ax[2, 1].plot(np.arange(m_s2.shape[0]), m_s2)
ax[2, 2].plot(np.arange(m_s3.shape[0]), m_s3)
pt.show()
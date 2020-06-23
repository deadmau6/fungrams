import numpy as np

def scale_vector(scale, vect, ndigits=None):
	new_vect = [0] * len(vect)
	for i in range(0, len(vect)):
		if ndigits:
			new_vect[i] = round(vect[i] * scale, ndigits)
		else:
			new_vect[i] = vect[i] * scale
	return new_vect

def add_vectors(v, w):
	if len(v) != len(w):
		return "Error: vectors not correct size!"
	new_vect = [0] * len(v)
	for i in range(0, len(v)):
		new_vect[i] = v[i] +w[i]
	return new_vect

def dot_vect(v, w):
	if len(v) != len(w):
		return "Error: vectors not correct size!"
	res = 0
	for i in range(0, len(v)):
		res += v[i] * w[i]
	return res

def is_misclassified(y, x, w, b):
	sign = dot_vect(w, x) + b
	if y < 0:
		return sign < 0
	return sign > 0

if __name__ == '__main__':
	Xs = [[-1,1],[0,-1],[10,1]]
	Ys = [1, -1, 1]
	w = [0, 0]
	b = 0
	c = [False, False, False]
	i = 0
	while not all(c):
		y = Ys[i % len(Ys)]
		x = Xs[i % len(Xs)]
		if not c[i % len(c)]:
			w = add_vectors(w, scale_vector(y, x))
			b += y
		y_n = Ys[(i+1) % len(Ys)]
		x_n = Xs[(i+1) % len(Xs)]
		c[(i+1) % len(c)] = is_misclassified(y_n, x_n, w, b)
		i += 1
		print(i, w, b, all(c))



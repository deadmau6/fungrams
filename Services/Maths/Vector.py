
def add_vectors(v, w):

	if len(v) != len(w):

		return "Error: vectors not correct size!"

	new_vect = [0] * len(v)

	for i in range(0, len(v)):

		new_vect[i] = v[i] +w[i]

	return new_vect

def scale_vector(scale, vect, ndigits=None):
	
	new_vect = [0] * len(vect)

	for i in range(0, len(vect)):
		if ndigits:
			new_vect[i] = round(vect[i] * scale, ndigits)
		else:
			new_vect[i] = vect[i] * scale

	return new_vect

def linear_combination(scale_a, vect_a, scale_b, vect_b):
	return add_vectors(scale_vector(scale_a, vect_a), scale_vector(scale_b, vect_b))

def vector_span(v, w, limit=5):
	# The set of all possible linear_combinations
	l_span = set()
	for i in range(-limit, limit):
		for j in range(-limit, limit):
			l_span.add(tuple(linear_combination(i, v, j, w)))
	return l_span

def matrix_vector_multi(matrix, vect):
	# Also known as linear transform.
	if len(vect) != len(matrix[0]):

		return "Error: incorrect input format"

	new_vect = [0] * len(vect)

	for i in range(0, len(vect)):

		for j in range(0, len(vect)):
			new_vect[i] += matrix[j][i] * vect[j]

	return new_vect

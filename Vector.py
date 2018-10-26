
def add_vectors(v, w):

	if len(v) != len(w):

		return "Error: vectors not correct size!"

	new_vect = [0] * len(v)

	for i in range(0, len(v)):

		new_vect[i] = v[i] +w[i]

	return new_vect

def scale_vector(vect, scale):
	
	new_vect = [0] * len(vect)

	for i in range(0, len(vect)):

		new_vect[i] = vect[i] * scale

	return new_vect

def vector_matrix_multi(vect, matrix):
	
	if len(vect) != len(matrix[0]):

		return "Error: incorrect input format"

	new_vect = [0] * len(vect)

	for i in range(0, len(vect)):

		for j in range(0, len(vect)):

			new_vect[i] += matrix[j][i] * vect[j]

	return new_vect
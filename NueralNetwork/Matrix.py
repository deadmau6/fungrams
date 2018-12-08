from .Vector import matrix_vector_multi

def matrix_multi(m1, m2):
    if len(m1) != len(m2[0]):
        return "Error: incorrect input format"

    if len(m1[0]) != len(m2):
        return "Error: incorrect input format"
    
    m_new = []

    for i in range(0, len(m1)):
        m_new.append(matrix_vector_multi(m2, m1[i]))

    return m_new

def _determinant_2d(m):
    return m[0][0]*m[1][1] - m[0][1]*m[1][0] 

def determinant(matrix):
    if len(matrix) != len(matrix[0]):
        return "Error: incorrect input format"

    if len(matrix) == 2:
        return _determinant_2d(matrix)
    else:
        det = 0
        for a in range(0, len(matrix)):
            sub_m = []
            for i in range(0, len(matrix)):
                if i != a:
                    sub_m.append(matrix[i][1:])

            if a % 2 == 0:
                det = det + matrix[a][0]*determinant(sub_m)
            else:
                det = det - matrix[a][0]*determinant(sub_m)
        return det



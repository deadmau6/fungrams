from .Vector import matrix_vector_multi, scale_vector

def transpose(matrix):
    m_T = []
    for row in range(len(matrix[0])):
        m_T.append([])
        for col in range(len(matrix)):
            m_T[row].append(matrix[col][row])
    return m_T

def matrix_multi(m1, m2, ndigits=None):
    if len(m1) != len(m2[0]):
        return "Error: incorrect input format"

    if len(m1[0]) != len(m2):
        return "Error: incorrect input format"
    
    m_new = []

    for i in range(0, len(m1)):
        if ndigits:
            m_new.append([round(x, ndigits) for x in matrix_vector_multi(m2, m1[i])])
        else:
            m_new.append(matrix_vector_multi(m2, m1[i]))

    return m_new

def _determinant_2d(m):
    return m[0][0]*m[1][1] + -1*m[0][1]*m[1][0] 

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

def get_identity(n):
    identity = []
    for i in range(n):
        identity.append([1 if x == i else 0 for x in range(n)])
    return identity

def is_identity(m):
    for i in range(len(m)):
        for j in range(len(m)):
            if i == j and m[i][j] != 1:
                return False
            elif i != j and m[i][j] != 0:
                return False
    return True

def get_inverse(A, ndigits=None):
    
    if len(A) != len(A[0]):
        return "Error: matrix is not square"

    det = determinant(A)

    if det == 0:
        return "Error: There is no inverse b.c. det(A) = 0"

    if len(A) == 2:
        return _inverse_2d(A)
    else:
        adj_A = transpose(get_cofactor(A))
        return [ scale_vector(1/det, col, ndigits=ndigits) for col in adj_A]

def _inverse_2d(m):
    d = _determinant_2d(m)
    return [
        scale_vector(1/d, [m[1][1], -1*m[0][1]], ndigits=3),
        scale_vector(1/d, [-1*m[1][0], m[0][0]], ndigits=3),
    ]

def get_minor(col, row, m):
    index = -1
    minor = []
    for i in range(len(m)):
        if i == col:
            continue
        index += 1
        minor.append([])
        for j in range(len(m)):
            if j == row:
                continue
            minor[index].append(m[i][j])
    return minor

def get_cofactor(m):
    cof_m = []
    for i in range(len(m)):
        cof_m.append([])
        for j in range(len(m)):
            if (i+j) % 2 == 0:
                cof_m[i].append(determinant(get_minor(i, j, m)))
            else:
                cof_m[i].append(-1*determinant(get_minor(i, j, m)))
    return cof_m


import unittest
import Vector

class TestVector(unittest.TestCase):
    """docstring for TestVector"""
    def test_add_vectors(self):
        self.assertEqual(Vector.add_vectors([2,5],[3,4]), [5,9])
        self.assertEqual(Vector.add_vectors([-2,5],[3,-4]), [1,1])
        self.assertEqual(Vector.add_vectors([-2,-5],[-3,-4]), [-5,-9])
        self.assertEqual(Vector.add_vectors([0.2,0.5],[0.3,0.4]), [0.5,0.9])

    def test_scale_vector(self):
        self.assertEqual(Vector.scale_vector([2,5], 2), [4,10])
        self.assertEqual(Vector.scale_vector([2,5], -1), [-2,-5])
        self.assertEqual(Vector.scale_vector([2,5], 0.3), [0.6,1.5])

    def test_vector_matrix_multi(self):
        self.assertEqual(Vector.vector_matrix_multi([2,5], [[0,1],[1,0]]), [5,2])
        self.assertEqual(Vector.vector_matrix_multi([2,5], [[1,0],[0,1]]), [2,5])
        self.assertEqual(Vector.vector_matrix_multi([2,5], [[0,-1],[-1,0]]), [-5,-2])

if __name__ == '__main__':
    unittest.main()
import argparse
"""
 Source: https://www.youtube.com/watch?v=ZusiKXcz_ac
"""

def kth_bit(n, k, op='toggle'):
    if op == 'set':
        return n | (1 << k)
    if op == 'clear':
        return n & ~(1 << k)
    # Assume: Op == 'toggle'
    return n ^ (1 << k)

def bit_mask(n, mask, shift, w=0, op='extract'):
    if op == 'set':
        return (x & ~mask) | ((y << shift) & mask)
    # Assume: Op == 'extract'
    return (n & mask) >> shift

def bit_swap(a, b):
    # ACTUALLY SLOWER than the temp variable swap b.c. this is not parallelizable.
    # Mask of 1's where bits differ from a and b then stores the mask in a.
    a = a ^ b
    # Flip the bits in b that differ from a.
    b = a ^ b
    # Flip the bits in a that differ from b.
    a = a ^ b
    return a, b

def bit_min(a, b):
    """How it works:
     First we assume that (b < a) will return 1 for true and 0 for false.
     If b < a then -(b < a) => -1 which is all 1's, so a ^ ((b ^ a) & -1) == a ^ (b ^ a),
     Then from the 'bit_swap' that a ^ b ^ a = b
     If b >= a then -(b < a) => 0, so a ^ ((b ^ a) & 0) == a ^ 0 == a.
    """
    return a ^ ((b ^ a) & -(b < a))

def bit_mod_add(x, y, n):
    """How it works:
    """
    z = x + y
    return z - (n & -(z >= n))

def queens_problem():
    pass

def magic_triangle(arr, M):
    """Given a list of 6 integers that form a triangle[a-e], determine if there is a solution s.t.:
    (note [a, e, c] are corners of the triangle and [f, d, b] are intersects)
    Side 1:  a+b+c=M 
    Side 2:  c+d+e=M 
    Side 3:  e+f+a=M
    which => (a+b+c) + (c+d+e) + (e+f+a) = M+M+M => (a+b+c+d+e+f) + (a+c+e) = 3M.
    """
    order_arr = sorted(arr)
    print(order_arr)
    min_corners = sum(order_arr[0:3])
    max_corners = sum(order_arr[-3:])
    print(min_corners, max_corners)
    # (a+b+c+d+e+f)
    X = sum(order_arr)
    # (a+c+e)
    corners = 3*M - X
    return min_corners <= corners <= max_corners

if __name__ == "__main__":
    print(bit_min(5, 10))
    print(bit_min(5, -10))
    print(magic_triangle([1,2,3,4,5,6], 8))
    # 4, 5, 7, 8
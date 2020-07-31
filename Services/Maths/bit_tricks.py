import argparse, random
from pprint import pprint
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
    """NOTE: ~x + 1 = -x
    And least significant bit = x & (-x)
    """
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

def bit_bounds(a, b, op='min'):
    """How it works:
     First we assume that (b < a) will return 1 for true and 0 for false.
     If b < a then -(b < a) => -1 which is all 1's, so a ^ ((b ^ a) & -1) == a ^ (b ^ a),
     Then from the 'bit_swap' that a ^ b ^ a = b
     If b >= a then -(b < a) => 0, so a ^ ((b ^ a) & 0) == a ^ 0 == a.
    """
    if op == 'min':
        return a ^ ((b ^ a) & -(b < a))    
    return b ^ ((b ^ a) & -(b < a))

def bit_mod_add(x, y, n):
    """How it works:
     Assuming that r = (x + y) mod n and that 0 <= x < n and 0 <= y < n
     Unless n is a power of 2 the classic method will use division which is expensive.
     What we can do is first let z = x + y and now r = z if z < n else z-n.
     Problem is that this will create branches in the assembly and even worse this particular branching is unpredicable.
     However, we can use the same trick from 'bit_min' to solve this problem.
     So if -(z >= n) = -1 then n & -1 = n which => z - n. If -(z >= n) = 0 then n & 0 = 0 which => z. 
    """
    z = x + y
    return z - (n & -(z >= n))

def ciel_to_power_of_2(n, power=6):
    """Helpful notes:
     Recall that n - 1 flips the right most bit and pads the right with ones.
     So n = '1010 1000' then n-1 = '1010 0111', then we set n = n - 1.
     Now lets say m = n >> 1 so m = '0101 0011', notice the zero's is in the gap.
     Next we let n = n || m = '1010 0111' || '0101 0111' => '1111 0111'.
     Then we repeat x times, such that { n(i) = n(i) || (m(i) = n >> 2 ** i) for i in [0,1,...x-1,x] }.
     Because we use the 'or' operator at each iteration, 'n' ones will just be padded to the right.
     In the end we should have n = '0000 1111 1111'and n+1 = '0001 0000 0000' = 256.
    """
    n -= 1
    # max power of 2 is 2^power
    for i in range(power):
        ### if power == 6 this is what will run:
        # n |= n >> 1
        # n |= n >> 2
        # n |= n >> 4
        # n |= n >> 8
        # n |= n >> 16
        # n |= n >> 32
        ###
        n |= n >> 2 ** i
    return n+1

def log2_power2(n):
    """ Find the log base 2 of a power of 2. (so n must be a power of 2).
    A deBruijn sequence 's' of length 2^k is a cyclic '0'-'1' sequence such that each of the
    2^k 0-1 strings of length k occurs exactly once as a substring of 's'.

    Example: s = 00011101 and k = 3
    --------------------------------
    i | 00011101   | x
    0 | 000        | 0
    1 |  001       | 1
    2 |   011      | 3
    3 |    111     | 7
    4 |     110    | 6 
    5 |      101   | 5
    6 |       010  | 2
    7 |        100 | 4
    --------------------------------
    Then create a convert table of length 2^k that represents the index 'i' of s given the value 'x' which is the substring of s of length k.
    So convert = [0,1,6,2,7,5,4,3], and convert[x] = i :
    ___________________________________
    x | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
    --|---|---|---|---|---|---|---|---|
    i | 0 | 1 | 6 | 2 | 7 | 5 | 4 | 3 |
    -----------------------------------

    Now recall that n is a power of 2 and we are looking for log2(n) = z such that 2^z = n.
    Suppose n = 16 and because n is a power of 2 we can do s * n => s << z, so :
    '0001 1101' * 16 = '1101 0000' now we wanna find the deBruijn value at the top of this sequence.
    To do that we can right shift the sequence by 5(?idk maybe bc 3 is not a power of 2): '1101 0000' >> 5 = 6.
    And now that we have the shift result we can look up the index where this result originally appeared in the sequence!
    convert[6] = 4 => log2(16) = 4 => 2^4 = 16.

    NOTE: This only works with a specific deBruijn sequence because that will give us a specific convert table!
    The previous example was just a subsection of that sequence but the convert tables are different(as you'll see).
    """
    # A deBruijn sequence of length 2^k, where k = 8 so n must be less than 64.
    deBruijn = 0x022fdd63cc95386d
    convert = [
        0,   1,  2, 53,  3,  7, 54, 27,
        4,  38, 41,  8, 34, 55, 48, 28,
        62,  5, 39, 46, 44, 42, 22,  9,
        24, 35, 59, 56, 49, 18, 29, 11,
        63, 52,  6, 26, 37, 40, 33, 47,
        61, 45, 43, 21, 23, 58, 17, 10,
        51, 25, 36, 32, 60, 20, 57, 16,
        50, 31, 19, 15, 30, 14, 13, 12
    ]
    return convert[(n * deBruijn) >> 58]

def queens_problem(n):
    """Given an n x n grid, place n queens s.t. no two queens are in the same row, column, or diagonal.
    This problem is solved with backtracking search but we can represent the grid in a helpful way using only 3 bit vectors.
    So we create 3 bit vectors of size n, 2n - 1 and 2n - 1.
    Example n = 4:
    --------------------------------------------------
        Down(size n)    Left(2n - 1)    Right(2n - 1)
        [_][_][q][_]   0[_][_][q][_]    [_][_][q][_]0
        [q][_][_][_]   1[q][_][_][_]    [q][_][_][_]1
        [_][_][_][q]   1[_][_][_][q]    [_][_][_][q]1
        [_][q][_][_]   0[_][q][_][_]    [_][q][_][_]0
         1  1  1  1      1  1  0            0  1  1
    --------------------------------------------------
    Down, stores a 1 for each column with a queen and a 0 otherwise, checking column c is safe if down & (1 << c) == 0.
    Left, stores a 1 for each right-left diagonal with a queen, checking row r and column c is safe if left & (1 << (r+c)) == 0.
    Right, stores a 1 for each left-right diagonal with a queen, checking row r and column c is safe if right & (1 << (n-1-r+c)) == 0.
    """
    pass

def population_count(n, op=None):
    """ Count the number of 1 bits in word n.
    Also you can use this to find log2_power2(n) by doing population_count(n-1)
    """
    if op == 'mask':
        # 0^32 1^32
        M5 = ~((-1) << 32)
        # 0^32 1^32
        M4 = M5 ^ (M5 << 16)
        # 0^32 1^32
        M3 = M4 ^ (M4 << 8)
        # 0^32 1^32
        M2 = M3 ^ (M3 << 4)
        # 0^32 1^32
        M1 = M2 ^ (M2 << 2)
        # (01)32
        M0 = M1 ^ (M1 << 1)
        # Computes Count
        n = ((n >> 1) & M0) + (n & M0)
        n = ((n >> 2) & M1) + (n & M1)
        n = ((n >> 4) + n) & M2
        n = ((n >> 8) + n) & M3
        n = ((n >> 16) + n) & M4
        n = ((n >> 32) + n) & M5
        return n
    if op == 'lookup':
        count_table = [
                0, 1, 1, 2, 1, 2, 2, 3,
                1, 2, 2, 3, 2, 3, 3, 4,
                1, 2, 2, 3, 2, 3, 3, 4,
                2, 3, 3, 4, 3, 4, 4, 5,
                1, 2, 2, 3, 2, 3, 3, 4,
                2, 3, 3, 4, 3, 4, 4, 5,
                2, 3, 3, 4, 3, 4, 4, 5,
                3, 4, 4, 5, 4, 5, 5, 6,
                1, 2, 2, 3, 2, 3, 3, 4,
                2, 3, 3, 4, 3, 4, 4, 5,
                2, 3, 3, 4, 3, 4, 4, 5,
                3, 4, 4, 5, 4, 5, 5, 6,
                2, 3, 3, 4, 3, 4, 4, 5,
                3, 4, 4, 5, 4, 5, 5, 6,
                3, 4, 4, 5, 4, 5, 5, 6,
                4, 5, 5, 6, 5, 6, 6, 7,
                1, 2, 2, 3, 2, 3, 3, 4,
                2, 3, 3, 4, 3, 4, 4, 5,
                2, 3, 3, 4, 3, 4, 4, 5,
                3, 4, 4, 5, 4, 5, 5, 6,
                2, 3, 3, 4, 3, 4, 4, 5,
                3, 4, 4, 5, 4, 5, 5, 6,
                3, 4, 4, 5, 4, 5, 5, 6,
                4, 5, 5, 6, 5, 6, 6, 7,
                2, 3, 3, 4, 3, 4, 4, 5,
                3, 4, 4, 5, 4, 5, 5, 6,
                3, 4, 4, 5, 4, 5, 5, 6,
                4, 5, 5, 6, 5, 6, 6, 7,
                3, 4, 4, 5, 4, 5, 5, 6,
                4, 5, 5, 6, 5, 6, 6, 7,
                4, 5, 5, 6, 5, 6, 6, 7,
                5, 6, 6, 7, 6, 7, 7, 8
            ]
        r = 0
        while n != 0:
            r += count_table[n & 255]
            n >>= 8
        return r
    r = 0
    while n != 0:
        r += 1
        n &= n - 1
    return r

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

def get_seq(x):
    seq = [i+1 for i in range(x)]
    for i in range(x-1, 1, -1):
        r = random.randint(0, i)
        if r == i:
            continue
        temp = seq[i]
        seq[i] = seq[r]
        seq[r] = temp
    return seq

def select_strat(p, seq):
    n = int(len(seq)/2)
    p_index = p
    for i in range(n):
        if seq[p_index-1] == p:
            return True
        p_index = seq[p_index-1]
    return False

def get_cycles(seq):
    indexes = set([_ for _ in range(len(seq))])
    curr = []
    cycles = []
    i = indexes.pop()
    while True:
        val = seq[i]
        if len(indexes) == 0:
            curr.append(val)
            cycles.append(curr)
            break
        elif val in curr:
            cycles.append(curr)
            curr = []
            i = indexes.pop()
        else:
            curr.append(val)
            indexes.discard(val-1)
            i = val - 1
    print(i)
    return cycles

def josephus(arr):
    if len(arr) == 1:
        return arr[0]
    remain = []
    for i in range(0, len(arr), 2):
        val = arr[i]
        if val not in remain:
            if i == len(arr)-1:
                remain.insert(0, val)
            else:
                remain.append(val)
    return josephus(remain)

def pseudo_gradient_descent(point, step_size, threshold):
    # step_size or "learning rate" are better if they are small but take longer to converge.
    value = f(point)
    new_point = point - step_size * gradient(point)
    new_value = f(new_point)
    if abs(new_value - value) < threshold:
        return value
    return pseudo_gradient_descent(new_point, step_size, threshold)

def init_primes(limit=1000):
    # sieve_of_eratosthenes
    marked = []
    p = 2
    while p ** 2 <= limit:
        if p not in marked:
            for i in range(p**2, limit+1, p):
                marked.append(i)
        p += 1
    primes = [x for x in range(2, limit) if x not in marked]
    return primes

def is_prime(num, primes=[]):
    if num in primes:
        return True
    if num < 2:
        return False
    if num % 2 == 0 or num % 3 == 0:
        return False
    p = 5
    while p ** 2 <= num:
        if num % p == 0 or num % (p + 2) == 0:
            return False
        p += 6
    #primes.append(num)
    return True

if __name__ == "__main__":
    #print(bit_bounds(5, 10))
    #print(bit_bounds(5, -10))
    #print(magic_triangle([1,2,3,4,5,6], 8))
    #print(ciel_to_power_of_2(68))
    #print(log2_power2(16))
    #print(population_count(255))
    #print(population_count(255, 'lookup'))
    #print(population_count(255, 'mask'))
    #s = get_seq(10)
    #print(s)
    #cs = get_cycles(s)
    #print(cs)
    #res = []
    #for i in range(1, 11):
    #    res.append((i, select_strat(i, s)))
    #print(res)
    table = {}
    for n in range(1, 25):
        arr = [i+1 for i in range(n)]
        table[n] = josephus(arr)
    #n = 9
    #arr = [i+1 for i in range(n)]
    #table[n] = josephus(arr)
    pprint(table)

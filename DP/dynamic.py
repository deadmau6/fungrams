import numpy as np
import cv2 as cv
import math, re

class Dynamic:
    
    @staticmethod
    def sum_subset(N, S, i=0):
        """Given a set of non-negative integers S and a value sum N.
        Determine if there exists a subset of integers in S that add up to integer N.
        If no such set exists, return 0, otherwise return the number of subsets that sum to N.
        """
        if N == 0:
            return 1

        # no possible subset was found.
        if i == len(S):
            return 0
        
        a = S[i]

        if a > N:
            return Dynamic.sum_subset(N, S, i + 1)

        return Dynamic.sum_subset(N, S, i + 1) + Dynamic.sum_subset(N-a, S, i + 1)

    @staticmethod
    def fibonacci(N):
        """Given the number N, calculate the fibonacci sequence until N.
        """
        if N == 1:
            return 1
        
        if N < 1:
            return 0

        return Dynamic.fibonacci(N-1) + Dynamic.fibonacci(N-2)

    @staticmethod
    def LCS(X, Y, m, n):
        """ Given two character sequences X and Y, find the longest common subsequence.
        Note that comparison between characters in the sequences is in fact case sensitive!
        """
        L = [[0]*(n+1) for i in range(m+1)]
        for i in range(m+1):
            for j in range(n+1):
                if i == 0 or j == 0:
                    L[i][j] = 0
                elif X[i-1] == Y[j-1]:
                    L[i][j] = L[i-1][j-1] + 1
                else:
                    L[i][j] = max(L[i-1][j], L[i][j-1])
        
        lcs = []
        i = m
        j = n
        while i > 0 and j > 0:
            if X[i-1] == Y[j-1]:
                lcs.append(X[i-1])
                i-=1
                j-=1
            elif L[i-1][j] > L[i][j-1]:
                i-=1
            else:
                j-=1
        return ''.join(lcs[::-1])

    @staticmethod
    def similarity_seq_image(text_file):
        with open(text_file, 'r') as f:
            data = f.read().lower()
        
        seq = re.split(r"\W+", data)
        s = len(seq)
        ksize = math.ceil(800/s)
        d = s * ksize

        img = np.full((d+1 , d+1, 3), 255, np.uint8)
        print(img.shape)
        for i in range(0, d, ksize):
            r = 128 + (i % 128)
            for j in range(0, d, ksize):
                b = 128 + (j % 128)
                if seq[(j % s)] == seq[(i % s)]:
                    g = r + b if r + b > 255 else 255
                    img[i:i + ksize, j:j + ksize] = [r, g, b]
                    img[i,j] = 0
                    

        cv.imshow('image', img)
        cv.waitKey(0)
        cv.destroyAllWindows()

    def start(self, args):
        if args.sum_subset:
            subset = set()
            s_val, n_val = args.sum_subset
            for n in s_val.split(','):
                subset.add(int(n, 10))
            n_sum = int(n_val, 10)
            print(Dynamic.sum_subset(n_sum, list(subset)))
        elif args.fib:
            print(Dynamic.fibonacci(args.fib))
        elif args.lcs:
            s1 = list(args.lcs[0])
            s2 = list(args.lcs[1])
            subseq = Dynamic.LCS(s1, s2, len(s1), len(s2))
            print(f"Found LCS: {subseq}\nLCS Length: {len(subseq)}")
        elif args.word_image:
            Dynamic.similarity_seq_image(args.word_image)
        else:
            print(Dynamic.fibonacci(10))

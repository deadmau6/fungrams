import numpy as np
import cv2 as cv
from pprint import pprint
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
    def minimum_edit_distance(X, Y):
        """ Given the string X and Y, calculate the Levenshtien distance from X to Y. Note that the
        Levenshtien distance gives a weight of 1 for inserting/deleting characters and a weight of 2
        for substituting characters.(Resource: https://youtu.be/Q7QQCNM7AJ4)
        """
        m = len(X)
        n = len(Y)
        d = [[0 for x in range(n+1)] for y in range(m+1)]
        for i in range(m+1):
            for j in range(n+1):
                if j == 0:
                    d[i][0] = i
                elif i == 0:
                    d[0][j] = j
                else:
                    l = 0 if X[i-1] == Y[j-1] else 2
                    d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + l)
        #pprint(Dynamic._backtrace_edit_distance(d))
        return d[m][n]

    @staticmethod
    def _backtrace_edit_distance(dsts):
        backtrace = []
        i = len(dsts) - 1
        j = i
        while i >= 0:
            curr = dsts[i][j]
            backtrace.append(curr)
            left = dsts[i][j-1] + curr
            down = dsts[i-1][j] + curr
            diag = dsts[i-1][j-1] + curr
            if left < down and left < diag:
                j -= 1
            elif down < left and down < diag:
                i -= 1
            else:
                i -= 1
                j -= 1
        return backtrace

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
        """Given a text file, create a self similarity matrix based on the words in the text file.
        The matrix is then converted into an image using opencv, each pixel represents a word match
        and the color is just a random gradient. Note: the pixel opacity is set by a strength modifier,
        which represents word sequences. This helps eliminate excess noise caused by common words like
        'the' or 'a' and it highlights repetitiveness.
        (Resource: https://www.youtube.com/watch?v=_tjFwcmHy5M)
        """
        with open(text_file, 'rb') as f:
            data = f.read().decode('utf-8', 'ignore').lower()
        
        seq = re.split(r"[^a-z']+", data)
        s = len(seq)
        ksize = math.ceil(800/s)
        d = s * ksize
        win = [x+1 for x in range(2)]
        color_grad  = math.ceil(s/255)

        img = np.full((d+1 , d+1, 4), 255, np.uint8)
        r = 0
        RED = 0
        BLUE = 0
        GREEN = 255
        for i in range(s):
            c = -ksize
            RED = RED + color_grad if i % color_grad == 0 else RED
            for j in range(s):
                c += ksize
                if seq[j] != seq[i]:
                    continue

                if j == i:
                    BLUE += 1
                    GREEN -= 1
                    img[r:r+ksize, c:c+ksize] = [RED, GREEN, BLUE, 0]
                    continue

                strength = 0
                for w in win:
                    if j+w < s:
                        if seq[j+w] == seq[j]:
                            strength += 63

                        if i+w < s and seq[j+w] == seq[i+w]:
                            strength += 63

                    if j-w > 0:
                        if seq[j-w] == seq[j]:
                            strength += 63

                        if i-w > 0 and seq[j-w] == seq[i-w]:
                            strength += 63
                
                if strength < 63:
                    continue

                val = 252 - strength
                img[r:r+ksize, c:c+ksize] = [RED, GREEN, BLUE, val]
                #if val-RED >= 0 and val+RED <= 255:
                #    val_r, val_b = (val-RED, val+RED ) 
                #    img[r:r+ksize, c:c+ksize] = [val_r, val, val_b, val]
                #else:
                #    img[r:r+ksize, c:c+ksize] = [RED, 0, 255, val]
                
            r += ksize

        print(img.shape, s, ksize)

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
        elif args.edit_distance:
            s1 = args.edit_distance[0]
            s2 = args.edit_distance[1]
            print(Dynamic.minimum_edit_distance(s1, s2))
        else:
            print("No function specified.")

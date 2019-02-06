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
        else:
            print('done')

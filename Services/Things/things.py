import random

class Things:
    """Things is a random assortment of programs, utilities, and games."""

    @staticmethod
    def pennys_game():
        """Penny's Game is sequence generating game between two players in which,
        player A selects a binary sequence of length 3 and then player B picks a
        different sequence and whose sequence appears first wins. For simplicity
        this version converts the binary sequence to an integer value so both
        players pick a number from 0 to 7.
        """
        choice = {
            '111' : 3,
            '110' : 3,
            '101' : 6,
            '100' : 6,
            '011' : 1,
            '010' : 1,
            '001' : 4,
            '000' : 4
        }
        print("Guess a number from 0 - 7:")
        usr_msg = input()
        usr_guess = int(usr_msg, 10)
        usr_guess_bits = format(usr_guess, '0>3b')
        my_guess = choice[usr_guess_bits]
        print(f"Okay my guess is {my_guess}")
        while True:
            try:
                r = random.getrandbits(3)
                print(r)
                if r == usr_guess:
                    print("You Won!")
                    break
                if r == my_guess:
                    print("I Won!")
                    break
            except KeyboardInterrupt:
                print('Exiting...')
                break

    @staticmethod
    def read_section(fname, start, end):
        """This reads a section of bytes from a file and then returns a array of bytes split by 
        the newline character. 
        """
        with open(fname, 'rb') as f:
            f.seek(start, 0)
            sect = f.read(end - start)
        return sect.split(b'\n')

    @staticmethod
    def gauss_trick(start, end):
        """ The Gauss trick is used to quickly find the sum of a given sequence (N).
        The sequence must be comprised of whole numbers and must be a range that increments
        by one, or N = start + (start + 1) + (start + 2) + (start + 3)... + end.
        """
        if start < end:
            print(int((start + end) * ((end - start + 1) / 2)))
        else:
            print("Invalid range, the start must be less than the end.")

    def start(self, args):
        if args.pennys_game:
            Things.pennys_game()
        elif args.gauss_trick:
            Things.gauss_trick(args.start, args.end)

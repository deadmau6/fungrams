import re
from collections import deque

class CodeBook:
    """Some implementations from the book The Code Book by Simon Singh."""
    allowed_methods = ['rail_fence', 'caesar_cipher']
    
    @staticmethod
    def _derail_fence(msg, rows, lead):
        corrected = ['' for _ in range(len(msg))]
        starts = deque([(lead - 1 + j) % rows for j in range(rows)])
        i = starts.popleft()
        for c in msg:
            if i < len(corrected):
                corrected[i] = c
            else:
                i = starts.popleft()
                corrected[i] = c
            i += rows
        return ''.join(corrected), {'rows': rows, 'lead': lead}

    @staticmethod
    def rail_fence(msg, encrypt, verbose, args={}):
        """ Rail Fence Cipher or Zig-Zag Cipher.
        The rail fence cipher is a transpose cipher in which the plain text is written with alternating letters on seperate lines(or rails).
        The first letter starts at the top rail the second letter on the rail below the next letter on the rail below that and so on, until
        you hit the bottom rail then the letters are placed on the rail above until you hit the top. This repeats for the entire message
        then, finally each rail is concatenated to create the scrambled message. For example, lets use three rows (rows=3) for the message
        'we the people' the rows would look like this:
            W . . H . . E . . L .
            . E . . E . . O . . E
            . . T . . P . . P . .
        Then if we say the lead row for conacatenating is 1 (lead=1) then the final message looks like this: 'WHELEEOETPP'.
        Remeber, in order for this cipher to be useable only the sender and the recipient need to know the rows and lead.
        """
        rows = int(args.get('rows', '2'))
        lead = int(args.get('lead', '1'))
        keep_case = args.get('keep_case', 'True')=='True'
        #
        msg = re.sub(r'\s+', '', msg)
        if not keep_case:
            msg = msg.lower()
        #
        if not encrypt:
            return CodeBook._derail_fence(msg, rows, lead)
        #
        scramble = []
        for i in range(rows):
            start = (lead-1 + i) % rows
            scramble += [msg[j] for j in range(start, len(msg), rows)]
        #
        return ''.join(scramble), {'rows': rows, 'lead': lead}

    @staticmethod
    def caesar_cipher(msg, encrypt, verbose, args={}):
        """ The Caesar Shift or the Caesar Cipher and its variants.
        The Caesar Cipher is a substitution cipher in which each letter in the alphabet is mapped to another letter creating a new cipher alphabet.
        The plain text message is then encrypted by substituting each letter to its corrisponding letter in the cipher alphabet. It is important to
        note that this mapping from the original alphabet to our cipher alphabet must be one-to-one and it is our KEY! Also there are 3 methods to
        create this key and some of them are stronger than others.
        
        Method 1) Shift: we can simply shift our cipher alphabet to a certain degree relative to the original alphabet. For example, if we say
        `shift = 1` then our mapping(key) from original to cipher will be `a = B`, `b = C`, `c = D`, ..., `z = A`. Then our original message "hello"
        will be encrypted to "ifmmp". The problem with this method is we can only create 25 different keys because we are restricted by the length of
        the alphabet. However the key size is very small it's just the shift degree.

        Method 2) Unordered substitution: in this method we define a direct substitution for each letter in the original alphabet to another random
        letter. For example, we can arbitrarily say `a = X`, `b = B`, `c = O`, ... `z = Y`, but each mapping must be one-to-one meaning no two elements
        in the original can map to the same element in the cipher (like `a = X`, `g = X`) or else the decryption won't work. This method is much more
        powerful and can create 4 x 10^10 potential keys! However the key has to be the complete mapping therefore our key size must be the length of
        the alphabet.

        Method 3) Keyphrase substitution: in this method we establish a key phrase that will act as a prefix to the cipher alphabet. Then the remaining
        cipher alphabet continues in the original order but it will skip over letters that appear in the prefix. Also in order to maintain a one-to-one
        mapping, any duplicates in the keyphrase are removed but order is maintained. For example, our `keyphrase='JULIUS CAESAR'` this then gets
        reduced to 'JULISCAER' as our prefix. Then the remaining cipher alphabet is filled in such that final letter in the prefix determines the
        starting point in the original alphabet and letters in the prefix are not added. So the complete cipher alphabet looks like this:
        'JULISCAERTVWXYZBDFGHKMNOPQ'. This method is the best because the arrangement of the cipher alphabet is some what random so the number of
        potentail keys is 4 x 10^10, but the key size can be smaller and more memorable.

        Parameters:
         * `sub=(string)` - optional.
         * `shift=(integer)` - optional.
         * `keyphrase=(string)` - optional.
         * Default is `shift=3` the params used resolve in this order: `keyphrase`, `sub`, `shift`. So if you enter a `keyphrase` and `sub` then only
         the `keyphrase` is used, if you enter a `sub` and a `shift` then only the `sub` is used.
        """
        
        alphabet = [ _ for _ in 'abcdefghijklmnopqrstuvwxyz']
        cipher_alphabet = []
        #
        keyphrase = args.get('keyphrase')
        sub = args.get('sub')
        shift = int(args.get('shift', '3')) % len(alphabet)
        # Method 3
        if keyphrase:
            # create/clean the prefix
            for letter in keyphrase.lower():
                if letter in alphabet and letter not in cipher_alphabet:
                    cipher_alphabet.append(letter)
            # finish the cipher
            last = alphabet.index(cipher_alphabet[-1])
            for i in range(len(alphabet)):
                index = (last + i) % len(alphabet)
                if alphabet[index] not in cipher_alphabet:
                    cipher_alphabet.append(alphabet[index])
        # Method 2
        elif sub:
            cipher_alphabet = [letter for letter in sub.lower() if letter in alphabet]
        # Method 1
        else:
            for i in range(len(alphabet)):
                index = (shift + i) % len(alphabet)
                cipher_alphabet.append(alphabet[index])
        #
        if verbose >= 1:
            print(f"Origin: {' '.join(alphabet)}.")
            print(f"Cipher: {' '.join(cipher_alphabet)}.")
        #
        if encrypt:
            cipher_map = { k: v for k,v in zip(alphabet, cipher_alphabet) }
        else:
            cipher_map = { k: v for k,v in zip(cipher_alphabet, alphabet) }
        #
        output = [cipher_map.get(letter, letter) for letter in msg.lower()]
        return ''.join(output), {'keyphrase': keyphrase, 'sub': sub, 'shift': shift}

    @staticmethod
    def start(args):
        #
        usr_args = {}
        if args.params:
            for param in args.params:
                k, v = param.split('=', maxsplit=1)
                usr_args[k.strip()] = v.strip()
        #
        cipher = getattr(CodeBook, args.cipher, None)
        if cipher:
            out, params = cipher(args.message, args.encrypt, args.verbose, args=usr_args)
            if args.verbose >= 2:
                print(cipher.__doc__)
            if args.verbose >= 1:
                print(f"Params: {params}")
            print(f"Result: {out}")
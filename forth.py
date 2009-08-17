#!/usr/bin/env python


import sys


def is_int(x):
    try:
        int(x)
        return True
    except ValueError:
        return False


class Forth:
    
    def __init__(self):
        self.stack = []
        self.state = 0
        self.def_stack = []
        self.dot_quote_stack = []
        
        # @@@ at the moment, this is a dict in the python sense and doesn't
        # allow multiple definitions of a word the way Forth does
        self.dictionary = {}
        
        # because some parts of Forth need to refer to things by address, here
        # is an index-addressable memory. eventually the dictionary and stack
        # may actually go this way too (and interesting impedence mis-match
        # implementing a low-level language on top of a high-level language)
        self.memory = [0] * 256
        
    def add(self, name, value):
        if callable(value):
            # version of func that operates on stack
            def stack_func():
                num_args = value.func_code.co_argcount
                self.stack, args = self.stack[:-num_args], self.stack[-num_args:]
                self.stack.extend(value(*args) or tuple())
            self.dictionary[name] = stack_func
        else:
            self.dictionary[name] = value
    
    def execute(self, token_list):
        for token in token_list:
            if self.state == 0:
                if token in self.dictionary:
                    word = self.dictionary[token]
                    if callable(word):
                        word()
                    else:
                        self.execute(word)
                elif is_int(token):
                    self.stack.append(int(token))
                elif token == ":":
                    self.state = 1
                elif token == "(":
                    self.state = 3
                elif token == '."':
                    self.state = 4
                elif token == "!":
                    # because this needs memory access, it's not a normal
                    # dictionary word (yet)
                    addr = self.stack.pop()
                    value = self.stack.pop()
                    self.memory[addr] = value
                elif token == "@":
                    # because this needs memory access, it's not a normal
                    # dictionary word (yet)
                    addr = self.stack.pop()
                    value = self.memory[addr]
                    self.stack.append(value)
                else:
                    print "UNKNOWN TOKEN: %s" % token
            elif self.state == 1:
                name = token
                self.state = 2
            elif self.state == 2:
                if token == ":":
                    print ": INSIDE :"
                elif token == ";":
                    self.dictionary[name] = self.def_stack[:]
                    self.def_stack = []
                    self.state = 0
                else:
                    self.def_stack.append(token)
            elif self.state == 3: # comment
                if token == ")":
                    self.state = 0
            elif self.state == 4: # dot-quote
                if token == '"':
                    sys.stdout.write(" ".join(self.dot_quote_stack))
                    self.dot_quote_stack = []
                    self.state = 0
                else:
                    self.dot_quote_stack.append(token)
            else:
                print "UNKNOWN STATE: %s" % self.state


forth = Forth()

forth.add("+", lambda x, y: (x + y,))
forth.add("-", lambda x, y: (x - y,))
forth.add("*", lambda x, y: (x * y,))
forth.add("/", lambda x, y: (x / y,))
forth.add("/MOD", lambda x, y: divmod(x, y)[::-1])
forth.add("MOD", lambda x, y: (x % y,))
forth.add("SWAP", lambda n1, n2: (n2, n1))
forth.add("DUP", lambda n: (n, n))
forth.add("OVER", lambda n1, n2: (n1, n2, n1))
forth.add("ROT", lambda n1, n2, n3: (n2, n3, n1))
forth.add("DROP", lambda n: None)

# words that can't be defined as a stack-expression

def spaces(n):
    sys.stdout.write(" " * n)

def emit(c):
    sys.stdout.write(chr(c))

def bye():
    sys.exit(0)

def dot(n):
    sys.stdout.write(str(n) + " ")
    
forth.add("SPACES", spaces)
forth.add("EMIT", emit)
forth.add("BYE", bye)
forth.add(".", dot)


# words defined in terms of other words
    
forth.add("CR", ["13", "EMIT", "10", "EMIT"])


while True:
    line = raw_input("> ")
    forth.execute(line.split())
    print "ok"

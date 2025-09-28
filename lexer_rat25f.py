import sys
from enum import Enum, auto
from typing import Tuple, Optional, List

class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    REAL = auto()
    OPERATOR = auto()
    SEPARATOR = auto()
    STRING = auto()
    COMMENT = auto()
    EOF = auto()
    UNKNOWN = auto()

KEYWORDS = {
    "while", "if", "else", "for", "int", "float", "bool", "true", "false",
    "function", "return", "read", "write", "then", "fi", "do", "od"
}

SEPARATORS = {
    "(", ")", "{", "}", "[", "]", ",", ";", ":"
}

MULTI_CHAR_OPS = {"<=", ">=", "==", "!=", "&&", "||"}
SINGLE_CHAR_OPS = {"+", "-", "*", "/", "%", "=", "<", ">", "!"}

def is_letter(ch: str) -> bool:
    return ch.isalpha()

def is_digit(ch: str) -> bool:
    return ch.isdigit()

def is_alnum(ch: str) -> bool:
    return ch.isalnum()

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)

    def peek(self, k: int = 0) -> str:
        idx = self.i + k
        if idx < self.n:
            return self.text[idx]
        return ""

    def advance(self, steps: int = 1) -> None:
        self.i += steps

    def eof(self) -> bool:
        return self.i >= self.n

    def skip_whitespace(self):
        while not self.eof() and self.peek().isspace():
            self.advance()

    def skip_comments(self) -> Optional[Tuple[TokenType, str]]:
        """
        Handles // line comments and /* ... */ block comments.
        Returns a COMMENT token tuple if a full comment is consumed,
        otherwise None (no comment at current position).
        """
        if self.peek() == "/" and self.peek(1) == "/":
            start = self.i
            while not self.eof() and self.peek() != "\n":
                self.advance()
            lexeme = self.text[start:self.i]
            return (TokenType.COMMENT, lexeme)

        if self.peek() == "/" and self.peek(1) == "*":
            start = self.i
            self.advance(2) 
            while not self.eof() and not (self.peek() == "*" and self.peek(1) == "/"):
                self.advance()
            if not self.eof():
                self.advance(2) 
            lexeme = self.text[start:self.i]
            return (TokenType.COMMENT, lexeme)

        return None

    def lex_identifier(self) -> Optional[Tuple[TokenType, str]]:
        """
        IDENTIFIER DFA (explicit):
          State S0: if letter -> S1 else reject
          State S1: while (letter or digit or '_') stay in S1
          Accepting state: S1
        Note: First char must be a letter. After that, underscores allowed.
        """
        if not is_letter(self.peek()):
            return None

        start = self.i
        self.advance()
        while not self.eof():
            ch = self.peek()
            if is_alnum(ch) or ch == "_":
                self.advance()
            else:
                break

        lexeme = self.text[start:self.i]
        if lexeme in KEYWORDS:
            return (TokenType.KEYWORD, lexeme)
        return (TokenType.IDENTIFIER, lexeme)

    def lex_integer(self) -> Optional[Tuple[TokenType, str]]:
        """
        INTEGER DFA (explicit):
          Regex: 0 | [1-9][0-9]*
          States:
            S0: if '0' -> accept '0' (S1), else if [1-9] -> S2, else reject
            S2: while digit -> stay S2
          Accepting states: S1, S2
        """
        if not is_digit(self.peek()):
            return None

        start = self.i

        if self.peek() == "0":
            self.advance()
            if self.peek() != ".":
                return (TokenType.INTEGER, self.text[start:self.i])
            else:
                self.i = start
                return None

        if self.peek() in "123456789":
            self.advance()
            while not self.eof() and is_digit(self.peek()):
                self.advance()
            if self.peek() == ".":
                self.i = start
                return None
            return (TokenType.INTEGER, self.text[start:self.i])

        return None

    def lex_real(self) -> Optional[Tuple[TokenType, str]]:
        """
        REAL DFA (explicit, simplified):
          Regex (simplified):  [0-9]+ '.' [0-9]+ ( [eE] [+-]? [0-9]+ )?
          Strategy: parse integral part, dot, fractional part, optional exponent.

          This requires at least one digit before and after the dot.
        """
        start = self.i
        i0 = self.i

        if not is_digit(self.peek()):
            return None
        while not self.eof() and is_digit(self.peek()):
            self.advance()

        if self.peek() != ".":
            self.i = i0
            return None
        self.advance()  

        if not is_digit(self.peek()):
            self.i = i0
            return None
        while not self.eof() and is_digit(self.peek()):
            self.advance()

        if self.peek() in ("e", "E"):
            self.advance()
            if self.peek() in ("+", "-"):
                self.advance()
            if not is_digit(self.peek()):
                self.i = i0
                return None
            while not self.eof() and is_digit(self.peek()):
                self.advance()

        return (TokenType.REAL, self.text[start:self.i])

    # ---------------- String literal ----------------
    def lex_string(self) -> Optional[Tuple[TokenType, str]]:
        if self.peek() != '"':
            return None
        start = self.i
        self.advance() 
        while not self.eof() and self.peek() != '"':
            if self.peek() == "\n":
                break
            self.advance()
        if self.peek() == '"':
            self.advance() 
        return (TokenType.STRING, self.text[start:self.i])

    def lex_operator_or_separator(self) -> Optional[Tuple[TokenType, str]]:
        two = self.peek() + self.peek(1)
        if two in MULTI_CHAR_OPS:
            tok = (TokenType.OPERATOR, two)
            self.advance(2)
            return tok

        ch = self.peek()
        if ch in SINGLE_CHAR_OPS:
            tok = (TokenType.OPERATOR, ch)
            self.advance()
            return tok

        if ch in SEPARATORS:
            tok = (TokenType.SEPARATOR, ch)
            self.advance()
            return tok

        return None

    def next_token(self) -> Tuple[TokenType, str]:
        while not self.eof():
            self.skip_whitespace()

            com = self.skip_comments()
            if com:
                return com

            if self.eof():
                break

           
            for fn in (self.lex_real, self.lex_integer, self.lex_identifier, self.lex_string, self.lex_operator_or_separator):
                here = self.i
                tok = fn()
                if tok is not None:
                    return tok
                else:
                    self.i = here  

           
            ch = self.peek()
            self.advance()
            return (TokenType.UNKNOWN, ch)

        return (TokenType.EOF, "")

def lex_file(in_path: str, out_path: str) -> None:
    with open(in_path, "r", encoding="utf-8") as f:
        text = f.read()

    lx = Lexer(text)
    rows: List[Tuple[str, str]] = []

    while True:
        tok, lex = lx.next_token()
        if tok == TokenType.EOF:
            brea
        if tok == TokenType.COMMENT:
           
            continue
        rows.append((tok.name.lower(), lex))

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(f"{'token':<15} {'lexeme'}\n")
        out.write("-" * 40 + "\n")
        for t, l in rows:
            out.write(f"{t:<15} {l}\n")

if __name__ == "__main__":
    import os
    if len(sys.argv) == 3:
        lex_file(sys.argv[1], sys.argv[2])
    else:
        tests_dir = os.path.join(os.path.dirname(__file__), "tests")
        os.makedirs(tests_dir, exist_ok=True)
        for i in range(1, 4):
            in_f = os.path.join(tests_dir, f"test{i}.rat")
            out_f = os.path.join(tests_dir, f"test{i}.out.txt")
            if os.path.exists(in_f):
                lex_file(in_f, out_f)
                print(f"Wrote {out_f}")
        print("Done demo.")

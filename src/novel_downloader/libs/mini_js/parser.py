#!/usr/bin/env python3
"""
novel_downloader.libs.mini_js.parser
------------------------------------
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .ast import (
    ArrayLiteral,
    Assign,
    BinaryOp,
    CallExpr,
    ConditionalExpr,
    DeleteOp,
    FunctionDecl,
    FunctionExpr,
    Identifier,
    IndexExpr,
    LetDecl,
    Literal,
    LogicalOp,
    MemberExpr,
    ObjectLiteral,
    OptCallExpr,
    OptMemberExpr,
    Program,
    ReturnStmt,
    StringLiteral,
    TypeofOp,
    UnaryOp,
)
from .tokenizer import (
    T_AMP,
    T_ANDAND,
    T_ANDANDEQ,
    T_ANDEQ,
    T_BAR,
    T_CARET,
    T_COLON,
    T_COMMA,
    T_DELETE,
    T_DIV,
    T_DIVEQ,
    T_DOT,
    T_EOF,
    T_EQ,
    T_EQEQ,
    T_FALSE,
    T_FLOAT,
    T_FUNCTION,
    T_GE,
    T_GT,
    T_ID,
    T_IN,
    T_INF,
    T_INTEGER,
    T_LBRACE,
    T_LBRACK,
    T_LE,
    T_LET,
    T_LPAREN,
    T_LT,
    T_MINUS,
    T_MINUSEQ,
    T_MOD,
    T_MODEQ,
    T_NAN,
    T_NEQ,
    T_NOT,
    T_NULL,
    T_NULLISH,
    T_NULLISHEQ,
    T_OREQ,
    T_OROR,
    T_OROREQ,
    T_PLUS,
    T_PLUSEQ,
    T_POW,
    T_POWEQ,
    T_QDOT,
    T_QUESTION,
    T_RBRACE,
    T_RBRACK,
    T_RETURN,
    T_RPAREN,
    T_SAR,
    T_SAREQ,
    T_SEMICOL,
    T_SEQ,
    T_SHL,
    T_SHLEQ,
    T_SHR,
    T_SHREQ,
    T_SNEQ,
    T_STRING,
    T_TILDE,
    T_TIMES,
    T_TIMESEQ,
    T_TRUE,
    T_TYPEOF,
    T_UNDEF,
    T_XOREQ,
    JsTokenizer,
    Token,
)
from .utils import unescape_js_string

# assignment operators mapping (to runtime's op strings)
ASSIGN_OP_MAP: dict[int, str | None] = {
    T_EQ: None,
    T_PLUSEQ: "+=",
    T_MINUSEQ: "-=",
    T_TIMESEQ: "*=",
    T_DIVEQ: "/=",
    T_MODEQ: "%=",
    T_OROREQ: "||=",
    T_ANDANDEQ: "&&=",
    T_NULLISHEQ: "??=",
    T_ANDEQ: "&=",
    T_OREQ: "|=",
    T_XOREQ: "^=",
    T_SHLEQ: "<<=",
    T_SAREQ: ">>=",
    T_SHREQ: ">>>=",
    T_POWEQ: "**=",
}

# binding powers (higher = tighter)
BP_TERNARY = 2
BP_LOGICAL_OR_NULLISH = 3
BP_LOGICAL_AND = 4
BP_BIT_OR = 5
BP_BIT_XOR = 6
BP_BIT_AND = 7
BP_EQUALITY = 8
BP_RELATIONAL = 9
BP_SHIFT = 10
BP_ADD = 11
BP_MUL = 12
BP_POW = 15
BP_PREFIX = 14
BP_POSTFIX = 20

EOF_TOKEN = Token(T_EOF, "")

# small int -> runtime BinaryOp.op (string)
_SYM2: dict[int, str] = {
    T_PLUS: "+",
    T_MINUS: "-",
    T_TIMES: "*",
    T_DIV: "/",
    T_MOD: "%",
}

_KIND2BINOP: dict[int, str] = {
    T_EQEQ: "EQEQ",
    T_NEQ: "NEQ",
    T_SEQ: "SEQ",
    T_SNEQ: "SNEQ",
    T_LT: "LT",
    T_LE: "LE",
    T_GT: "GT",
    T_GE: "GE",
    T_IN: "IN",
    T_SHL: "SHL",
    T_SAR: "SAR",
    T_SHR: "SHR",
}

# infix table: kind -> (lbp, right_assoc, builder)
Builder = Callable[[int, Any, Any], Any]
INFIX_TABLE: dict[int, tuple[int, bool, Builder]] = {
    # logical
    T_OROR: (
        BP_LOGICAL_OR_NULLISH,
        False,
        lambda _t, lhs, rhs: LogicalOp("||", lhs, rhs),
    ),
    T_NULLISH: (
        BP_LOGICAL_OR_NULLISH,
        False,
        lambda _t, lhs, rhs: LogicalOp("??", lhs, rhs),
    ),
    T_ANDAND: (BP_LOGICAL_AND, False, lambda _t, lhs, rhs: LogicalOp("&&", lhs, rhs)),
    # bitwise
    T_BAR: (BP_BIT_OR, False, lambda _t, lhs, rhs: BinaryOp("BIT_OR", lhs, rhs)),
    T_CARET: (BP_BIT_XOR, False, lambda _t, lhs, rhs: BinaryOp("BIT_XOR", lhs, rhs)),
    T_AMP: (BP_BIT_AND, False, lambda _t, lhs, rhs: BinaryOp("BIT_AND", lhs, rhs)),
    # equality / relational / shift
    T_EQEQ: (
        BP_EQUALITY,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_NEQ: (BP_EQUALITY, False, lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs)),
    T_SEQ: (BP_EQUALITY, False, lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs)),
    T_SNEQ: (
        BP_EQUALITY,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_LT: (
        BP_RELATIONAL,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_LE: (
        BP_RELATIONAL,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_GT: (
        BP_RELATIONAL,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_GE: (
        BP_RELATIONAL,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_IN: (
        BP_RELATIONAL,
        False,
        lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs),
    ),
    T_SHL: (BP_SHIFT, False, lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs)),
    T_SAR: (BP_SHIFT, False, lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs)),
    T_SHR: (BP_SHIFT, False, lambda t, lhs, rhs: BinaryOp(_KIND2BINOP[t], lhs, rhs)),
    # add / mul
    T_PLUS: (BP_ADD, False, lambda t, lhs, rhs: BinaryOp(_SYM2[t], lhs, rhs)),
    T_MINUS: (BP_ADD, False, lambda t, lhs, rhs: BinaryOp(_SYM2[t], lhs, rhs)),
    T_TIMES: (BP_MUL, False, lambda t, lhs, rhs: BinaryOp(_SYM2[t], lhs, rhs)),
    T_DIV: (BP_MUL, False, lambda t, lhs, rhs: BinaryOp(_SYM2[t], lhs, rhs)),
    T_MOD: (BP_MUL, False, lambda t, lhs, rhs: BinaryOp(_SYM2[t], lhs, rhs)),
    # ** (right-assoc)
    T_POW: (BP_POW, True, lambda _t, lhs, rhs: BinaryOp("**", lhs, rhs)),
}


class JsParser:
    __slots__ = ("tokens", "pos", "n")

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.n = len(tokens)

    # ---- cursor helpers ----
    def peek(self) -> Token:
        if self.pos < self.n:
            return self.tokens[self.pos]
        return EOF_TOKEN

    def peek_type(self) -> int:
        if self.pos < self.n:
            return self.tokens[self.pos].type
        return T_EOF

    def lookahead(self, n: int = 1) -> Token:
        i = self.pos + n
        if i < self.n:
            return self.tokens[i]
        return EOF_TOKEN

    def consume(self, expected_type: int | None = None) -> Token:
        tok = self.peek()
        if expected_type is not None and tok.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {tok.type}")
        self.pos += 1
        return tok

    # ---- program / statements ----
    def parse_program(self) -> Program:
        stmts: list[Any] = []
        pt = self.peek_type
        c = self.consume
        while pt() != T_EOF:
            stmts.append(self.parse_stmt())
            if pt() == T_SEMICOL:
                c(T_SEMICOL)
        return Program(stmts)

    def parse_stmt(self) -> Any:
        t = self.peek_type()
        if t == T_LET:
            return self._parse_let()
        if t == T_RETURN:
            return self._parse_return()
        if t == T_FUNCTION and self.lookahead().type == T_ID:
            return self._parse_function_decl()
        return self.parse_assignment()

    def _parse_let(self) -> LetDecl:
        self.consume(T_LET)
        name = self.consume(T_ID).value
        self.consume(T_EQ)
        expr = self.parse_assignment()
        return LetDecl(name, expr)

    def _parse_return(self) -> ReturnStmt:
        self.consume(T_RETURN)
        expr = self.parse_assignment()
        return ReturnStmt(expr)

    def _parse_function_decl(self) -> FunctionDecl:
        self.consume(T_FUNCTION)
        name = self.consume(T_ID).value
        params, body = self._parse_function_rest()
        return FunctionDecl(name, params, body)

    # ---- expression (Pratt) with assignment handled on top ----
    def parse_assignment(self) -> Any:
        left = self._parse_expr_bp(0)

        t = self.peek_type()
        if t in ASSIGN_OP_MAP:
            op_tok = self.consume().type
            if not isinstance(left, Identifier | MemberExpr | IndexExpr):
                raise SyntaxError("Invalid left-hand side in assignment")
            value = self.parse_assignment()  # right-assoc
            return Assign(left, value, ASSIGN_OP_MAP[op_tok])
        return left

    def _parse_expr_bp(self, min_bp: int) -> Any:
        left = self._nud()
        left = self._parse_postfix_chain(left)

        pt = self.peek_type
        c = self.consume

        while True:
            t = pt()

            # ternary ?:
            if t == T_QUESTION:
                if min_bp > BP_TERNARY:
                    break
                c(T_QUESTION)
                mid = self.parse_assignment()
                c(T_COLON)
                right = self.parse_assignment()
                left = ConditionalExpr(left, mid, right)
                left = self._parse_postfix_chain(left)
                continue

            spec = INFIX_TABLE.get(t)
            if spec is None:
                break
            lbp, right_assoc, builder = spec
            if lbp < min_bp:
                break

            op_type = c().type
            rbp = lbp if right_assoc else lbp + 1
            right = self._parse_expr_bp(rbp)
            left = builder(op_type, left, right)
            left = self._parse_postfix_chain(left)

        return left

    # ---- nud / prefix / primary ----
    def _nud(self) -> Any:
        t = self.peek_type()
        c = self.consume

        if t in (T_PLUS, T_MINUS, T_NOT, T_TILDE, T_TYPEOF, T_DELETE):
            op_type = c().type
            operand = self._parse_expr_bp(BP_PREFIX)
            if op_type == T_TYPEOF:
                return TypeofOp(operand)
            if op_type == T_DELETE:
                return DeleteOp(operand)
            return UnaryOp(
                {T_PLUS: "+", T_MINUS: "-", T_NOT: "!", T_TILDE: "~"}[op_type], operand
            )

        if t == T_FLOAT:
            return Literal(float(c().value))
        if t == T_INTEGER:
            return Literal(int(c().value))
        if t == T_STRING:
            return StringLiteral(unescape_js_string(c().value))
        if t in (T_TRUE, T_FALSE, T_NULL, T_UNDEF, T_NAN, T_INF):
            tok = c()
            mapping: dict[int, Any] = {
                T_TRUE: True,
                T_FALSE: False,
                T_NULL: None,
                T_UNDEF: None,
                T_NAN: float("nan"),
                T_INF: float("inf"),
            }
            return Literal(mapping[tok.type])
        if t == T_ID:
            return Identifier(c().value)
        if t == T_LPAREN:
            c(T_LPAREN)
            expr = self.parse_assignment()
            c(T_RPAREN)
            return expr
        if t == T_LBRACE:
            return self._parse_object()
        if t == T_LBRACK:
            return self._parse_array()
        if t == T_FUNCTION:
            return self._parse_function_expr()

        raise SyntaxError(f"Unexpected token {self.peek()} in expression")

    # ---- postfix chain: call/member/index/optional ----
    def _parse_postfix_chain(self, node: Any) -> Any:
        pt = self.peek_type
        c = self.consume
        while True:
            t = pt()
            if t == T_QDOT:
                c(T_QDOT)
                if pt() == T_LPAREN:
                    args = self._parse_args()
                    node = OptCallExpr(node, args)
                else:
                    prop = c(T_ID).value
                    node = OptMemberExpr(node, prop)
                continue
            if t == T_LPAREN:
                args = self._parse_args()
                node = CallExpr(node, args)
                continue
            if t == T_DOT:
                c(T_DOT)
                prop = c(T_ID).value
                node = MemberExpr(node, prop)
                continue
            if t == T_LBRACK:
                c(T_LBRACK)
                idx = self.parse_assignment()
                c(T_RBRACK)
                node = IndexExpr(node, idx)
                continue
            break
        return node

    # ---- object / array / function ----
    def _parse_object(self) -> ObjectLiteral:
        c = self.consume
        pt = self.peek_type
        c(T_LBRACE)
        props: dict[str, Any] = {}
        while pt() != T_RBRACE:
            key = unescape_js_string(c().value) if pt() == T_STRING else c(T_ID).value
            c(T_COLON)
            props[key] = self.parse_assignment()
            if pt() == T_COMMA:
                c(T_COMMA)
        c(T_RBRACE)
        return ObjectLiteral(props)

    def _parse_array(self) -> ArrayLiteral:
        c = self.consume
        pt = self.peek_type
        c(T_LBRACK)
        elems: list[Any] = []
        while pt() != T_RBRACK:
            elems.append(self.parse_assignment())
            if pt() == T_COMMA:
                c(T_COMMA)
        c(T_RBRACK)
        return ArrayLiteral(elems)

    def _parse_function_rest(self) -> tuple[list[str], list[Any]]:
        c = self.consume
        pt = self.peek_type
        c(T_LPAREN)
        params: list[str] = []
        while pt() != T_RPAREN:
            params.append(c(T_ID).value)
            if pt() == T_COMMA:
                c(T_COMMA)
        c(T_RPAREN)
        c(T_LBRACE)
        body: list[Any] = []
        while self.peek_type() != T_RBRACE:
            body.append(self.parse_stmt())
            if self.peek_type() == T_SEMICOL:
                c(T_SEMICOL)
        c(T_RBRACE)
        return params, body

    def _parse_function_expr(self) -> FunctionExpr:
        self.consume(T_FUNCTION)
        params, body = self._parse_function_rest()
        return FunctionExpr(params, body)

    def _parse_args(self) -> list[Any]:
        c = self.consume
        pt = self.peek_type
        c(T_LPAREN)
        args: list[Any] = []
        while pt() != T_RPAREN:
            args.append(self.parse_assignment())
            if pt() == T_COMMA:
                c(T_COMMA)
        c(T_RPAREN)
        return args


def parse_code(code: str) -> Program:
    tokens = list(JsTokenizer().tokenize(code))
    return JsParser(tokens).parse_program()

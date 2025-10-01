#!/usr/bin/env python3
"""
novel_downloader.libs.mini_js.runtime
-------------------------------------
"""

from __future__ import annotations

import operator as _op
from dataclasses import dataclass
from typing import Any, cast
from typing import Literal as TLiteral

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
from .parser import parse_code
from .utils import js_nullish, js_truthy, to_int32, to_uint32, typeof_value

# ------------------------------
# Node type aliases
# ------------------------------

type ExpressionNode = (
    Literal
    | StringLiteral
    | Identifier
    | UnaryOp
    | BinaryOp
    | LogicalOp
    | ConditionalExpr
    | ObjectLiteral
    | ArrayLiteral
    | FunctionExpr
    | CallExpr
    | MemberExpr
    | OptMemberExpr
    | IndexExpr
    | OptCallExpr
    | Assign
    | TypeofOp
    | DeleteOp
)

type StatementNode = LetDecl | FunctionDecl | ReturnStmt | ExpressionNode

# assignment reference forms
type IdRef = tuple[TLiteral["id"], str]
type MemberRef = tuple[TLiteral["member"], tuple[dict[Any, Any], Any]]
type IndexListRef = tuple[TLiteral["index_list"], tuple[list[Any], int]]
type IndexDictRef = tuple[TLiteral["index_dict"], tuple[dict[Any, Any], Any]]
type Ref = IdRef | MemberRef | IndexListRef | IndexDictRef

# operator maps
_ARITH: dict[str, Any] = {
    "+": _op.add,
    "-": _op.sub,
    "*": _op.mul,
    "/": _op.truediv,
    "%": _op.mod,
    "**": _op.pow,
}
_REL: dict[str, Any] = {"LT": _op.lt, "LE": _op.le, "GT": _op.gt, "GE": _op.ge}
_EQNE: dict[str, Any] = {"EQEQ": _op.eq, "NEQ": _op.ne, "SEQ": _op.eq, "SNEQ": _op.ne}


# ------------------------------
# Environment & function
# ------------------------------


class Env:
    def __init__(
        self, data: dict[str, Any] | None = None, parent: Env | None = None
    ) -> None:
        self.data: dict[str, Any] = {} if data is None else dict(data)
        self.parent: Env | None = parent

    def define(self, name: str, value: Any) -> None:
        self.data[name] = value

    def set(self, name: str, value: Any) -> None:
        env = self._find(name)
        if env is None:
            raise NameError(f"{name} is not defined")
        env.data[name] = value

    def get(self, name: str) -> Any:
        env = self._find(name)
        if env is None:
            raise NameError(f"{name} is not defined")
        return env.data[name]

    def _find(self, name: str) -> Env | None:
        cur: Env | None = self
        while cur:
            if name in cur.data:
                return cur
            cur = cur.parent
        return None


class _ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


@dataclass
class JsFunction:
    params: list[str]
    body: list[StatementNode]
    closure: Env

    def __call__(self, args: list[Any]) -> Any:
        call_env = Env(parent=self.closure)
        if len(args) != len(self.params):
            raise TypeError(f"Expected {len(self.params)} arguments, got {len(args)}")
        for name, val in zip(self.params, args, strict=False):
            call_env.define(name, val)
        try:
            for stmt in self.body:
                MiniJS._eval_stmt_in_env_static(stmt, call_env)
            return None
        except _ReturnSignal as r:
            return r.value


# ------------------------------
# Runtime
# ------------------------------


class MiniJS:
    def __init__(self) -> None:
        self._env: Env = Env()

    def env(self) -> dict[str, Any]:
        return dict(self._env.data)

    def clean_env(self) -> None:
        self._env = Env()

    def eval(self, code: str) -> Any:
        ast: Program = parse_code(code)
        last_expr_val: Any = None
        for stmt in cast(list[StatementNode], ast.body):
            val, is_expr = MiniJS._eval_stmt_in_env_static(stmt, self._env)
            if is_expr:
                last_expr_val = val
        return last_expr_val

    @staticmethod
    def _eval_stmt_in_env_static(
        node: StatementNode, env: Env
    ) -> tuple[Any | None, bool]:
        match node:
            case LetDecl(name=name, expr=expr):
                val = MiniJS._eval_expr_in_env_static(expr, env)
                env.define(name, val)
                return None, False

            case FunctionDecl(name=name, params=params, body=body):
                func = JsFunction(params=params, body=body, closure=env)
                env.define(name, func)
                return None, False

            case ReturnStmt(expr=expr):
                value = MiniJS._eval_expr_in_env_static(expr, env)
                raise _ReturnSignal(value)

            case _:
                return (
                    MiniJS._eval_expr_in_env_static(cast(ExpressionNode, node), env),
                    True,
                )

    @staticmethod
    def _eval_expr_in_env_static(node: ExpressionNode, env: Env) -> Any:
        match node:
            # literals & id
            case Literal(value=v):
                return v
            case StringLiteral(value=s):
                return s
            case Identifier(name=n):
                return env.get(n)

            # typeof
            case TypeofOp(expr=expr):
                try:
                    v = MiniJS._eval_expr_in_env_static(expr, env)
                except NameError:
                    return "undefined"
                if isinstance(v, JsFunction):
                    return "function"
                return typeof_value(v)

            # delete
            case DeleteOp(target=t):
                match t:
                    case Identifier():
                        raise SyntaxError("Cannot delete variable")
                    case MemberExpr(obj=obj_e, prop=prop):
                        obj = MiniJS._eval_expr_in_env_static(obj_e, env)
                        if not isinstance(obj, dict):
                            raise TypeError("Member delete on non-object")
                        return obj.pop(prop, None) is not None
                    case IndexExpr(obj=obj_e, index=idx_e):
                        obj = MiniJS._eval_expr_in_env_static(obj_e, env)
                        idx = MiniJS._eval_expr_in_env_static(idx_e, env)
                        if isinstance(obj, dict):
                            return obj.pop(idx, None) is not None
                        if isinstance(obj, list):
                            if isinstance(idx, int) and 0 <= idx < len(obj):
                                obj[idx] = None
                                return True
                            return True
                        raise TypeError("Index delete on unsupported type")
                    case _:
                        raise SyntaxError("Invalid delete target")

            # unary
            case UnaryOp(op=op, operand=operand):
                val = MiniJS._eval_expr_in_env_static(operand, env)
                if op in ("!", "not"):
                    return not js_truthy(val)
                if op == "+":
                    return +val
                if op == "-":
                    return -val
                if op == "~":
                    return to_int32(~to_int32(val))
                raise RuntimeError(f"Unsupported unary operator: {op}")

            # logical
            case LogicalOp(op=lop, left=left, right=right):
                lv = MiniJS._eval_expr_in_env_static(left, env)
                if lop == "&&":
                    return (
                        lv
                        if not js_truthy(lv)
                        else MiniJS._eval_expr_in_env_static(right, env)
                    )
                if lop == "||":
                    return (
                        lv
                        if js_truthy(lv)
                        else MiniJS._eval_expr_in_env_static(right, env)
                    )
                if lop == "??":
                    return (
                        lv
                        if not js_nullish(lv)
                        else MiniJS._eval_expr_in_env_static(right, env)
                    )
                raise RuntimeError(f"Unsupported logical operator: {lop}")

            # conditional
            case ConditionalExpr(test=test, consequent=consequent, alternate=alternate):
                t = MiniJS._eval_expr_in_env_static(test, env)
                branch = consequent if js_truthy(t) else alternate
                return MiniJS._eval_expr_in_env_static(branch, env)

            # binary
            case BinaryOp(op=op, left=left, right=right):
                lv = MiniJS._eval_expr_in_env_static(left, env)
                rv = MiniJS._eval_expr_in_env_static(right, env)

                fn = _ARITH.get(op)
                if fn is not None:
                    return fn(lv, rv)

                if op == "BIT_AND":
                    return to_int32(to_int32(lv) & to_int32(rv))
                if op == "BIT_OR":
                    return to_int32(to_int32(lv) | to_int32(rv))
                if op == "BIT_XOR":
                    return to_int32(to_int32(lv) ^ to_int32(rv))
                if op == "SHL":
                    return to_int32(to_int32(lv) << (int(rv) & 31))
                if op == "SAR":
                    return to_int32(to_int32(lv) >> (int(rv) & 31))
                if op == "SHR":
                    return to_uint32(lv) >> (int(rv) & 31)

                fn = _EQNE.get(op)
                if fn is not None:
                    return fn(lv, rv)
                fn = _REL.get(op)
                if fn is not None:
                    return fn(lv, rv)

                if op == "IN":
                    if isinstance(rv, dict):
                        return lv in rv
                    if isinstance(rv, list):
                        try:
                            idx = int(lv)
                            return 0 <= idx < len(rv)
                        except Exception:
                            return False
                    raise TypeError("'in' right-hand side should be object or array")

                raise RuntimeError(f"Unsupported binary operator: {op}")

            # object / array / function expr
            case ObjectLiteral(props=props):
                return {
                    k: MiniJS._eval_expr_in_env_static(v, env) for k, v in props.items()
                }
            case ArrayLiteral(elements=els):
                return [MiniJS._eval_expr_in_env_static(e, env) for e in els]
            case FunctionExpr(params=params, body=body):
                return JsFunction(params=params, body=body, closure=env)

            # calls
            case CallExpr(func=fn_expr, args=args):
                fn_val = MiniJS._eval_expr_in_env_static(fn_expr, env)
                if fn_val is None:
                    return None
                argv = [MiniJS._eval_expr_in_env_static(a, env) for a in args]
                if not callable(fn_val):
                    raise TypeError("Attempted to call a non-function value")
                return fn_val(argv)
            case OptCallExpr(func=fn_expr, args=args):
                fn_val = MiniJS._eval_expr_in_env_static(fn_expr, env)
                if js_nullish(fn_val):
                    return None
                argv = [MiniJS._eval_expr_in_env_static(a, env) for a in args]
                if not callable(fn_val):
                    raise TypeError("Attempted to call a non-function value")
                return fn_val(argv)

            # member / index
            case MemberExpr(obj=obj_expr, prop=prop):
                obj = MiniJS._eval_expr_in_env_static(obj_expr, env)
                if not isinstance(obj, dict):
                    raise TypeError("Member access on non-object")
                return obj.get(prop, None)
            case OptMemberExpr(obj=obj_expr, prop=prop):
                obj = MiniJS._eval_expr_in_env_static(obj_expr, env)
                if js_nullish(obj):
                    return None
                if not isinstance(obj, dict):
                    raise TypeError("Member access on non-object")
                return obj.get(prop, None)
            case IndexExpr(obj=obj_expr, index=idx_expr):
                obj = MiniJS._eval_expr_in_env_static(obj_expr, env)
                idx = MiniJS._eval_expr_in_env_static(idx_expr, env)
                if isinstance(obj, list):
                    return obj[idx]
                if isinstance(obj, dict):
                    return obj.get(idx, None)
                raise TypeError("Indexing on unsupported type")

            # assignment
            case Assign(target=target, value=value, op=op):

                def get_ref_and_current(t: ExpressionNode) -> tuple[Ref, Any]:
                    match t:
                        case Identifier(name=name):
                            return ("id", name), env.get(name)
                        case MemberExpr(obj=obj_e, prop=prop):
                            obj = MiniJS._eval_expr_in_env_static(obj_e, env)
                            if not isinstance(obj, dict):
                                raise TypeError("Member assignment on non-object")
                            return ("member", (obj, prop)), obj.get(prop, None)
                        case IndexExpr(obj=obj_e, index=idx_e):
                            obj = MiniJS._eval_expr_in_env_static(obj_e, env)
                            idx_v = MiniJS._eval_expr_in_env_static(idx_e, env)
                            if isinstance(obj, list):
                                idx_i = int(idx_v)
                                return ("index_list", (obj, idx_i)), obj[idx_i]
                            if isinstance(obj, dict):
                                return ("index_dict", (obj, idx_v)), obj.get(
                                    idx_v, None
                                )
                            raise TypeError("Index assignment on unsupported type")
                        case _:
                            raise RuntimeError("Invalid assignment target")

                def store(ref: Ref, v: Any) -> None:
                    tag = ref[0]
                    if tag == "id":
                        id_ref = cast(IdRef, ref)
                        env.set(id_ref[1], v)
                    elif tag == "member":
                        mref = cast(MemberRef, ref)
                        obj, prop = mref[1]
                        obj[prop] = v
                    elif tag == "index_list":
                        lref = cast(IndexListRef, ref)
                        arr, i = lref[1]
                        arr[i] = v
                    elif tag == "index_dict":
                        dref = cast(IndexDictRef, ref)
                        dct, key = dref[1]
                        dct[key] = v
                    else:
                        raise RuntimeError("Invalid store target")

                if op is None:
                    val = MiniJS._eval_expr_in_env_static(value, env)
                    ref, _cur = get_ref_and_current(target)
                    store(ref, val)
                    return val

                ref, cur = get_ref_and_current(target)
                rhs = MiniJS._eval_expr_in_env_static(value, env)

                if op == "+=":
                    new_val = cur + rhs
                elif op == "-=":
                    new_val = cur - rhs
                elif op == "*=":
                    new_val = cur * rhs
                elif op == "/=":
                    new_val = cur / rhs
                elif op == "%=":
                    new_val = cur % rhs
                elif op == "&=":
                    new_val = to_int32(to_int32(cur) & to_int32(rhs))
                elif op == "|=":
                    new_val = to_int32(to_int32(cur) | to_int32(rhs))
                elif op == "^=":
                    new_val = to_int32(to_int32(cur) ^ to_int32(rhs))
                elif op == "<<=":
                    new_val = to_int32(to_int32(cur) << (int(rhs) & 31))
                elif op == ">>=":
                    new_val = to_int32(to_int32(cur) >> (int(rhs) & 31))
                elif op == ">>>=":
                    new_val = to_uint32(cur) >> (int(rhs) & 31)
                elif op == "**=":
                    new_val = cur**rhs
                elif op == "||=":
                    if js_truthy(cur):
                        return cur
                    new_val = rhs
                elif op == "&&=":
                    if not js_truthy(cur):
                        return cur
                    new_val = rhs
                elif op == "??=":
                    if not js_nullish(cur):
                        return cur
                    new_val = rhs
                else:
                    raise RuntimeError(f"Unsupported compound assignment {op}")

                store(ref, new_val)
                return new_val

            case _:
                raise RuntimeError(
                    f"Unsupported expression node: {type(node).__name__}"
                )

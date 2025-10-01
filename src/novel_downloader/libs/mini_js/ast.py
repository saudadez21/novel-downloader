#!/usr/bin/env python3
"""
novel_downloader.libs.mini_js.ast
---------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# --------- Program / Stmt ----------
@dataclass
class Program:
    body: list[Any]


@dataclass
class LetDecl:
    name: str
    expr: Any


@dataclass
class FunctionDecl:
    name: str
    params: list[str]
    body: list[Any]


@dataclass
class ReturnStmt:
    expr: Any


# --------- Expr ----------
@dataclass
class Identifier:
    name: str


@dataclass
class Literal:
    value: Any


@dataclass
class StringLiteral:
    value: str


@dataclass
class UnaryOp:
    op: str
    operand: Any


@dataclass
class BinaryOp:
    op: str
    left: Any
    right: Any


@dataclass
class LogicalOp:
    op: str
    left: Any
    right: Any


@dataclass
class ConditionalExpr:
    test: Any
    consequent: Any
    alternate: Any


@dataclass
class ObjectLiteral:
    props: dict[str, Any]


@dataclass
class ArrayLiteral:
    elements: list[Any]


@dataclass
class FunctionExpr:
    params: list[str]
    body: list[Any]


@dataclass
class CallExpr:
    func: Any
    args: list[Any]


@dataclass
class MemberExpr:
    obj: Any
    prop: str


@dataclass
class OptMemberExpr:
    obj: Any
    prop: str


@dataclass
class IndexExpr:
    obj: Any
    index: Any


@dataclass
class OptCallExpr:
    func: Any
    args: list[Any]


@dataclass
class Assign:
    target: Any
    value: Any
    op: str | None = None


@dataclass
class TypeofOp:
    expr: Any


@dataclass
class DeleteOp:
    target: Any

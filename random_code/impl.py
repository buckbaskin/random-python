from ast import (
    Assert,
    Assign,
    AugAssign,
    AST,
    AsyncFor,
    AsyncFunctionDef,
    AsyncWith,
    Attribute,
    BinOp,
    BoolOp,
    Break,
    Call,
    ClassDef,
    Compare,
    comprehension,
    Constant,
    Delete,
    Dict,
    DictComp,
    dump,
    ExceptHandler,
    Expr,
    fix_missing_locations,
    For,
    FormattedValue,
    FunctionDef,
    GeneratorExp,
    If,
    IfExp,
    Import,
    ImportFrom,
    Index,
    JoinedStr,
    keyword,
    Lambda,
    List,
    ListComp,
    Module,
    Name,
    NodeTransformer,
    NodeVisitor,
    parse,
    Pass,
    Raise,
    Return,
    Set,
    SetComp,
    Slice,
    Starred,
    Subscript,
    Try,
    Tuple,
    UnaryOp,
    While,
    With,
    withitem,
    Yield,
)

### Feature List
# "alias": {"name": [], "asname": []},
# "AnnAssign": {"target": [], "annotation": [], "value": [], "simple": []},
# "arg": {"arg": [], "annotation": [], "type_comment": []},
# "arguments": {
# "Assert": {"test": [], "msg": []},
# "Assign": {"targets": [], "value": [], "type_comment": []},
# "AsyncFunctionDef": {
# "Attribute": {"value": [], "attr": [], "ctx": []},
# "AugAssign": {"target": [], "op": [], "value": []},
# "Await": {"value": []},
# "BinOp": {"left": [], "right": [], "op": []},
# "BoolOp": {"op": [], "values": []},
# "Call": {"func": [], "args": [], "keywords": []},
# "ClassDef": {
# "Compare": {"left": [], "ops": [], "comparators": []},
# "comprehension": {"target": [], "iter": [], "ifs": [], "is_async": []},
# "Constant": {"value": [], "kind": []},
# "Delete": {"targets": []},
# "Dict": {"keys": [], "values": []},
# "DictComp": {"key": [], "value": [], "generators": []},
# "ExceptHandler": {"type": [], "name": [], "body": []},
# "Expr": {"value": []},
# "For": {
# "FormattedValue": {"value": [], "conversion": [], "format_spec": []},
# "FunctionDef": {
# "GeneratorExp": {"elt": [], "generators": []},
# "Global": {"names": []},
# "If": {"test": [], "body": [], "orelse": []},
# "IfExp": {"test": [], "body": [], "orelse": []},
# "Import": {"names": []},
# "ImportFrom": {"module": [], "names": [], "level": []},
# "Index": {"value": []},
# "JoinedStr": {"values": []},
# "keyword": {"arg": [], "value": []},
# "Lambda": {"args": [], "body": []},
# "List": {"elts": [], "ctx": []},
# "ListComp": {"elt": [], "generators": []},
# "Module": {"body": [], "type_ignores": []},
# "Name": {"id": [], "ctx": []},
# "Nonlocal": {"names": []},
# "Raise": {"exc": [], "cause": []},
# "Return": {"value": []},
# "Set": {"elts": []},
# "SetComp": {"elt": [], "generators": []},
# "Slice": {"lower": [], "upper": [], "step": []},
# "Starred": {"value": [], "ctx": []},
# "Subscript": {"value": [], "slice": [], "ctx": []},
# "Try": {"body": [], "handlers": [], "orelse": [], "finalbody": []},
# "Tuple": {"elts": [], "ctx": []},
# "TypeIgnore": {"lineno": [], "tag": []},
# "UnaryOp": {"op": [], "operand": []},
# "While": {"test": [], "body": [], "orelse": []},
# "With": {"items": [], "body": [], "type_comment": []},
# "withitem": {"context_expr": [], "optional_vars": []},
# "Yield": {"value": []},
# "YieldFrom": {"value": []},
### End Feature List (~60 elements)

try:
    # python3.9 and after
    from ast import unparse
except ImportError:
    # before python3.9's ast.unparse
    from astunparse import unparse


def ast_unparse(ast):
    return unparse(fix_missing_locations(ast))


import code
import logging

from abc import ABC
from collections import defaultdict, ChainMap, deque
from typing import List as tList, Dict as tDict
from random import Random
from functools import partial, wraps

UnbundledElementsType = tDict[str, tDict[str, tList[AST]]]


log = logging.getLogger(__name__)
log.setLevel("WARN")


class NotNameParent(ABC):
    _doesnt_contain_names = {
        "Break",
        "Constant",
        "Import",
        "ImportFrom",
        "NoneType",
        "Pass",
    }

    @classmethod
    def __subclasshook__(cls, C):
        name = C.__name__
        return name in cls._doesnt_contain_names


class UnbundlingVisitor(NodeVisitor):
    def __init__(self, *, max_depth=10000, log_level=None):
        if log_level is not None:
            log.setLevel(log_level)

        self.depth = 0
        self.max_depth = max_depth
        self.missed_parents = set()
        self.missed_children = set()

        # currently setting up as a collection of lists
        # easy to select and random body, type_ignores in the Module case
        # harder if you want to keep bodies and type_ignores paired
        self.visited = {
            "alias": {"name": [], "asname": []},
            "AnnAssign": {"target": [], "annotation": [], "value": [], "simple": []},
            "arg": {"arg": [], "annotation": [], "type_comment": []},
            "arguments": {
                "posonlyargs": [],
                "args": [],
                "vararg": [],
                "kwonlyargs": [],
                "kw_defaults": [],
                "kwarg": [],
                "defaults": [],
            },
            "Assert": {"test": [], "msg": []},
            "Assign": {"targets": [], "value": [], "type_comment": []},
            "AsyncFunctionDef": {
                "name": [],
                "args": [],
                "body": [],
                "decorator_list": [],
                "returns": [],
                "type_comment": [],
            },
            "Attribute": {"value": [], "attr": [], "ctx": []},
            "AugAssign": {"target": [], "op": [], "value": []},
            "Await": {"value": []},
            "BinOp": {"left": [], "right": [], "op": []},
            "BoolOp": {"op": [], "values": []},
            "Call": {"func": [], "args": [], "keywords": []},
            "ClassDef": {
                "name": [],
                "bases": [],
                "keywords": [],
                "body": [],
                "decorator_list": [],
            },
            "Compare": {"left": [], "ops": [], "comparators": []},
            "comprehension": {"target": [], "iter": [], "ifs": [], "is_async": []},
            "Constant": {"value": [], "kind": []},
            "Delete": {"targets": []},
            "Dict": {"keys": [], "values": []},
            "DictComp": {"key": [], "value": [], "generators": []},
            "ExceptHandler": {"type": [], "name": [], "body": []},
            "Expr": {"value": []},
            "For": {
                "target": [],
                "iter": [],
                "body": [],
                "orelse": [],
                "type_comment": [],
            },
            "FormattedValue": {"value": [], "conversion": [], "format_spec": []},
            "FunctionDef": {
                "name": [],
                "args": [],
                "body": [],
                "decorator_list": [],
                "returns": [],
                "type_comment": [],
            },
            "GeneratorExp": {"elt": [], "generators": []},
            "Global": {"names": []},
            "If": {"test": [], "body": [], "orelse": []},
            "IfExp": {"test": [], "body": [], "orelse": []},
            "Import": {"names": []},
            "ImportFrom": {"module": [], "names": [], "level": []},
            "Index": {"value": []},
            "JoinedStr": {"values": []},
            "keyword": {"arg": [], "value": []},
            "Lambda": {"args": [], "body": []},
            "List": {"elts": [], "ctx": []},
            "ListComp": {"elt": [], "generators": []},
            "Module": {"body": [], "type_ignores": []},
            "Name": {"id": [], "ctx": []},
            "Nonlocal": {"names": []},
            "Raise": {"exc": [], "cause": []},
            "Return": {"value": []},
            "Set": {"elts": []},
            "SetComp": {"elt": [], "generators": []},
            "Slice": {"lower": [], "upper": [], "step": []},
            "Starred": {"value": [], "ctx": []},
            "Subscript": {"value": [], "slice": [], "ctx": []},
            "Try": {"body": [], "handlers": [], "orelse": [], "finalbody": []},
            "Tuple": {"elts": [], "ctx": []},
            "TypeIgnore": {"lineno": [], "tag": []},
            "UnaryOp": {"op": [], "operand": []},
            "While": {"test": [], "body": [], "orelse": []},
            "With": {"items": [], "body": [], "type_comment": []},
            "withitem": {"context_expr": [], "optional_vars": []},
            "Yield": {"value": []},
            "YieldFrom": {"value": []},
        }
        self.ignore = [
            "Add",
            "Eq",
            "IsNot",
            "Load",
            "Lt",
            "LtE",
            "Mult",
            "Store",
            "Sub",
        ]
        self.explore = ["Expr"]

        for k in self.visited:
            name = "visit_%s" % (k,)
            setattr(self, name, self._helper_function_factory(k))

        for k in self.ignore:
            name = "visit_%s" % (k,)
            setattr(self, name, self._ignore_function_factory(k))

        for k in self.explore:
            if k in self.visited or k in self.ignore:
                continue
            name = "visit_%s" % (k,)
            setattr(self, name, self._explore_function_factory(k))

    def depth_padding(self):
        return " " * self.depth

    def _helper_function_factory(self, node_name):
        @depth_protection
        def _visit_X(self, node_):
            self._known_visit(node_name, node_)
            self._post_visit(node_)

        _visit_X.name = node_name
        _visit_X.__name__ = node_name
        return partial(_visit_X, self)

    def _ignore_function_factory(self, node_name):
        @depth_protection
        def _visit_X_ignore(self, node_):
            self._post_visit(node_)

        _visit_X_ignore.name = node_name
        _visit_X_ignore.__name__ = node_name
        return partial(_visit_X_ignore, self)

    def _explore_function_factory(self, node_name):
        @depth_protection
        def _visit_X_explore(self, node_):
            self._explore_visit(node_name, node_)
            self.generic_visit(node_)

        _visit_X_explore.name = node_name
        _visit_X_explore.__name__ = node_name
        return partial(_visit_X_explore, self)

    def _post_visit(self, node):
        log.info(self.depth_padding() + " Processed " + type(node).__name__)
        NodeVisitor.generic_visit(self, node)

    def _explore_visit(self, name, node):
        log.warning(self.depth_padding() + "Explore %s %s" % (name, dir(node)))
        for k in sorted(list(dir(node))):
            if not k.startswith("__"):
                log.warning(self.depth_padding(), k, getattr(node, k))
        log.warning(self.depth_padding() + "---")

    def _known_visit(self, name, nodex):
        for k in self.visited[name]:
            self.visited[name][k].append(getattr(nodex, k))

    def unbundled(self):
        return self.visited

    def generic_visit(self, node):
        if len(node._fields) > 0:
            if type(node).__name__ not in self.missed_parents:

                def field_str(node):
                    for f in node._fields:
                        yield '"%s": []' % (f,)

                log.warning(
                    self.depth_padding()
                    + '"%s": {%s},' % (type(node).__name__, ",".join(field_str(node)))
                )
            self.missed_parents.add(type(node).__name__)
        else:
            self.missed_children.add(type(node).__name__)

        self._post_visit(node)


def unbundle_ast(ast: AST):
    v = UnbundlingVisitor()
    v.visit(ast)

    result = v.unbundled()

    try:
        assert len(v.missed_parents) == 0
    except AssertionError:
        log.error("Missed AST types to handle")
        log.error(sorted(list(v.missed_parents)))
        log.error("Optional AST types to handle")
        log.error(sorted(list(v.missed_children)))
        raise

    return result


def merge_unbundled_asts(asts: tList[UnbundledElementsType]):
    unbundled = {}

    for _map in asts:
        for ast_type, elements in unbundle_ast(_map).items():
            if ast_type not in unbundled:
                unbundled[ast_type] = defaultdict(list)
            for k, list_of_vals in elements.items():
                unbundled[ast_type][k].extend(list_of_vals)

    for k in list(unbundled.keys()):
        unbundled[k] = dict(unbundled[k])

    return unbundled


class BagOfConcepts(object):
    def __init__(self, corpus, seed=1):
        self.corpus = corpus

        self.rng = Random(seed)

        for ast_element in self.corpus:
            setattr(self, ast_element, self._strategy_strict_pairs(ast_element))

    def _strategy_strict_pairs(self, node_name):
        min_examples = min([len(v) for k, v in self.corpus[node_name].items()])
        reference = self.corpus[node_name]

        batch = sorted(list(reference.items()))
        identifiers = [k for k, v in batch]
        data_lists = [v for k, v in batch]

        common_data_pairs = list(zip(*data_lists))

        def _visit_strict_pairs():
            self.rng.shuffle(common_data_pairs)
            for data_pair in common_data_pairs:
                kwargs = {k: v for k, v in zip(identifiers, data_pair)}

                import ast

                yield getattr(ast, node_name)(**kwargs)

        _visit_strict_pairs.name = node_name
        _visit_strict_pairs.__name__ = node_name
        return _visit_strict_pairs


def contains_return(element, top_level=None):
    maybe_contained = deque([element])

    MAX_ITERS = 10000
    for i in range(MAX_ITERS):
        if len(maybe_contained) == 0:
            break

        element = maybe_contained.popleft()
        if element is None:
            return False

        if isinstance(element, Return):
            return True

        # From the AST, Statements that might contain Return (itself a statement that can't contain a Return)
        #   FunctionDef(identifier name, arguments args,
        #                stmt* body, expr* decorator_list, expr? returns,
        #                string? type_comment)
        #   | AsyncFunctionDef(identifier name, arguments args,
        #                      stmt* body, expr* decorator_list, expr? returns,
        #                      string? type_comment)
        #   | ClassDef(identifier name,
        #      expr* bases,
        #      keyword* keywords,
        #      stmt* body,
        #      expr* decorator_list)
        #   | For(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)
        #   | AsyncFor(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)
        #   | While(expr test, stmt* body, stmt* orelse)
        #   | If(expr test, stmt* body, stmt* orelse)
        #   | With(withitem* items, stmt* body, string? type_comment)
        #   | AsyncWith(withitem* items, stmt* body, string? type_comment)
        #   | Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)

        if (
            isinstance(element, FunctionDef)
            or isinstance(element, AsyncFunctionDef)
            or isinstance(element, ClassDef)
            or isinstance(element, With)
            or isinstance(element, AsyncWith)
        ):
            maybe_contained.extend(element.body)

        if (
            isinstance(element, For)
            or isinstance(element, AsyncFor)
            or isinstance(element, While)
            or isinstance(element, If)
        ):
            maybe_contained.extend(element.body)
            maybe_contained.extend(element.orelse)

        if isinstance(element, Try):
            maybe_contained.extend(element.body)
            maybe_contained.extend(element.orelse)
            maybe_contained.extend(element.finalbody)

    if i == MAX_ITERS - 1:
        return True

    return False


def args_to_names(arguments):
    args = [
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
    ]
    if arguments.vararg is not None:
        args.append(arguments.vararg)
    if arguments.kwarg is not None:
        args.append(arguments.kwarg)
    return args


def nested_unpack(element, top_level=None):
    assert not isinstance(element, list)

    if isinstance(element, NotNameParent):
        log.debug("Ending NotNameParent with no elements: %s" % (type(element)))
        return []
    elif isinstance(element, Name):
        return [element.id]
    elif (
        isinstance(element, Attribute)
        or isinstance(element, Index)
        or isinstance(element, Starred)
    ):
        return nested_unpack(element.value, top_level)
    elif isinstance(element, JoinedStr):

        def flattened_JoinedStr():
            for expr in element.values:
                for eid in nested_unpack(expr, top_level):
                    yield eid

        return list(flattened_JoinedStr())
    elif isinstance(element, Subscript):
        return nested_unpack(element.value, top_level) + nested_unpack(
            element.slice, top_level
        )
    elif isinstance(element, Call):

        def flattened_Call():
            for fid in nested_unpack(element.func, top_level):
                yield fid
            for arg in element.args:
                for aid in nested_unpack(arg, top_level):
                    yield aid
            for keyword in element.keywords:
                for kid in nested_unpack(keyword, top_level):
                    yield kid

        return list(flattened_Call())
    elif isinstance(element, Lambda):
        arg_names = set(args_to_names(element.args))
        body_names = set(nested_unpack(element.body, top_level))
        return [name for name in body_names - arg_names]
    elif (
        isinstance(element, If)
        or isinstance(element, IfExp)
        or isinstance(element, While)
    ):
        # Note: the body, orelse can be undefined depending on the result of the test, so taking the less strict approach here
        return nested_unpack(element.test, top_level)
    elif isinstance(element, UnaryOp):
        return nested_unpack(element.operand, top_level)
    elif isinstance(element, BinOp):
        return [
            *nested_unpack(element.left, top_level),
            *nested_unpack(element.right, top_level),
        ]
    elif isinstance(element, BoolOp):

        def flattened_BoolOp():
            for v in element.values:
                for vid in nested_unpack(v, top_level):
                    yield vid

        return list(flattened_BoolOp())
    elif isinstance(element, Compare):

        def flattened_Compare():
            for lid in nested_unpack(element.left, top_level):
                yield lid
            for comparator in element.comparators:
                for cid in nested_unpack(comparator, top_level):
                    yield cid

        return list(flattened_Compare())

    elif isinstance(element, Dict):

        def flattened_Dict():
            for k in element.keys:
                for kid in nested_unpack(k, top_level):
                    yield kid
            for v in element.values:
                for vid in nested_unpack(v, top_level):
                    yield vid

        return list(flattened_Dict())
    elif isinstance(element, Set):

        def flattened_Set():
            for k in element.elts:
                for kid in nested_unpack(k, top_level):
                    yield kid

        return list(flattened_Set())
    elif (
        isinstance(element, ListComp)
        or isinstance(element, GeneratorExp)
        or isinstance(element, DictComp)
        or isinstance(element, SetComp)
    ):

        def flattened_ListComp():
            # Note: elt_id, ifs may be defined by the generators
            # for elt_id in nested_unpack(element.elt, top_level):
            #     yield elt_id

            for gen in element.generators:
                for gid in nested_unpack(gen, top_level):
                    yield gid

        return list(flattened_ListComp())
    elif isinstance(element, comprehension):

        def flattened_comprehension():
            # names in ifs may be defined by other parts of the comprehension
            # for if_ in element.ifs:
            #     for ifid in nested_unpack(if_, top_level):
            #         yield ifid
            for iid in nested_unpack(element.iter, top_level):
                yield iid

        return list(flattened_comprehension())
    elif isinstance(element, Yield) or isinstance(element, Return):
        return nested_unpack(element.value, top_level)
    elif isinstance(element, Expr):
        return nested_unpack(element.value, top_level)
    elif isinstance(element, With):

        def flattened_With():
            for withitem in element.items:
                for cid in nested_unpack(withitem.context_expr, top_level):
                    yield cid

            for expr in element.body:
                for eid in nested_unpack(expr, top_level):
                    yield eid

        return list(flattened_With())
    elif isinstance(element, withitem):
        return nested_unpack(element.context_expr, top_level)
    elif isinstance(element, ClassDef):

        def flattened_ClassDef():
            for base in element.bases:
                for eid in nested_unpack(base, top_level):
                    yield eid

            for decorator in element.decorator_list:
                for did in nested_unpack(decorator, top_level):
                    yield did

            if len(element.keywords) > 0:
                log.warning(element)
                log.warning(ast_unparse(element))
                log.warning(element.keywords)
                log.warning(ast_unparse(element.keywords))
                raise NotImplementedError("ClassDef with keywords")

        return list(flattened_ClassDef())
    elif isinstance(element, FunctionDef):

        def flattened_FunctionDef():
            for decorator in element.decorator_list:
                for did in nested_unpack(decorator, top_level):
                    yield did

            all_args = [
                *element.args.posonlyargs,
                *element.args.args,
                *element.args.kwonlyargs,
            ]
            if element.args.vararg is not None:
                all_args.append(element.args.vararg)
            if element.args.kwarg is not None:
                all_args.append(element.args.kwarg)
            for a in all_args:
                for aid in nested_unpack(a.annotation, top_level):
                    yield aid

        return list(flattened_FunctionDef())
    elif isinstance(element, keyword):
        return nested_unpack(element.value, top_level)
    elif isinstance(element, Assign):
        return nested_unpack(element.value, top_level)
    elif isinstance(element, AugAssign):
        return nested_unpack(element.target, top_level) + nested_unpack(
            element.value, top_level
        )
    elif isinstance(element, Try):
        # Note: handlers, orelse, finalbody conditionally executed and ignored

        def flattened_Try():
            for expr in element.body:
                for eid in nested_unpack(expr, top_level):
                    yield eid
            for excepthandler in element.handlers:
                for eid in nested_unpack(excepthandler, top_level):
                    yield eid

        return list(flattened_Try())
    elif isinstance(element, Assert):
        # Note: structurally like if
        return nested_unpack(element.test, top_level)
    elif isinstance(element, For):

        def flattened_For():
            for iid in nested_unpack(element.iter, top_level):
                yield iid
            for stmt in element.body:
                for sid in nested_unpack(stmt):
                    yield sid

        return list(flattened_For())
    elif isinstance(element, List) or isinstance(element, Tuple):

        def flattened_List():
            for elem in element.elts:
                for eid in nested_unpack(elem, top_level):
                    yield eid

        return list(flattened_List())
    elif isinstance(element, Raise):
        if element.cause is not None:
            log.warning(element)
            log.warning(ast_unparse(element))
            log.warning(element.cause)
            log.warning(ast_unparse(element.cause))
            raise NotImplementedError("Raise with a cause")
        return nested_unpack(element.exc)
    elif isinstance(element, Delete):

        def flattened_Delete():
            for elem in element.targets:
                for eid in nested_unpack(elem, top_level):
                    yield eid

        return list(flattened_Delete())
    elif isinstance(element, FormattedValue):
        return nested_unpack(element.value)
    elif isinstance(element, ExceptHandler):

        def flattened_ExceptHandler():
            for tid in nested_unpack(element.type, top_level):
                yield tid
            for expr in element.body:
                for eid in nested_unpack(expr, top_level):
                    yield eid

        return list(flattened_ExceptHandler())
    elif isinstance(element, Module):

        def flattened_Module():
            for expr in element.body:
                for eid in nested_unpack(expr, top_level):
                    yield eid

        return list(flattened_Module())
    elif isinstance(element, Slice):

        def flattened_Slice():
            if element.lower is not None:
                for lid in nested_unpack(element.lower, top_level):
                    yield lid
            if element.upper is not None:
                for uid in nested_unpack(element.upper, top_level):
                    yield uid
            if element.step is not None:
                for sid in nested_unpack(element.step, top_level):
                    yield sid

        return list(flattened_Slice())

    else:
        log.warning("args unpacking?")
        if top_level is not None:
            log.warning("Top Level")
            log.warning(top_level)
            log.warning(ast_unparse(top_level))
            log.warning("Element")
        log.warning(element)
        try:
            log.warning(ast_unparse(element))
            log.warning(element._fields)
        except AttributeError:
            pass
        raise NotImplementedError("nested_unpack: Element %s" % (type(element),))


def littering(name, to_name):
    """
    Wraps a member function to assign a specified member `name` to `to_name` on the output of the function call.

    For example, used to append the scope to each member of the AST to enable asserting on scope properties in testing
    """

    def wrapper(func):
        @wraps(func)
        def wrapped(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            log.info("littering %s.%s with %s", result, to_name, name)
            setattr(result, to_name, getattr(self, name))
            return result

        return wrapped

    return wrapper


def depth_protection(
    func,
):  # increment depth, check max depth, decrement depth on function exit
    @wraps(func)
    def wrapped(self, node):
        self.depth += 1
        if self.depth >= self.max_depth:
            log.warning(
                "depth_protection: %s max_depth %d exceeded with depth %d",
                str(self),
                self.max_depth,
                self.depth,
            )
            result = node
        else:
            result = func(self, node)
        self.depth -= 1
        return result

    return wrapped


class RecursionCheckerVisitor(NodeVisitor):
    def __init__(self, max_depth=10000):
        self.visited = set()
        self.depth = 0
        self.max_depth = max_depth

    def generic_visit(self, node):
        self.depth += 1

        node_type = type(node)
        node_id = id(node)
        log.debug("%s|-- Visiting %s %s", " " * self.depth, node_type, node_id)

        if (node_type, node_id) in self.visited:
            log.debug("%s|-- Loop Visiting %s %s", " " * self.depth, node_type, node_id)
            raise RecursionError(
                "RecursionCheckerVisitor: Visited the same node twice in a tree"
            )

        if self.depth > self.max_depth:
            log.debug(
                "%s|-- Loop Depth Reached %d %s %s",
                " " * self.depth,
                self.depth,
                node_type,
                node_id,
            )
            return

        self.visited.add((node_type, node_id))

        NodeVisitor.generic_visit(self, node)

        self.depth -= 1


def loop_detection(ast):
    checker = RecursionCheckerVisitor()
    try:
        checker.visit(ast)
    except RecursionError as re:
        log.debug("loop_detection: %s", re)
        return True
    return False


class RandomizingTransformer(NodeTransformer):
    def __init__(self, corpus, *, log_level=None, visit_only=False):
        if log_level is not None:
            log.setLevel(log_level)

        self.corpus = corpus

        self.visit_only = visit_only

        self.depth = 0
        self.max_depth = 10
        self.missed_parents = set()
        self.missed_children = set()

        # This is where the craziness begins
        self.scope = ChainMap(
            {
                "__random_code_return_ok": False,
            }
        )
        for k in __builtins__:
            self.scope[k] = "builtin"
        self.scope = self.scope.new_child()

        self.out_of_scope = set()

        self.visited = set(corpus.corpus.keys())
        self.ignore = ["Module"]

        for k in self.visited:
            name = "visit_%s" % (k,)
            if not hasattr(self, name):
                setattr(self, name, self._helper_function_factory(k))
            else:
                log.debug(self.depth_padding() + "Not clobbering %s", k)

        for k in self.ignore:
            name = "visit_%s" % (k,)
            setattr(self, name, self._ignore_function_factory(k))

    def depth_padding(self):
        return " " * self.depth

    def valid_swap(self, node_, proposed_swap):
        log.debug("valid_swap: %s for %s", str(node_), str(proposed_swap))
        assert type(node_) == type(proposed_swap)

        if loop_detection(proposed_swap):
            return False

        node_type = type(node_).__name__
        new_definitions = ["Module", "arguments"]
        if node_type in new_definitions:
            return True

        i_know_its_wrong = ["alias", "ImportFrom"]
        if node_type in i_know_its_wrong:
            return True

        if (
            "__random_code_return_ok" not in self.scope
            or not self.scope["__random_code_return_ok"]
        ):
            if contains_return(proposed_swap, proposed_swap):
                log.debug("invalid swap: return not ok but contains return")
                return False

        if node_type == "arg":
            if node_.arg == "self" or proposed_swap.arg == "self":
                # Heuristic because self has special usage
                return False

            if node_.annotation is None or node_.annotation.id == "Any":
                return True

            # Note: Right now this is strictly equal type swapping vs allowing subtypes
            return proposed_swap.annotation.id == node_.annotation.id

        if node_type == "Name":
            if proposed_swap.id not in self.scope:
                self.out_of_scope.add(proposed_swap.id)
                log.debug(
                    self.depth_padding()
                    + "Bad Swap: proposed_swap out of scope %s" % (proposed_swap.id,)
                )
                return False

            type_to_match = "Any"
            if node_.id in self.scope:
                type_to_match = self.scope[node_.id]

            condition = proposed_swap.id in self.scope and (
                type_to_match == "Any" or self.scope[proposed_swap.id] == type_to_match
            )
            if condition:
                log.debug(
                    self.depth_padding()
                    + "Good Swap %s and (%s or %s) scope: %s"
                    % (
                        proposed_swap.id in self.scope,
                        type_to_match == "Any",
                        self.scope[proposed_swap.id] == type_to_match,
                        self.scope.maps[:-1],
                    )
                )
            else:
                log.debug(
                    self.depth_padding()
                    + "Bad Swap %s and (%s or %s)"
                    % (
                        proposed_swap.id in self.scope,
                        type_to_match == "Any",
                        self.scope[proposed_swap.id] == type_to_match,
                    )
                )
            return condition

        if node_type == "Call":
            names_to_check = []

            names_to_check.extend(nested_unpack(proposed_swap.func, proposed_swap))
            if len(proposed_swap.args) > 0:
                for a in proposed_swap.args:
                    names_to_check.extend(nested_unpack(a, proposed_swap))
            if len(proposed_swap.keywords) > 0:
                for k in proposed_swap.keywords:
                    arg_value = k.value
                    names_to_check.extend(nested_unpack(arg_value, proposed_swap))

            try:
                pass
                # assert len(names_to_check) > 0
                # Counter Example: 'a b c'.split()
            except AssertionError:
                log.error(self.depth_padding() + "Failed to find names to check")
                log.error(self.depth_padding() + proposed_swap)
                log.error(self.depth_padding() + ast_unparse(proposed_swap))
                code.interact(
                    local=dict(ChainMap({"ast_unparse": ast_unparse}, locals()))
                )
                raise

            for name in names_to_check:
                if name not in self.scope:
                    self.out_of_scope.add(name)
                    return False

            return True

        names_to_check = nested_unpack(proposed_swap, proposed_swap)
        for name in names_to_check:
            if name not in self.scope:
                self.out_of_scope.add(name)
                log.debug(
                    "%s%s swap failed to %s not in scope",
                    self.depth_padding(),
                    node_type,
                    name,
                )
                return False
        return True

    def _helper_function_factory(self, node_name):
        @littering("scope", "_ending_scope")
        @depth_protection
        def _visit_X(self, node_):
            log.info("Visit_X-ing into %s %s", node_name, ast_unparse(node_))
            assert node_name not in [
                "FunctionDef",
                "With",
                "Assign",
                "ListComp",
                "DictComp",
                "SetComp",
                "GeneratorExp",
                "ClassDef",
                "arg",
            ]

            for swapout in getattr(self.corpus, node_name)():
                if self.visit_only:
                    continue
                if self.valid_swap(node_, swapout):
                    # Let python scoping drop this variable
                    break
            else:
                # no valid swapout found
                log.warning("%s Ending due to no valid swap found", node_name)
                swapout = node_

            if node_name == "arguments":
                log.debug(
                    self.depth_padding()
                    + "Swapped arguments in Scope %s for %s"
                    % (
                        [a.arg for a in args_to_names(node_)],
                        [a.arg for a in args_to_names(swapout)],
                    )
                )

                for arg in args_to_names(swapout):
                    type_ = "Any"
                    if arg.annotation is not None:
                        type_ = arg.annotation.id
                    elif arg.type_comment is not None:
                        type_ = arg.type_comment.id
                        raise NotImplementedError("arg evaluation with a type comment")
                    self.scope[arg.arg] = type_
                    log.debug("scope gains value %s from arg - arguments" % (arg.arg,))
                    if arg.annotation is not None or arg.type_comment is not None:
                        log.debug(self.depth_padding() + "arguments - Typed Scope")
                        log.debug(self.depth_padding() + str(self.scope.maps[:-1]))
                log.warning("_visit_X for arguments")

            result = self._post_visit(swapout)

            ## Start If Inspection
            if node_name == "If":
                log.debug("\n===\nIf return evaluation")
                log.debug(
                    "Start contains return %s, in scope %s, return ok %s",
                    contains_return(node_, node_),
                    "__random_code_return_ok" in self.scope,
                    self.scope["__random_code_return_ok"],
                )
                log.debug(ast_unparse(node_))
                log.debug(
                    "Swap contains return %s",
                    contains_return(swapout, swapout),
                )
                log.debug(ast_unparse(swapout))
            if (
                "__random_code_return_ok" not in self.scope
                or not self.scope["__random_code_return_ok"]
            ):
                if contains_return(swapout, swapout):
                    if node_name == "If":
                        log.debug("Skipping Due to Contains Return")
            ## End If Inspection

            log.debug(
                self.depth_padding() + "Swapped " + str(node_) + " for " + str(result)
            )
            log.debug(self.depth_padding() + "====")
            try:
                log.debug(self.depth_padding() + ast_unparse(node_))
            except RecursionError:
                log.debug(self.depth_padding() + str(node_))
            log.debug(self.depth_padding() + ">>>>")
            try:
                log.debug(self.depth_padding() + ast_unparse(swapout))
            except RecursionError:
                log.debug(self.depth_padding() + str(swapout))
            log.debug(self.depth_padding() + "====")

            log.info("Visiting out  %s", node_name)
            return result

        _visit_X.name = node_name
        _visit_X.__name__ = node_name
        return partial(_visit_X, self)

    def _ignore_function_factory(self, node_name):
        @depth_protection
        def _visit_X_ignore(self, node_):
            result = self._post_visit(node_)
            return result

        _visit_X_ignore.name = node_name
        _visit_X_ignore.__name__ = node_name
        return partial(_visit_X_ignore, self)

    def _post_visit(self, node):
        log.debug(
            self.depth_padding() + type(node).__name__ + " " + str(self.scope.maps[:-1])
        )

        result = NodeTransformer.generic_visit(self, node)
        assert result is not None
        return result

    @littering("scope", "_ending_scope")
    def generic_visit(self, node):
        node_type_str = type(node).__name__
        name = "visit_%s" % (node_type_str,)
        log.debug(
            self.depth_padding()
            + "generic_visit: Providing default ignore case for %s" % (node_type_str,)
        )
        setattr(self, name, self._ignore_function_factory(node_type_str))
        return self._post_visit(node)

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_FunctionDef(self, node_):
        # Scoping Order
        # decorator_list
        # returns
        # args
        #
        # name
        #
        # body (body has name [recursion], args, decorator names in scope)
        # type comment (it's a comment, anyone can write anything there, but other code can't observe it

        # Note: Typing a FunctionDef as its return value would enable swapping a function call for a value

        # name
        def custom_scope_processor_FunctionDef(swapout):
            self.scope.maps[1][swapout.name] = "FunctionDef"
            log.debug(
                self.depth_padding()
                + "Scope after %s name %s"
                % (
                    "FunctionDef",
                    self.scope.maps[:-1],
                )
            )
            return swapout

        return self._visit_impl(
            node_,
            "FunctionDef",
            new_scope=True,
            return_ok=True,
            scope_order=[
                ("decorator_list", "multi-visit"),
                ("returns", "single-visit"),
                ("args", "single-visit"),
                (custom_scope_processor_FunctionDef, "custom"),
                ("body", "multi-visit"),
            ],
        )

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_Lambda(self, node_):
        return self._visit_impl(
            node_,
            "Lambda",
            new_scope=True,
            return_ok=False,
            scope_order=[("args", "single-visit"), ("body", "single-visit")],
        )

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_With(self, node_):
        def custom_scope_processor_WithItems(swapout):
            for withitem in swapout.items:
                type_ = "Any"
                if withitem.optional_vars is not None:
                    vars_to_scope = withitem.optional_vars
                    if isinstance(vars_to_scope, Name):
                        self.scope[vars_to_scope.id] = type_
                    else:
                        raise NotImplementedError("Non-Name Assignment in With")
            return swapout

        return self._visit_impl(
            node_,
            "With",
            new_scope=True,
            scope_order=[
                ("items", "multi-visit"),
                (custom_scope_processor_WithItems, "custom"),
                ("body", "multi-visit"),
            ],
        )

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_Assign(self, node_):
        return self._visit_impl(
            node_,
            "Assign",
            new_scope=False,
            scope_order=[
                ("targets", "multi-visit"),
                ("targets", "multi-name"),
            ],
        )

    def visit_ListCompLike(self, node_, node_name, keys_and_values):
        # Scoping order
        # generators
        # elt
        # ifs (expr, so no assign)

        def custom_scope_processor_KV(swapout):
            for member in keys_and_values:
                log.warning(
                    "custom_scope_processor_KV: %s %s",
                    member,
                    ast_unparse(getattr(swapout, member)),
                )
                setattr(
                    swapout,
                    member,
                    NodeTransformer.visit(self, getattr(swapout, member)),
                )
                assert getattr(swapout, member) is not None
                getattr(swapout, member)._ending_scope = dict(self.scope)
            return swapout

        return self._visit_impl(
            node_,
            node_name,
            new_scope=True,
            scope_order=[
                ("generators", "multi-visit"),
                ("generators", "multi-name"),
                (custom_scope_processor_KV, "custom"),
            ],
        )

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_ListComp(self, node_):
        return self.visit_ListCompLike(node_, "ListComp", ["elt"])

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_DictComp(self, node_):
        return self.visit_ListCompLike(node_, "DictComp", ["key", "value"])

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_SetComp(self, node_):
        return self.visit_ListCompLike(node_, "SetComp", ["elt"])

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_GeneratorExp(self, node_):
        return self.visit_ListCompLike(node_, "GeneratorExp", ["elt"])

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_ClassDef(self, node_):
        # Note: Debuggery for me
        if len(node_.keywords) != 0:
            print(ast_unparse(node_))
            for idx, key in enumerate(node_.keywords):
                print(idx, ast_unparse(key))
            raise NotImplementedError("ClassDef with keywords")

        return self._visit_impl(
            node_,
            "ClassDef",
            new_scope=False,
            scope_order=[
                ("bases", "multi-visit"),
                ("keywords", "multi-visit"),
                ("decorator_list", "multi-visit"),
                ("name", "name"),
                ("body", "multi-visit"),
            ],
        )

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_arg(self, node_):
        return self._visit_impl(
            node_, "arg", new_scope=False, scope_order=[("arg", "name")]
        )

    @littering("scope", "_ending_scope")
    @depth_protection
    def visit_ExceptHandler(self, node_):
        return self._visit_impl(
            node_,
            "ExceptHandler",
            new_scope=True,
            scope_order=[
                ("type", "single-visit"),
                ("name", "name"),
                ("body", "multi-visit"),
            ],
        )

    def _visit_impl(self, node_, node_name, *, new_scope, scope_order, return_ok=None):
        assert len(scope_order) > 0
        log.info(
            self.depth_padding() + "Visiting into %s %s", node_name, ast_unparse(node_)
        )

        if new_scope:
            self.scope = self.scope.new_child()
        if return_ok is not None:
            self.scope["__random_code_return_ok"] = return_ok

        for swapout in getattr(self.corpus, node_name)():
            if self.valid_swap(node_, swapout):
                # Let python scoping drop this variable
                break
        else:
            # no valid swapout found
            log.warning(
                self.depth_padding() + "%s Ending due to no valid swap found", node_name
            )
            swapout = node_

        log.debug(
            self.depth_padding()
            + "Scope at %s start %s"
            % (
                node_name,
                self.scope.maps[:-1],
            )
        )

        if len(scope_order) > 0:
            for field, field_type in scope_order:
                if field_type == "single-visit":
                    if getattr(swapout, field) is not None:
                        setattr(
                            swapout,
                            field,
                            NodeTransformer.generic_visit(
                                self, getattr(swapout, field)
                            ),
                        )
                        assert getattr(swapout, field) is not None
                        getattr(swapout, field)._ending_scope = dict(self.scope)
                elif field_type == "name":
                    if getattr(swapout, field) is not None:
                        # TODO(buck): Types instead of Any
                        type_ = "Any"
                        self.scope[getattr(swapout, field)] = type_
                elif field_type == "multi-visit":
                    for i in range(len(getattr(swapout, field))):
                        getattr(swapout, field)[i] = NodeTransformer.generic_visit(
                            self, getattr(swapout, field)[i]
                        )
                        assert getattr(swapout, field)[i] is not None
                        getattr(swapout, field)[i]._ending_scope = dict(self.scope)
                elif field_type == "multi-name":
                    for generator in getattr(swapout, field):
                        type_ = "Any"
                        # Assignment Case
                        if isinstance(generator, Name):
                            self.scope[generator.id] = type_
                        # Generator case
                        elif isinstance(generator.target, Name):
                            self.scope[generator.target.id] = type_
                        elif isinstance(generator.target, Tuple):
                            for elt in generator.target.elts:
                                if hasattr(elt, "id"):
                                    self.scope[elt.id] = type_
                        else:
                            log.error(swapout)
                            log.error(ast_unparse(swapout))
                            log.error(field)
                            log.error(field_type)
                            log.error(generator)
                            log.error(ast_unparse(generator))
                            if hasattr(generator, "target"):
                                log.error("target")
                                log.error(generator.target)
                                log.error(ast_unparse(generator.target))
                            raise NotImplementedError(
                                "Assignment in a multi-name to non-Names"
                            )
                elif field_type == "custom":
                    log.info(
                        self.depth_padding() + "scope_order selector custom: %s", field
                    )
                    swapout = field(swapout)
                else:
                    raise NotImplementedError(
                        "_visit_impl scope_order selector %s" % (field_type,)
                    )

            result = swapout
        else:
            result = self._post_visit(swapout)

        log.debug(
            self.depth_padding()
            + "Scope at %s end %s"
            % (
                node_name,
                self.scope.maps[:-1],
            )
        )
        if new_scope:
            self.scope = self.scope.parents

        log.debug(
            self.depth_padding() + "Swapped " + str(node_) + " for " + str(result)
        )
        log.debug(self.depth_padding() + "====")
        try:
            log.debug(self.depth_padding() + ast_unparse(node_))
        except RecursionError:
            log.debug(self.depth_padding() + str(node_))
        log.debug(self.depth_padding() + ">>>>")
        try:
            log.debug(self.depth_padding() + ast_unparse(swapout))
        except RecursionError:
            log.debug(self.depth_padding() + str(swapout))
        log.debug(self.depth_padding() + "====")

        log.info(self.depth_padding() + "Visiting out  %s", node_name)
        return result


def the_sauce(gen: BagOfConcepts, start: Module, *, log_level=None):
    transformer = RandomizingTransformer(gen, log_level=log_level)
    result = transformer.visit(start)
    assert result is not None
    # result = fix_missing_locations(result)
    return result


def make_asts(corpus: tList[str]):
    ast_set = {}

    syntax_errors = []

    for corpus_file_path in corpus:
        with open(corpus_file_path) as f:
            file_contents = []
            for line in f:
                file_contents.append(line)
            try:
                ast_set[corpus_file_path] = parse(
                    "\n".join(file_contents), corpus_file_path, type_comments=True
                )
            except SyntaxError:
                syntax_errors.append(corpus_file_path)

    if len(syntax_errors) > 0:
        log.debug("Syntax Mishaps")
        log.debug(syntax_errors[:5])
        log.debug("...")

    return ast_set


def find_files(directory: str):
    import os

    directory = os.path.normpath(directory)
    directory = os.path.realpath(directory)

    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


class RandomCodeSource(object):
    def __init__(self, corpus: tList[str], seed=1, *, log_level=None):
        assert len(corpus) > 0
        if log_level is not None:
            log.setLevel(log_level)

        ast_set = make_asts(corpus)
        raw_materials = merge_unbundled_asts(ast_set.values())
        self.gen = BagOfConcepts(raw_materials, seed=seed)

    def next_source(self):
        starter_home = next(self.gen.Module())
        result = the_sauce(self.gen, starter_home)

        # Five retries
        for i in range(3):
            try:
                text_result = ast_unparse(result)
                return text_result
            except RecursionError as re:
                log.error("Infinite Recursion suspected in result")

        raise ValueError("Random code generation caused a cycle")


# todo: accept str or path
def give_me_random_code(corpus: tList[str], *, log_level=None):
    code_source = RandomCodeSource(corpus, log_level=log_level)

    text_result = code_source.next_source()
    return text_result


def main():
    corpus_paths = list(find_files("corpus"))
    print(corpus_paths)
    print("### Random Code")
    random_source = give_me_random_code(
        ["corpus/int_functions.py", "corpus/main.py"], log_level="DEBUG"
    )
    print(random_source)


if __name__ == "__main__":
    main()

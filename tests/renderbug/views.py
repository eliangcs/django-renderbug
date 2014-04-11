from django.http import HttpResponse
from django.shortcuts import render
from django.template import VariableNode
from django.template.defaulttags import ForNode, IfNode
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode
from faker import Faker

from django.template import TOKEN_TEXT, TOKEN_VAR
from dotdict import dotdict


# faker = Faker()


# def populate(expression, context=None, value=None):
#     if context is None:
#         context = {}

#     tokens = expression.split('.')
#     num_tokens = len(tokens)
#     current = context
#     for i, token in enumerate(tokens):
#         if i < num_tokens - 1:
#             current[token] = {}
#             current = current[token]
#         else:
#             current[token] = value
#     return context


# def populate_variable_node(node):
#     expr = node.filter_expression.var.var
#     return populate(expr, value=faker.name())


# def populate_if_node(node):
#     try:
#         expr = node.conditions_nodelists[0][0].text
#     except Exception as e:
#         print repr(e)
#         expr = ''
#         print type(node.conditions_nodelists[0][0]).__module__
#         print type(node.conditions_nodelists[0][0]).__name__
#     return populate(expr, value=True)


# def populate_for_node(node):
#     expr = node.sequence.var.var
#     arr = [{ 'name': faker.name(), 'email': faker.email() } for __ in xrange(10)]
#     return populate(expr, value=arr)


# def populate_container_node(node):
#     context = {}
#     for node in node.nodelist:
#         populator = find_populator(type(node))
#         if populator:
#             context.update(populator(node))
#     return context


# POPULATORS = {
#     BlockNode: populate_container_node,
#     ExtendsNode: populate_container_node,
#     ForNode: populate_for_node,
#     IfNode: populate_if_node,
#     VariableNode: populate_variable_node,
# }


# def find_populator(node_type):
#     populator = POPULATORS.get(node_type)
#     if populator:
#         return populator

#     for k, v in POPULATORS.iteritems():
#         if issubclass(node_type, k):
#             return v

#     return None


def stringify_node(node, indent=0):
    prefix = ' ' * indent
    result = ['%s%r' % (prefix, repr(node))]
    for attr in node.child_nodelists:
        nodelist = getattr(node, attr, None)
        if nodelist:
            result.append(stringify_nodelist(nodelist, indent + 4))
    return '\n'.join(result)


def stringify_nodelist(nodelist, indent=0):
    result = [stringify_node(node, indent) for node in nodelist]
    return '\n'.join(result)


def print_node_tree(request, path):
    t = get_template(path)
    return HttpResponse(stringify_nodelist(t.nodelist))


faker = Faker()


def merge_context(c1, c2):
    for k, v in c2.iteritems():
        if isinstance(v, dict) and isinstance(c1.get(k), dict):
            merge_context(c1[k], v)
        else:
            c1[k] = v


def populate(expression, value=None):
    context = dotdict()

    tokens = expression.split('.')
    num_tokens = len(tokens)
    current = context
    for i, token in enumerate(tokens):
        if i < num_tokens - 1:
            if not isinstance(current.get(token), dict):
                current[token] = dotdict()
            current = current[token]
        else:
            current[token] = value
    return context


def populate_variable_node(node):
    expr = node.filter_expression.var.var
    return populate(expr, value=faker.name())


def populate_operator(op, value):
    route = {
        'literal': populate_literal,
        'or': populate_operator_or,
        'and': populate_operator_and,
        'not': populate_operator_not,
        'in': None,
        'not in': None,
        '=': None,
        '==': None,
        '!=': None,
        '>': None,
        '>=': None,
        '<': None,
        '<=': None
    }
    populator = route.get(op.id)
    if populator:
        return populator(op, value)
    return dotdict()


def populate_literal(literal, value):
    return populate(literal.text, value)


def populate_operator_or(op, value):
    if value:
        context = populate_operator(op.first, True)
    else:
        context = populate_operator(op.first, False)
        context.update(populate_operator(op.second, False))
    return context


def populate_operator_and(op, value):
    if value:
        context = populate_operator(op.first, True)
        context.update(populate_operator(op.second, True))
    else:
        context = populate_operator(op.first, False)
    return context


def populate_operator_not(op, value):
    return populate_operator(op.first, False)


def populate_if_node(node):
    context = dotdict()
    first_cond = node.conditions_nodelists[0][0]
    merge_context(context, populate_operator(first_cond, True))

    first_body_nodes = node.conditions_nodelists[0][1]
    merge_context(context, fake_context_from_nodelist(first_body_nodes))

    return context


def populate_for_node(node):
    expr = node.sequence.var.var
    loopvars = node.loopvars
    arr = []
    for __ in xrange(3):
        c = dotdict()
        for child_node in node.nodelist_loop:
            merge_context(c, fake_context_from_node(child_node))

        for loopvar in loopvars:
            loopvar_context = c.pop(loopvar)
            if loopvar_context and isinstance(loopvar_context, dict):
                c.update(loopvar_context)

        arr.append(c)
    return populate(expr, value=arr)


def populate_container_node(node):
    context = dotdict()
    for child_node in node.nodelist:
        populator = find_populator(type(child_node))
        if populator:
            context.update(populator(child_node))
    return context


def populate_blocktrans_node(node):
    context = dotdict()
    tokens = node.singular
    for token in tokens:
        if token.token_type == TOKEN_VAR:
            context[token.contents] = faker.name()
    return context


def find_populator(node_type):
    if not isinstance(node_type, basestring):
        node_type = '%s.%s' % (node_type.__module__, node_type.__name__)
    return _POPULATORS.get(node_type)


_POPULATORS = {
    'django.template.loader_tags.BlockNode': populate_container_node,
    'django.template.loader_tags.ExtendsNode': populate_container_node,
    'django.template.defaulttags.ForNode': populate_for_node,
    'django.template.defaulttags.IfNode': populate_if_node,
    'django.template.VariableNode': populate_variable_node,
    'django.template.debug.DebugVariableNode': populate_variable_node,
    'django.templatetags.i18n.BlockTranslateNode': populate_blocktrans_node
}


def fake_context_from_node(node):
    populator = find_populator(type(node))
    if populator:
        return populator(node)
    return dotdict()


def fake_context_from_nodelist(nodelist):
    context = dotdict()
    for node in nodelist:
        merge_context(context, fake_context_from_node(node))
    return context


def render_template(request, path):
    t = get_template(path)
    context = dotdict(
        request=dotdict(GET={}))

    merge_context(context, fake_context_from_nodelist(t.nodelist))
    import pprint
    pprint.pprint(context)

    return render(request, path, context)


# def render_template(request, path):
#     context = {}
#     t = get_template(path)
#     for node in t.nodelist:
#         populator = find_populator(type(node))
#         if populator:
#             context.update(populator(node))
#     import pprint
#     pprint.pprint(context)
#     return render(request, path, context)

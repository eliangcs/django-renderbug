from django.shortcuts import render
from django.template import VariableNode
from django.template.defaulttags import ForNode, IfNode
from django.template.loader import get_template
from faker import Faker


faker = Faker()


def populate(expression, context=None, value=None):
    if context is None:
        context = {}

    tokens = expression.split('.')
    num_tokens = len(tokens)
    current = context
    for i, token in enumerate(tokens):
        if i < num_tokens - 1:
            current[token] = {}
            current = current[token]
        else:
            current[token] = value
    return context


def populate_variable_node(node):
    expr = node.filter_expression.var.var
    return populate(expr, value=faker.name())


def populate_if_node(node):
    expr = node.conditions_nodelists[0][0].text
    return populate(expr, value=True)


def populate_for_node(node):
    expr = node.sequence.var.var
    arr = [{ 'name': faker.name(), 'email': faker.email() } for __ in xrange(10)]
    return populate(expr, value=arr)


POPULATORS = {
    ForNode: populate_for_node,
    IfNode: populate_if_node,
    VariableNode: populate_variable_node,
}


def find_populator(node_type):
    populator = POPULATORS.get(node_type)
    if populator:
        return populator

    for k, v in POPULATORS.iteritems():
        if issubclass(node_type, k):
            return v

    return None


def render_template(request, path):
    context = {}
    t = get_template(path)
    for node in t.nodelist:
        populator = find_populator(type(node))
        if populator:
            context.update(populator(node))
    import pprint
    pprint.pprint(context)
    return render(request, path, context)

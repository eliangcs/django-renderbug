from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import render
from faker import Faker


def index(request):
    return HttpResponse('Hello world')


class SuperContext(dict):

    def __init__(self):
        self.faker = Faker()

    def __getitem__(self, name):
        print name
        if name == 'name':
            return self.faker.name()
        if name == 'title':
            return self.faker.country()
        return super(SuperContext, self).__getitem__(name)

    def __iter__(self):
        a = ['name', 'title']
        for aa in a:
            print aa
            yield aa


faker = Faker()


def populate_variable_node(node):
    var_name = node.filter_expression.var.var
    return { var_name: faker.name() }


NODE_TYPES = {
    'DebugVariableNode': populate_variable_node,
    'VariableNode': populate_variable_node
}


def render_template(request, path):
    context = {}
    t = get_template(path)
    for node in t.nodelist:
        node_type = type(node).__name__
        print node_type
        populate = NODE_TYPES.get(node_type)
        if populate:
            context.update(populate(node))
    return render(request, path, context)

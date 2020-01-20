import json

from django.db import transaction

from rest_framework.decorators import api_view
from rest_framework.response import Response

from editor.models import Function, FunctionTemplateLink
from editor.models import ComponentTemplate, ComponentTemplateLink
from editor.models import Variable, VariableType
from editor.models import Rule, Component, ComponentArgument


def get_serialized_functions():
    functions = []
    for f in Function.objects.all():
        serialized_function = {
            'category': f.category,
            'return_type': f.return_type,
            'name': f.name,
            'links': [],
        }
        for ftl in FunctionTemplateLink.objects.filter(function=f):
            function_template_link = {
                'type': ftl.type,
            }
            if ftl.type == 'text':
                function_template_link['text'] = ftl.text
            elif ftl.type == 'argument':
                function_template_link['key'] = ftl.key
                function_template_link['default_value'] = ftl.default_value
            serialized_function['links'].append(function_template_link)
        functions.append(serialized_function)

    return functions


def get_serialized_component_templates(context):
    component_templates = []
    for ct in ComponentTemplate.objects.filter(context=context):
        component_template = {
            'name': ct.name,
            'links': [],
        }
        for ctl in ComponentTemplateLink.objects.filter(template=ct):
            component_template_link = {
                'type': ctl.type,
            }
            if ctl.type == 'text':
                component_template_link['text'] = ctl.text
            elif ctl.type == 'argument':
                component_template_link['key'] = ctl.key
                component_template_link['default_value'] = ctl.default_value
            component_template['links'].append(component_template_link)

        component_templates.append(component_template)

    return component_templates


@api_view(['GET'])
def get_templates(request):
    response = {
        'function': get_serialized_functions(),
        'trigger': get_serialized_component_templates('trigger'),
        'condition': get_serialized_component_templates('condition'),
        'action': get_serialized_component_templates('action'),
    }

    return Response(response)


def get_serialized_variables():
    variables = []
    for v in Variable.objects.all():
        variable = {
            'id': v.id,
            'name': v.name,
            'init_value': v.init_value,
            'list': v.list,
            'types': [],
        }
        for vt in VariableType.objects.filter(variable=v):
            variable['types'].append(vt.type)
        variables.append(variable)

    return variables


def get_serialized_components(rule, context):
    components = []
    for c in Component.objects.filter(rule=rule, template__context=context):
        component = {
            'id': c.id,
            'template': c.template.name,
            'arguments': {},
        }
        for ca in ComponentArgument.objects.filter(component=c):
            component['arguments'][ca.key] = json.loads(ca.value)
        components.append(component)

    return components


def get_serialized_rules():
    rules = []
    for r in Rule.objects.all():
        rule = {
            'id': r.id,
            'name': r.name,
            'triggers': get_serialized_components(r, 'trigger'),
            'conditions': get_serialized_components(r, 'condition'),
            'actions': get_serialized_components(r, 'action'),
        }
        rules.append(rule)
    return rules


@api_view(['GET'])
def get_scenario(request):
    # scenario_id = int(request.GET.get('scenario_id'))

    response = {
        'variables': get_serialized_variables(),
        'rules': get_serialized_rules(),
    }

    return Response(response)


def create_components(rule, components, context):
    for index, component in enumerate(components):
        template = ComponentTemplate.objects.get(
            name=component['template'],
            context=context,
        )
        new_component = Component(
            rule=rule,
            template=template,
            index=index,
        )
        new_component.save()

        for key, value in component['arguments'].items():
            ComponentArgument(
                component=new_component,
                key=key,
                value=json.dumps(value),
            ).save()


def update_component_arguments(component, arguments):
    argument_keys = {*arguments.keys()}

    old_arguments = ComponentArgument.objects.filter(component=component)
    old_argument_keys = {a.key for a in old_arguments}

    # Delete
    keys_to_delete = old_argument_keys - argument_keys
    old_arguments.filter(key__in=keys_to_delete, component=component)

    # Update
    keys_to_update = argument_keys & old_argument_keys
    for key in keys_to_update:
        value = json.dumps(arguments[key])
        argument_to_update = ComponentArgument.objects.get(component=component, key=key)

        if argument_to_update.value != value:
            argument_to_update.value = value
            argument_to_update.save()

    # Create
    arguments_to_create = {key: value for key, value in arguments.items() if key not in keys_to_update}
    for key, value in arguments_to_create:
        ComponentArgument(
            component=component,
            key=key,
            value=json.dumps(value),
        ).save()


def update_components(rule, components, context):
    component_ids = {c.get('id', None) for c in components}
    component_ids.discard(None)

    old_components = Component.objects.all()
    old_component_ids = {c.id for c in old_components}

    # Delete
    ids_to_delete = old_component_ids - component_ids
    old_components.filter(id__in=ids_to_delete, rule=rule, template__context=context).delete()

    # Update
    ids_to_update = component_ids & old_component_ids
    for id_ in ids_to_update:
        save = False
        component = [c for c in components if c.get('id', None) == id_][0]
        component_to_update = Component.objects.get(id=id_)

        template = ComponentTemplate.objects.get(name=component['template'])
        if component_to_update.template != template:
            component_to_update.template = template
            save = True

        if component_to_update.index != components.index(component):
            component_to_update.index = components.index(component)
            save = True

        if save:
            component_to_update.save()

        # Update arguments
        update_component_arguments(component_to_update, component['arguments'])

    # Create
    components_to_create = [c for c in components if c.get('id', None) not in ids_to_update]
    create_components(rule, components_to_create, context)


def update_rules(rules):
    rule_ids = {r.get('id', None) for r in rules}
    rule_ids.discard(None)

    old_rules = Rule.objects.all()
    old_rule_ids = {r.id for r in old_rules}

    # Delete
    ids_to_delete = old_rule_ids - rule_ids
    old_rules.filter(id__in=ids_to_delete).delete()

    # Update
    ids_to_update = rule_ids & old_rule_ids
    for id_ in ids_to_update:
        save = False
        rule = [r for r in rules if r.get('id', None) == id_][0]
        rule_to_update = Rule.objects.get(id=id_)

        if rule_to_update.name != rule['name']:
            rule_to_update.name = rule['name']
            save = True

        if rule_to_update.index != rules.index(rule):
            rule_to_update.index = rules.index(rule)
            save = True

        if save:
            rule_to_update.save()

        # Update components
        update_components(rule_to_update, rule['triggers'], 'trigger')
        update_components(rule_to_update, rule['conditions'], 'condition')
        update_components(rule_to_update, rule['actions'], 'action')

    # Create
    rules_to_create = [r for r in rules if r.get('id', None) not in ids_to_update]
    for rule in rules_to_create:
        new_rule = Rule(
            name=rule['name'],
            index=rules.index(rule),
        )
        new_rule.save()

        create_components(new_rule, rule['triggers'], 'trigger')
        create_components(new_rule, rule['conditions'], 'condition')
        create_components(new_rule, rule['actions'], 'action')


def update_variable_types(variable, types):
    old_types = {t.type for t in VariableType.objects.filter(variable=variable)}
    new_types = {*types}

    # Delete
    types_to_delete = old_types - new_types
    VariableType.objects.filter(
        variable=variable, type__in=types_to_delete).delete()

    # Create
    types_to_create = new_types - old_types
    for type_ in types_to_create:
        VariableType(variable=variable, type=type_).save()


def update_variables(variables):
    variable_ids = {v.get('id', None) for v in variables}
    variable_ids.discard(None)

    old_variables = Variable.objects.all()
    old_variable_ids = {v.id for v in old_variables}

    # Delete
    ids_to_delete = old_variable_ids - variable_ids
    old_variables.filter(id__in=ids_to_delete).delete()

    # Update
    ids_to_update = variable_ids & old_variable_ids
    for id_ in ids_to_update:
        save = False
        variable = [v for v in variables if v.get('id', None) == id_][0]
        variable_to_update = Variable.objects.get(id=id_)

        if variable_to_update.name != variable['name']:
            variable_to_update.name = variable['name']
            save = True

        if variable_to_update.index != variables.index(variable):
            variable_to_update.index = variables.index(variable)
            save = True

        if variable_to_update.init_value != variable['init_value']:
            variable_to_update.init_value = variable['init_value']
            save = True

        if variable_to_update.list != variable['list']:
            variable_to_update.list = variable['list']
            save = True

        if save:
            variable_to_update.save()

        # Update types
        update_variable_types(variable_to_update, variable['types'])

    # Create
    variables_to_create = [v for v in variables if v.get('id', None) not in ids_to_update]
    for variable in variables_to_create:
        new_variable = Variable(
            name=variable['name'],
            index=variables.index(variable),
            init_value=variable['init_value'],
            list=variable['list'],
        )
        new_variable.save()

        for type_ in variable['types']:
            new_type = VariableType(
                variable=new_variable,
                type=type_,
            )
            new_type.save()


@api_view(['POST'])
def update_scenario(request):
    # scenario_id = int(request.POST.get('scenario_id'))
    rules = json.loads(request.POST.get('rules'))
    variables = json.loads(request.POST.get('variables'))

    with transaction.atomic():
        update_rules(rules)
        update_variables(variables)

    response = {
        'variables': get_serialized_variables(),
        'rules': get_serialized_rules(),
    }

    return Response(response)
import datetime
from django import template

register = template.Library()


@register.simple_tag
def switch(value, *args, **kwargs):
    if len(args) % 2 != 0:
        raise template.TemplateSyntaxError(
            "switch tag requires pairs of arguments"
        )
    for i in range(0, len(args), 2):
        if value == args[i]:
            return args[i + 1]



from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    return float(value) - float(arg)

@register.filter
def div(value, arg):
    return float(value) / float(arg)

@register.filter
def mult(value, arg):
    return float(value) * float(arg)

@register.filter
def positive(value):
    return float(value) >= 0
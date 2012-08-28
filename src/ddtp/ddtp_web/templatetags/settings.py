from django.template import TemplateSyntaxError, Variable, Node, Variable, Library
from django.conf import settings

register = Library()
# I found some tricks in URLNode and url from defaulttags.py:
# https://code.djangoproject.com/browser/django/trunk/django/template/defaulttags.py
@register.tag
def setting(parser, token):
    """ templatetag for accessing settings from templates. Can be used either as

    {% setting 'DEBUG' %}

    to use value directly. Or as

    {% setting 'DEBUG' as variable %}

    to store value in variable.

    Found on stackoverflow: http://stackoverflow.com/revisions/6343321/3
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one " \
          "argument (settings constant to retrieve)" % bits[0])
    settingsvar = bits[1]
    settingsvar = settingsvar[1:-1] if settingsvar[0] == '"' else settingsvar
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]
    if len(bits):
        raise TemplateSyntaxError("'value_from_settings' didn't recognise " \
          "the arguments '%s'" % ", ".join(bits))
    return ValueFromSettings(settingsvar, asvar)

class ValueFromSettings(Node):
    def __init__(self, settingsvar, asvar):
        self.arg = Variable(settingsvar)
        self.asvar = asvar
    def render(self, context):
        ret_val = getattr(settings,self.arg.resolve(context))
        if self.asvar:
            context[self.asvar] = ret_val
            return ''
        else:
            return ret_val

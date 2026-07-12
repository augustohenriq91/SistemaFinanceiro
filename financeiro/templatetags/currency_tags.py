from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()

@register.filter
def format_brl(value):
    if value is None:
        return ''

    try:
        valor = Decimal(value)
    except (TypeError, ValueError, InvalidOperation):
        return value

    valor = valor.quantize(Decimal('0.01'))
    valor_str = f'{valor:,.2f}'
    valor_str = valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'R$ {valor_str}'

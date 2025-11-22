from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the given value by the argument"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return None

@register.filter
def sub(value, arg):
    """Subtract the argument from the given value"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return None

@register.filter
def currency(value):
    """Format a number as currency"""
    try:
        decimal_val = Decimal(str(value))
        return f"₹{decimal_val:,.2f}"
    except (ValueError, TypeError, InvalidOperation):
        return value

@register.filter
def percentage(value):
    """Format a number as percentage"""
    try:
        decimal_val = Decimal(str(value))
        return f"{decimal_val:,.2f}%"
    except (ValueError, TypeError, InvalidOperation):
        return value

@register.filter
def gain_loss_class(value):
    """Return CSS class based on positive/negative value"""
    try:
        val = float(value)
        return 'price-up' if val > 0 else 'price-down' if val < 0 else ''
    except (ValueError, TypeError):
        return ''

@register.filter
def format_pnl(value):
    """Format P/L value with color class and proper formatting"""
    try:
        val = Decimal(str(value))
        class_name = 'price-up' if val > 0 else 'price-down' if val < 0 else ''
        formatted_val = f"₹{abs(val):,.2f}"
        prefix = '+' if val > 0 else '-' if val < 0 else ''
        return f'<span class="{class_name}">{prefix}{formatted_val}</span>'
    except (ValueError, TypeError, InvalidOperation):
        return value

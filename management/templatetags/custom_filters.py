from django import template
from accounts.models import Transaction, Deposit
from django.contrib.auth.models import User
import json
from django.db.models import Sum

register = template.Library()

@register.filter(name='user_data_json')
def user_data_json(user_id):
    u = User.objects.get(id=user_id)
    profile = getattr(u, 'profile', None)
    if profile:
        total_earnings = profile.total_earned
    else:
        total_earnings = 0
    total_deposits = Deposit.objects.filter(wallet__user=u).aggregate(total=Sum('amount'))['total'] or 0
    total_withdrawals = Transaction.objects.filter(user=u, transaction_type='withdraw', status="approved")
    total_pending_withdrawals = Transaction.objects.filter(user=u, transaction_type="withdraw", status="pending").aggregate(total=Sum("amount"))["total"] or 0
    
    data = {
        'id': u.id,
        'total_balance': float(u.profile.balance),
        'total_earnings': float(total_earnings),
        'total_deposits': float(total_deposits),
        'total_withdrawals_count': total_withdrawals.count(),
        'total_withdrawals': float(total_withdrawals.aggregate(total=Sum('amount'))['total'] or 0),
        'total_pending_withdrawals': float(total_pending_withdrawals),
    }
    return json.dumps(data)

@register.filter(name='json_value')
def json_value(value, key):
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return value.get(key, '')
    except Exception:
        return ''
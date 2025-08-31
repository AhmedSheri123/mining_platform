from decimal import Decimal
import random

def get_earnings_increment(profit):
    """
    حساب زيادة الأرباح لكل 10 ثواني باستخدام min و max مع عامل عشوائي
    والدقة الافتراضية لـ Decimal
    """
    # ربح كل 10 ثواني من الحدين
    min_profit = Decimal(profit) / Decimal('3600')
    max_profit = (profit + (profit * Decimal('0.05'))) / Decimal('3600')


    # التأكد من ترتيب min و max
    if min_profit > max_profit:
        min_profit, max_profit = max_profit, min_profit

    # رقم عشوائي بين min و max
    earnings_increment = min_profit + (max_profit - min_profit) * Decimal(str(random.random()))

    # لا نقوم بتقريب أو تقليل الدقة
    return earnings_increment

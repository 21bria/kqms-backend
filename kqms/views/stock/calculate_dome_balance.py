from datetime import timedelta
from django.db.models import Sum
from decimal import Decimal
from ...models.stock_balance import DomeBalance
from ...models.ore_productions import OreProductions
from ...models.selling_data import SellingProductions

def calculate_dome_balance(dome, material, date):
    prev_date = date - timedelta(days=1)

    prev_balance = DomeBalance.objects.filter(
        dome=dome, material=material, date=prev_date
    ).first()

    opening = prev_balance.closing_balance if prev_balance else Decimal('0')

    masuk = OreProductions.objects.filter(
        id_pile=dome,
        material=material,
        tgl_production=date
    ).aggregate(total=Sum('volume'))['total'] or Decimal('0')

    keluar = SellingProductions.objects.filter(
        id_pile=dome,
        material=material,
        tgl_selling=date
    ).aggregate(total=Sum('volume'))['total'] or Decimal('0')

    closing = opening + masuk - keluar

    DomeBalance.objects.update_or_create(
        dome=dome, material=material, date=date,
        defaults={
            'opening_balance': opening,
            'total_in': masuk,
            'total_out': keluar,
            'closing_balance': closing
        }
    )
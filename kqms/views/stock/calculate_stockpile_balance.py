from datetime import timedelta
from django.db.models import Sum
from decimal import Decimal
from ...models.stock_balance import StockpileBalance
from ...models.ore_productions import OreProductions
from ...models.selling_data import SellingProductions

def calculate_stockpile_balance(stockpile, material, date):
    prev_date = date - timedelta(days=1)

    prev_balance = StockpileBalance.objects.filter(
        id_stockpile=stockpile, material=material, date=prev_date
    ).first()

    opening = prev_balance.closing_balance if prev_balance else Decimal('0')

    masuk = OreProductions.objects.filter(
        id_stockpile=stockpile,
        material=material,
        tgl_production=date
    ).aggregate(total=Sum('volume'))['total'] or Decimal('0')

    keluar = SellingProductions.objects.filter(
        id_stockpile=stockpile,
        material=material,
        tgl_selling=date
    ).aggregate(total=Sum('volume'))['total'] or Decimal('0')

    closing = opening + masuk - keluar

    StockpileBalance.objects.update_or_create(
        id_stockpile=stockpile,
        material=material,
        date=date,
        defaults={
            'opening_balance': opening,
            'total_in': masuk,
            'total_out': keluar,
            'closing_balance': closing
        }
    )

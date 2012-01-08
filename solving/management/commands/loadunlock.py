from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from hunt.solving.models import UnlockBatch

unlock_batch_time = [
#batch, base_hours, minutes_early_per_point,
(1100, 0, 0),
(1101, 0, 0),
(1200, 6, 60),
(1201, 6, 60),
(1202, 8, 7.25307125307125),
(2100, 10, 1.53627311522048),
(2101, 10, 1.53627311522048),
(2102, 12, 1.038350603568),
(2200, 14, 0.45510026155187),
(2201, 14, 0.45510026155187),
(2202, 16, 0.30141094152474),
(3100, 18, 0.17775878645444),
(3101, 18, 0.17775878645444),
(3102, 20, 0.15554329840044),
(3103, 22, 0.10384769005459),
(3104, 24, 0.073426573426573),
(3200, 26, 0.054234167525541),
(3201, 26, 0.054234167525541),
(3202, 28, 0.046264375378299),
(4100, 30, 0.03605705289747),
(4101, 30, 0.03605705289747),
(4102, 32, 0.034297077775339),
(4103, 33, 0.02861635041311),
(4200, 34, 0.023793947266249),
(4201, 34, 0.023793947266249),
(4202, 35, 0.021763961104465),
(4203, 36, 0.01839686515979),
(5100, 37, 0.016986820025978),
(5101, 37, 0.016986820025978),
(5102, 38, 0.014557385415494),
(5103, 39, 0.013547715319369),
(5200, 40, 0.011911402327742),
(5201, 40, 0.011911402327742),
(5202, 41, 0.009816229174935),
(6100, 42, 0.008748368615085),
(6101, 42, 0.008748368615085),
(6102, 43, 0.007835023314899),
(6200, 44, 0.00566573973976),
(6201, 44, 0.00566573973976),
]

class Command(BaseCommand):
    help = """Load unlock data"""

    def handle(self, *args, **options):
        for batch_number, base_hours, minutes_early_per_point in unlock_batch_time:
            batch = list(UnlockBatch.objects.filter(batch=batch_number))
            if batch:
                batch = batch[0]
                batch.base_time = base_hours * 60 * 60 #convert to seconds
                batch.minutes_early_per_point = minutes_early_per_point
            else:
                batch = UnlockBatch(batch=batch_number,
                              base_time=base_hours * 60 * 60,
                              minutes_early_per_point=minutes_early_per_point)
            batch.save()


from django.db.models.signals import post_save
from threading import Thread

from .models import Answer, Statistics


def recalculate_statistics(sender, instance, created, **kwargs):
    statistics = Statistics.objects.get_or_create(user=instance.user)[0]
    thread = Thread(target=statistics.recalculate)
    thread.start()


post_save.connect(recalculate_statistics, sender=Answer)

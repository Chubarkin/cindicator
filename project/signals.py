from django.contrib.auth.models import Group, User, Permission
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType

from questionnaire.models import Question


def update_groups(sender, instance, created, **kwargs):
    admin_group, created = Group.objects.get_or_create(name='Admin')
    if created:
        content_type = ContentType.objects.get_for_model(Question)
        permissions = Permission.objects.filter(content_type=content_type)
        admin_group.permissions.add(*permissions)


post_save.connect(update_groups, sender=User)

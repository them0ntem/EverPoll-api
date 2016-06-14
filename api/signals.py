from pprint import pprint

from django.conf import settings
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

from .models import Room, Choice


def user_add_validation(sender, **kwargs):
	if kwargs['instance'].owner in kwargs['instance'].users.all():
		raise ValidationError({"non_field_errors":["Owner cannot be users of the room"]})
	elif kwargs['instance'].public == False and kwargs['instance'].users.count() > 10:
		raise ValidationError({"non_field_errors":["User limit exceed"]})


m2m_changed.connect(user_add_validation, sender=Room.users.through)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
	if created:
		Token.objects.create(user=instance)

from django.apps import AppConfig


class PollConfig(AppConfig):
	name = 'api'

	def ready(self):
		import api.signals

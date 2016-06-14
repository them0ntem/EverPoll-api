import time
from datetime import datetime

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions

from .models import *


def time_ago_in_words(time=False):
	"""
	Get a datetime object or a int() Epoch timestamp and return a
	pretty string like 'an hour ago', 'Yesterday', '3 months ago',
	'just now', etc
	"""
	now = timezone.now()
	if type(time) is int:
		diff = now - datetime.fromtimestamp(time)
	elif isinstance(time, datetime):
		diff = now - time
	elif not time:
		diff = now - now

	second_diff = diff.seconds
	day_diff = diff.days
	if day_diff < 0:
		return ''

	if day_diff == 0:
		if second_diff < 10:
			return "just now"
		if second_diff < 60:
			return str(second_diff) + " seconds ago"
		if second_diff < 120:
			return "a minute ago"
		if second_diff < 3600:
			return str(int(second_diff / 60)) + " minutes ago"
		if second_diff < 7200:
			return "an hour ago"
		if second_diff < 86400:
			return str(int(second_diff / 3600)) + " hours ago"
	if day_diff == 1:
		return "Yesterday"
	if day_diff < 7:
		return str(day_diff) + " days ago"
	if day_diff < 31:
		return str(int(day_diff / 7)) + " weeks ago"
	if day_diff < 365:
		return str(int(day_diff / 30)) + " months ago"
	return str(int(day_diff / 365)) + " years ago"


class ChoiceSerializers(serializers.ModelSerializer):
	class Meta:
		model = Choice
		fields = ('id', 'choice_text', 'votes', 'question')
		read_only_fields = ('votes', )
		extra_kwargs = {
			'question': {'required': False},
		}

	def validate(self, attrs):
		try:
			if Choice.objects.filter(question=attrs['question']).count() >= 4:
				msg = _('Can\'t add more than four choice')
				raise serializers.ValidationError(msg)
			elif self.context['request'].user != attrs['question'].set.owner:
				msg = _('Not Authorised to add choice to this question')
				raise exceptions.NotAuthenticated(msg)
		except Choice.DoesNotExist:
			pass
		except KeyError:
			pass

		return attrs


class QuestionSerializers(serializers.ModelSerializer):
	choice = ChoiceSerializers(many=True)

	class Meta:
		model = Question
		fields = ('id', 'question_text', 'set', 'choice')
		extra_kwargs = {
			'set': {'required': False},
		}

	def validate(self, attrs):
		try:
			if Question.objects.filter(set=attrs['set']).count() >= 10:
				msg = _('Can\'t add more than ten question')
				raise serializers.ValidationError(msg)
			elif self.context['request'].user != attrs['set'].owner:
				msg = _('Not Authorised to add question to this set')
				raise exceptions.NotAuthenticated(msg)
		except Question.DoesNotExist:
			pass
		except KeyError:
			pass

		return attrs

	def create(self, validated_data):
		choices_data = validated_data.pop('choice')
		question = Question.objects.create(**validated_data)
		for choice_data in choices_data:
			Choice.objects.create(question=question, **choice_data)
		return question


class QuestionSetListSerializers(serializers.ModelSerializer):
	owner = serializers.ReadOnlyField(source='owner.username')
	question = QuestionSerializers(many=True)

	class Meta:
		model = QuestionSet
		fields = ('id', 'name', 'owner', 'question')
		extra_kwargs = {
			'question': {'write_only': True},
		}


	def create(self, validated_data):
		questions_data = validated_data.pop('question')
		question_set = QuestionSet.objects.create(**validated_data)
		for question_data in questions_data:
			choices_data = question_data.pop('choice')
			question = 	Question.objects.create(set=question_set, **question_data)

			for choice_data in choices_data:
				Choice.objects.create(question=question, **choice_data)
		return question_set


	def validate(self, attrs):
		try:
			q= QuestionSet.objects.get(name=attrs['name'], owner=self.context['request'].user)
			print(q.id)
		except QuestionSet.DoesNotExist:
			pass
		except KeyError:
			pass
		else:
			# msg = _('A Question set with that user already exists')
			# raise serializers.ValidationError(msg)
			pass
		return attrs


class QuestionSetDetailSerializers(QuestionSetListSerializers):
	question = QuestionSerializers(many=True, read_only=True)

	class Meta(QuestionSetListSerializers.Meta):
		fields = ('id', 'name', 'owner', 'question')


class RoomSerializers(serializers.ModelSerializer):
	owner = serializers.ReadOnlyField(source='owner.username')
	days_ago = serializers.SerializerMethodField()
	response = serializers.SerializerMethodField()

	class Meta:
		model = Room
		fields = (
			'id', 'name', 'description', 'owner', 'question_set', 'destroyed', 'public', 'response', 'days_ago'
		)

	def validate(self, attrs):
		try:
			Room.objects.get(name=attrs['name'], owner=self.context['request'].user)
		except Room.DoesNotExist:
			pass
		except KeyError:
			pass
		else:
			msg = _('A Room with that user already exists')
			raise serializers.ValidationError(msg)

		return attrs

	@staticmethod
	def get_days_ago(obj):
		return time_ago_in_words(obj.created)

	@staticmethod
	def get_response(obj):
		return obj.users.count()

class RoomDetailSerializers(RoomSerializers):
	question_set_detail = QuestionSetDetailSerializers(source='question_set')

	class Meta(RoomSerializers.Meta):
		fields = (
			'id', 'name', 'description', 'owner', 'destroyed', 'public', 'response', 'days_ago', 'question_set_detail',
		)



class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ('id', 'password', 'email', 'first_name', 'last_name')
		extra_kwargs = {
			'password': {'write_only': True},
			'first_name': {'required': True},
			'last_name': {'required': True},
			'email': {'required': True},
		}
		read_only_fields = ('id',)

	def create(self, validated_data):
		user = User.objects.create(
			username=self.get_unique_username(),
			email=validated_data['email'],
			first_name=validated_data['first_name'],
			last_name=validated_data['last_name']
		)

		user.set_password(validated_data['password'])
		user.save()

		return user

	def get_unique_username(self):
		username = (self.validated_data['first_name'] + self.validated_data['last_name']).replace(' ', '').lower()

		while True:
			username += str(int(time.time() * 1000))
			if User.objects.filter(username=username).exists():
				username += str(int(time.time() * 1000))
			else:
				break
		return username

	@staticmethod
	def validate_email(value):
		if value in User.objects.values_list('email', flat=True):
			raise serializers.ValidationError("A user with that email already exists.")
		return value


class AuthTokenSerializer(serializers.Serializer):
	email = serializers.CharField(label=_("Email"))
	password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})

	def validate(self, attrs):
		email_or_username = attrs.get('email')
		password = attrs.get('password')

		if email_or_username and password:
			if self.validate_email_bool(email_or_username):
				try:
					user_request = User.objects.get(email=email_or_username)
				except User.DoesNotExist:
					msg = _('Unable to log in with provided credentials.')
					raise serializers.ValidationError(msg)
				email_or_username = user_request.username
			user = authenticate(username=email_or_username, password=password)

			if user:
				if not user.is_active:
					msg = _('User account is disabled.')
					raise serializers.ValidationError(msg)
			else:
				msg = _('Unable to log in with provided credentials.')
				raise serializers.ValidationError(msg)

		else:
			msg = _('Must include "email" and "password".')
			raise serializers.ValidationError(msg)

		attrs['user'] = user
		return attrs

	@staticmethod
	def validate_email_bool(email):
		from django.core.validators import validate_email
		from django.core.exceptions import ValidationError
		try:
			validate_email(email)
			return True
		except ValidationError:
			return False

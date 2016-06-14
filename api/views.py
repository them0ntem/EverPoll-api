import django_filters
from django.contrib.auth.models import User
from django.db.models import *
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import exceptions
from rest_framework import generics, status
from rest_framework import permissions, renderers, parsers, filters
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .models import Choice, Question, QuestionSet, Room
from .serializers import ChoiceSerializers, QuestionSerializers, RoomSerializers, \
	UserSerializer, AuthTokenSerializer, QuestionSetListSerializers, QuestionSetDetailSerializers, RoomDetailSerializers


@api_view(['GET'])
@permission_classes((AllowAny,))
def api_root(request, format=None):
	return Response({
		'users': reverse('user-list', request=request, format=format),
		'room': reverse('room-list', request=request, format=format),
		'question': reverse('question-list', request=request, format=format),
		'question-set': reverse('question-set-list', request=request, format=format),
		'choice': reverse('choice-list', request=request, format=format)
	})


class ChoiceList(generics.ListAPIView):
	queryset = Choice.objects.all()
	serializer_class = ChoiceSerializers
	filter_backends = (filters.DjangoFilterBackend,)
	filter_fields = ('question',)

	permission_classes = (permissions.IsAuthenticated,)


class ChoiceDetail(generics.RetrieveUpdateDestroyAPIView):
	queryset = Choice.objects.all()
	serializer_class = ChoiceSerializers

	permission_classes = (permissions.IsAuthenticated,)


@api_view(['POST'])
def group_choice_vote(request):
	choices = request.data

	for choice in choices:
		print(choice_vote(request, choice).status_text)


	return Response(request.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST'])
def choice_vote(request, pk):
	try:
		choice = Choice.objects.get(pk=pk)
		if request.user not in choice.question.set.room.first().users.all():
			raise exceptions.ValidationError({"non_field_errors": "Not authorised to vote"})
		elif request.user in choice.users.all():
			raise exceptions.ValidationError({"user": ["Already voted."]})

		choice.users.add(request.user)
		choice.votes = F('votes') + 1
		choice.save()
		choice = Choice.objects.get(pk=pk)
		print(choice)

		serialize = ChoiceSerializers(choice, context={'request': request})
		return Response(serialize.data, status=status.HTTP_201_CREATED)

	except Choice.DoesNotExist:
		raise exceptions.NotFound({"detail": "Not found."})


class QuestionList(generics.ListAPIView):
	queryset = Question.objects.all()
	serializer_class = QuestionSerializers
	filter_backends = (filters.DjangoFilterBackend,)
	filter_fields = ('set',)

	permission_classes = (permissions.IsAuthenticated,)


class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
	queryset = Question.objects.all()
	serializer_class = QuestionSerializers

	permission_classes = (permissions.IsAuthenticated,)


class QuestionSetList(generics.ListCreateAPIView):
	queryset = QuestionSet.objects.all()
	serializer_class = QuestionSetListSerializers

	permission_classes = (permissions.IsAuthenticated,)

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)

	def list(self, request, *args, **kwargs):
		self.queryset = QuestionSet.objects.filter(owner=request.user)
		return super(QuestionSetList, self).list(self, request, *args, **kwargs)


class QuestionSetDetail(generics.RetrieveUpdateDestroyAPIView):
	queryset = QuestionSet.objects.all()
	serializer_class = QuestionSetDetailSerializers

	permission_classes = (permissions.IsAuthenticated,)


@api_view(['GET'])
def question_set_valid(request, pk):
	try:
		question_set = QuestionSet.objects.get(pk=pk)
		err_question = []

		for question in question_set.question.all():
			if question.choice.all().count() < 2:
				err_question.append(question.pk)

		if len(err_question) > 0:
			raise exceptions.ValidationError({"valid": False, "question": err_question})

		return Response({"valid": True}, status=status.HTTP_200_OK)
	except QuestionSet.DoesNotExist:
		raise exceptions.NotFound()


class CaseInsensitiveBooleanFilter(django_filters.Filter):
	def filter(self, qs, value):
		if value is not None:
			lc_value = value.lower()
			if lc_value == "true":
				value = True
			elif lc_value == "false":
				value = False
			return qs.filter(**{self.name: value})
		return qs


class RoomFilter(filters.FilterSet):
	public = CaseInsensitiveBooleanFilter(name="public", lookup_type='eq')
	destroyed = CaseInsensitiveBooleanFilter(name="destroyed", lookup_type='eq')

	class Meta:
		model = Room
		filter_fields = ['question_set', 'destroyed', 'public']


class RoomList(generics.ListCreateAPIView):
	queryset = Room.objects.all()
	filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
	filter_class = RoomFilter
	ordering = ('-created',)
	serializer_class = RoomSerializers

	permission_classes = (permissions.IsAuthenticated,)

	def list(self, request, *args, **kwargs):
		self.queryset = Room.objects.exclude(users=request.user).exclude(owner=request.user)
		return super(RoomList, self).list(self, request, *args, **kwargs)

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)


class RoomDetail(generics.RetrieveUpdateDestroyAPIView):
	queryset = Room.objects.filter()
	serializer_class = RoomDetailSerializers

	permission_classes = (permissions.IsAuthenticated,)


@api_view(['GET'])
def room_user_create(request, pk):
	try:
		room = Room.objects.get(pk=pk)
		user = request.user

		if user in room.users.all():
			return Response({"user": ["Already exists."]}, status=status.HTTP_400_BAD_REQUEST)

		room.users.add(user)

		serialize = RoomDetailSerializers(room, context={'request': request})
		return Response(serialize.data, status=status.HTTP_201_CREATED)
	except Room.DoesNotExist:
		raise exceptions.NotFound()
	except MultiValueDictKeyError:
		raise exceptions.ValidationError({"user": ["This field is required."]})


class UserList(generics.ListCreateAPIView):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = (permissions.AllowAny,)

	def create(self, request, *args, **kwargs):
		response = super(UserList, self).create(request, args, kwargs)
		auth_token = Token.objects.get(user_id=response.data['id'])
		response.data['auth_token'] = auth_token.key
		return response


class UserDetail(generics.RetrieveAPIView):
	queryset = User.objects.all()
	serializer_class = UserSerializer

	permission_classes = (permissions.IsAuthenticated,)


class ObtainAuthToken(APIView):
	throttle_classes = ()
	permission_classes = ()
	parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
	renderer_classes = (renderers.JSONRenderer,)
	serializer_class = AuthTokenSerializer

	def post(self, request, *args, **kwargs):
		serializer = self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']
		token, created = Token.objects.get_or_create(user=user)
		return Response({'auth_token': token.key,
		                 'email': user.email,
		                 'id': user.id,
		                 'first_name': user.first_name,
		                 'last_name': user.last_name,
		                 })

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from api import views

urlpatterns = [
	url(r'^$', views.api_root),

	url(r'^question-set/$', views.QuestionSetList.as_view(), name='question-set-list'),
	url(r'^question-set/(?P<pk>[0-9]+)/valid/$', views.question_set_valid, name='question-set-valid'),
	url(r'^question-set/(?P<pk>[0-9]+)/$', views.QuestionSetDetail.as_view(), name='question-set-detail'),

	url(r'^question/$', views.QuestionList.as_view(), name='question-list'),
	url(r'^question/(?P<pk>[0-9]+)/$', views.QuestionDetail.as_view(), name='question-detail'),

	url(r'^choice/$', views.ChoiceList.as_view(), name='choice-list'),
	url(r'^choice/vote/$', views.group_choice_vote, name='choice-group-vote'),
	url(r'^choice/(?P<pk>[0-9]+)/vote/$', views.choice_vote, name='choice-vote'),
	url(r'^choice/(?P<pk>[0-9]+)/$', views.ChoiceDetail.as_view(), name='choice-detail'),

	url(r'^room/$', views.RoomList.as_view(), name='room-list'),
	url(r'^room/(?P<pk>[0-9]+)/user/$', views.room_user_create, name='room-user-create'),
	url(r'^room/(?P<pk>[0-9]+)/$', views.RoomDetail.as_view(), name='room-detail'),

	url(r'^users/$', views.UserList.as_view(), name='user-list'),
	url(r'^users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view(), name='user-detail'),

	url(r'^auth-token/$', views.ObtainAuthToken.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)

from rest_framework import permissions


class IsOwnerOfSet (permissions.BasePermission):
	"""
	Custom permission to only allow owners of an object to edit it.
	"""

	def has_object_permission(self, request, view, obj):
		if request.user in request.data:
			return True

		return obj.owner == request.user

from rest_framework.permissions import BasePermission


class IsSubscriber(BasePermission):
    message = "You need to be a subscriber to perform this action"

    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Subscribers').exists():
            return True
        return False


class IsLibrarian(BasePermission):
    message = "You need to be a librarian to perform this action"

    def has_permission(self, request, view):
        if (request.user
            and request.user.groups.filter(name='Librarians').exists()
            or request.user.groups.filter(name='Managers').exists()
        ):
            return True
        return False


class IsManager(BasePermission):
    message = "You need to be a manager to perform this action"

    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Managers').exists():
            return True
        return False


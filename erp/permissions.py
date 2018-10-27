from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsManager(BasePermission):
    message = "You need to be a manager to perform this action"

    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Managers').exists():
            return True
        return False


class IsLibrarian(BasePermission):
    """
    IsLibrarian includes both librarians and managers as managers are
    librarians too. If managers happen not to run the library operations,
    this permission could evolve to only include librarians.
    In this case, we would use the OR feature of `permission_classes`
    introduced with DRF 3.9 with `|` (like django's Q queries)
    """
    message = "You need to be a librarian to perform this action."

    def has_permission(self, request, view):
        if (request.user
            and request.user.groups.filter(name='Librarians').exists()
            or request.user.groups.filter(name='Managers').exists()
        ):
            return True
        return False


class IsLibrarianOrSubscriberReadOnly(BasePermission):
    message = "You need to be a librarian (or manager) to have full access, or a subscriber to read."

    def has_permission(self, request, view):
        if ((request.method in SAFE_METHODS and request.user
             and request.user.groups.filter(name='Subscribers').exists())
            or (request.user
            and request.user.groups.filter(name='Managers').exists()
            or request.user.groups.filter(name='Librarians').exists())
        ):
            return True
        return False


class IsSubscriber(BasePermission):
    message = "You need to be a subscriber to perform this action."

    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Subscribers').exists():
            return True
        return False

from rest_framework.permissions import BasePermission

class IsInManagerGroup(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

class NotInGroups(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        group_names = ['Manager', 'Delivery crew']
        user_groups = request.user.groups.values_list('name', flat=True)
        is_in_required_groups = any(group in user_groups for group in group_names)
        return not is_in_required_groups
    
class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.groups.filter(name='Manager').exists()
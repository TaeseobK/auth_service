import django_filters
from django.contrib.auth.models import User
from .config import *

class UserFilter(BaseFilter):
    id__in = django_filters.CharFilter(field_name='id', lookup_expr='in')
    
    class Meta:
        model = User
        fields = '__all__'
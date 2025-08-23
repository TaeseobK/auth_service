from django.contrib.auth.models import User
from rest_framework import serializers

class DynamicModelSerializer(serializers.ModelSerializer):
    """
    Bisa filter 'fields' dan 'exclude' (diambil dari kwargs atau query_params).
    """
    def __init__(self, *args, **kwargs):
        # Ambil context request
        context = kwargs.get('context', {})
        request = context.get('request')

        # Ambil fields & exclude dari kwargs
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        # Kalau ada query_params, ambil dari sana
        if request:
            qp = request.query_params
            if fields is None and 'fields' in qp:
                fields = [f.strip() for f in qp.get('fields', '').split(',') if f.strip()]
            if exclude is None and 'exclude' in qp:
                exclude = [f.strip() for f in qp.get('exclude', '').split(',') if f.strip()]

        super().__init__(*args, **kwargs)

        # Filter fields
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        # Exclude fields
        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name, None)

class UserSerializer(serializers.ModelSerializer):
    raw_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = '__all__'
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get('request')
        if request and not request.user.is_superuser:
            data.pop('password', None)

        return data
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, Project, Notification, TaskTime

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'mobile', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['assigned_to'] = UserSerializer(instance.assigned_to.all(), many=True).data
        return representation

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['assigned_to'] = UserSerializer(instance.assigned_to.all(), many=True).data
        return representation

class TaskTimeSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    task_name = serializers.ReadOnlyField(source='task.task_name')

    class Meta:
        model = TaskTime
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

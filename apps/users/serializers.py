from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ─────────────────────────────────────────────────────
#  Register
# ─────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model  = User
        fields = ['email', 'nom', 'telephone', 'adresse', 'password', 'password2']

    def validate(self, data: dict) -> dict:
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
        return data

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(**validated_data)


# ─────────────────────────────────────────────────────
#  User read/update
# ─────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'email', 'nom', 'telephone',
            'adresse', 'role', 'is_verified', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['nom', 'telephone', 'adresse']


# ─────────────────────────────────────────────────────
#  JWT — custom claims
# ─────────────────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        # Custom claims inside token
        token['email'] = user.email
        token['role']  = user.role
        token['nom']   = user.nom
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        # Append user data to login response
        data['user'] = UserSerializer(self.user).data
        return data


# ─────────────────────────────────────────────────────
#  Change password
# ─────────────────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value: str) -> str:
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Mot de passe actuel incorrect.')
        return value

    def save(self) -> None:
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])


# ─────────────────────────────────────────────────────
#  Admin — list users
# ─────────────────────────────────────────────────────
class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'email', 'nom', 'telephone', 'adresse',
            'role', 'is_verified', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

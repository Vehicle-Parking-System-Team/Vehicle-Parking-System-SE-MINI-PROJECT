from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class RevocableJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication backend enforcing immediate access-token revocation on logout
    and verifying domain-level active account status.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if not user.is_active or user.status != 'active':
            raise exceptions.AuthenticationFailed(
                detail='User account is inactive or suspended.',
                code='user_inactive',
            )

        token_version = validated_token.get('token_version')
        if type(token_version) is not int or token_version != user.token_version:
            raise exceptions.AuthenticationFailed(
                detail='Token has been revoked.',
                code='token_revoked',
            )

        return user

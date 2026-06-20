from fastapi import Request


class UserContext:

    @staticmethod
    def get_user(request: Request):

        return request.session.get("user")

    @staticmethod
    def get_name(request: Request):

        user = request.session.get("user")

        if user:

            return user.get("name")

        return ""

    @staticmethod
    def get_role(request: Request):

        user = request.session.get("user")

        if user:

            return user.get("role_code")

        return ""

    @staticmethod
    def is_admin(request: Request):

        user = request.session.get("user")

        if not user:

            return False

        return user.get("role_code") == "ADMIN"
from fastapi import Request


def template_context(

    request: Request,

    **kwargs

):

    context = {

        "request": request,

        "current_user": request.session.get("user"),

        "logged_in": "user" in request.session

    }

    context.update(kwargs)

    return context
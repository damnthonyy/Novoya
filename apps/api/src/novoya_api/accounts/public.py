"""What other modules may use from accounts. Nothing else in accounts may be imported.

- current_user / CurrentUser: the signed-in user (401 if nobody is), as a CurrentUserView
- require_client, require_agent, require_admin: protect a router by role (403 otherwise);
  the admin passes all three. Use them on the router, never test user.role in a route.
- Role

Planned: get_user(user_id) -> UserView, e.g. for the quote email (#53).
"""

from novoya_api.accounts.application.dto import CurrentUserView
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.presentation.http.dependencies import (
    CurrentUser,
    current_user,
    require_admin,
    require_agent,
    require_client,
)

__all__ = [
    "CurrentUser",
    "CurrentUserView",
    "Role",
    "current_user",
    "require_admin",
    "require_agent",
    "require_client",
]

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from novoya_api.accounts.application.dto import CurrentUserView
from novoya_api.accounts.application.use_cases.change_password import ChangePassword
from novoya_api.accounts.application.use_cases.change_user_role import (
    ChangeUserRole,
    ChangeUserRoleCommand,
)
from novoya_api.accounts.application.use_cases.get_account import GetAccount
from novoya_api.accounts.application.use_cases.list_users import ListUsers
from novoya_api.accounts.application.use_cases.password_reset import (
    RequestPasswordReset,
    ResetPassword,
)
from novoya_api.accounts.application.use_cases.register import Register, RegisterCommand
from novoya_api.accounts.application.use_cases.resend_verification_email import (
    ResendVerificationEmail,
)
from novoya_api.accounts.application.use_cases.sign_in_with_password import (
    SignInWithPassword,
    SignInWithPasswordCommand,
)
from novoya_api.accounts.application.use_cases.sign_out import SignOut, SignOutEverywhere
from novoya_api.accounts.application.use_cases.verify_email import VerifyEmail
from novoya_api.accounts.domain.value_objects import UserId
from novoya_api.accounts.presentation.http.cookies import (
    clear_session_cookie,
    read_session_cookie,
    set_session_cookie,
)
from novoya_api.accounts.presentation.http.dependencies import (
    ClientDep,
    CurrentUser,
    SettingsDep,
    get_change_password,
    get_change_user_role,
    get_get_account,
    get_list_users,
    get_register,
    get_request_password_reset,
    get_resend_verification_email,
    get_reset_password,
    get_sign_in_with_password,
    get_sign_out,
    get_sign_out_everywhere,
    get_verify_email,
    require_admin,
)
from novoya_api.accounts.presentation.http.schemas import (
    ChangePasswordRequest,
    ChangeRoleRequest,
    EmailRequest,
    MeResponse,
    RegisterRequest,
    ResetPasswordRequest,
    RoleName,
    SignInRequest,
    TokenRequest,
    UserResponse,
    role_of,
)
from novoya_api.shared.presentation.http.errors import ErrorResponse

ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
}

auth_router = APIRouter(prefix="/auth", tags=["auth"], responses=ERRORS)
me_router = APIRouter(prefix="/me", tags=["me"], responses=ERRORS)
admin_users_router = APIRouter(
    prefix="/admin/users",
    tags=["admin"],
    responses=ERRORS,
    dependencies=[Depends(require_admin)],
)


@auth_router.post("/register", operation_id="register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    client: ClientDep,
    use_case: Annotated[Register, Depends(get_register)],
) -> UserResponse:
    """Create a client account. A verification link is sent by email."""
    user = await use_case(
        RegisterCommand(
            email=body.email,
            password=body.password.get_secret_value(),
            name=body.name,
            locale_hint=body.locale or request.headers.get("accept-language"),
            ip_address=client.ip_address,
        )
    )
    return UserResponse.of(user)


@auth_router.post(
    "/email/verify", operation_id="verifyEmail", status_code=status.HTTP_204_NO_CONTENT
)
async def verify_email(
    body: TokenRequest, use_case: Annotated[VerifyEmail, Depends(get_verify_email)]
) -> None:
    """Confirm the email address with the token from the verification link."""
    await use_case(body.token)


@auth_router.post(
    "/email/verify/resend",
    operation_id="resendVerificationEmail",
    status_code=status.HTTP_202_ACCEPTED,
)
async def resend_verification_email(
    body: EmailRequest,
    use_case: Annotated[ResendVerificationEmail, Depends(get_resend_verification_email)],
) -> None:
    """Send a new verification link, if the account exists and is not verified yet."""
    await use_case(body.email)


@auth_router.post(
    "/login", operation_id="signInWithPassword", status_code=status.HTTP_204_NO_CONTENT
)
async def sign_in_with_password(
    body: SignInRequest,
    response: Response,
    client: ClientDep,
    settings: SettingsDep,
    use_case: Annotated[SignInWithPassword, Depends(get_sign_in_with_password)],
) -> None:
    """Sign in with email and password. Sets the session cookie."""
    token = await use_case(
        SignInWithPasswordCommand(body.email, body.password.get_secret_value(), client)
    )
    set_session_cookie(response, token, settings)


@auth_router.post("/logout", operation_id="signOut", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    request: Request,
    response: Response,
    settings: SettingsDep,
    use_case: Annotated[SignOut, Depends(get_sign_out)],
) -> None:
    """Close the current session. Works even if it already expired."""
    token = read_session_cookie(request, settings)
    if token is not None:
        await use_case(token)
    clear_session_cookie(response, settings)


@auth_router.post(
    "/logout-all", operation_id="signOutEverywhere", status_code=status.HTTP_204_NO_CONTENT
)
async def sign_out_everywhere(
    user: CurrentUser,
    response: Response,
    settings: SettingsDep,
    use_case: Annotated[SignOutEverywhere, Depends(get_sign_out_everywhere)],
) -> None:
    """Close every session of the signed-in user, on every device."""
    await use_case(user.user_id)
    clear_session_cookie(response, settings)


@auth_router.post(
    "/password/forgot", operation_id="forgotPassword", status_code=status.HTTP_202_ACCEPTED
)
async def forgot_password(
    body: EmailRequest,
    use_case: Annotated[RequestPasswordReset, Depends(get_request_password_reset)],
) -> None:
    """Send a reset link, if the account exists. The answer is the same either way."""
    await use_case(body.email)


@auth_router.post(
    "/password/reset", operation_id="resetPassword", status_code=status.HTTP_204_NO_CONTENT
)
async def reset_password(
    body: ResetPasswordRequest,
    use_case: Annotated[ResetPassword, Depends(get_reset_password)],
) -> None:
    """Set a new password with the token from the reset link. Every session is closed."""
    await use_case(body.token, body.new_password.get_secret_value())


@auth_router.post(
    "/password/change", operation_id="changePassword", status_code=status.HTTP_204_NO_CONTENT
)
async def change_password(
    body: ChangePasswordRequest,
    user: CurrentUser,
    use_case: Annotated[ChangePassword, Depends(get_change_password)],
) -> None:
    """Change the password of the signed-in user. Their other sessions are closed."""
    await use_case(
        user, body.current_password.get_secret_value(), body.new_password.get_secret_value()
    )


@me_router.get("", operation_id="getMe")
async def get_me(
    user: CurrentUser, use_case: Annotated[GetAccount, Depends(get_get_account)]
) -> MeResponse:
    """The signed-in user, with their role. The web app shows its menus from the role."""
    return MeResponse.of_account(await use_case(user.user_id))


@admin_users_router.get("", operation_id="listUsers")
async def list_users(
    use_case: Annotated[ListUsers, Depends(get_list_users)],
    q: Annotated[str | None, Query(max_length=254, description="Part of an email or name")] = None,
    role: RoleName | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserResponse]:
    """The users, newest first. Admin only."""
    users = await use_case(q, role_of(role), limit, offset)
    return [UserResponse.of(user) for user in users]


@admin_users_router.get("/{user_id}", operation_id="getUser")
async def get_user(
    user_id: UUID, use_case: Annotated[GetAccount, Depends(get_get_account)]
) -> MeResponse:
    """One user. Admin only."""
    return MeResponse.of_account(await use_case(UserId(user_id)))


@admin_users_router.patch("/{user_id}/role", operation_id="changeUserRole")
async def change_user_role(
    user_id: UUID,
    body: ChangeRoleRequest,
    admin: Annotated[CurrentUserView, Depends(require_admin)],
    use_case: Annotated[ChangeUserRole, Depends(get_change_user_role)],
) -> UserResponse:
    """Give a user another role. Admin only, never on their own account. The change is logged."""
    user = await use_case(
        ChangeUserRoleCommand(UserId(user_id), role_of(body.role), changed_by=admin.user_id)
    )
    return UserResponse.of(user)


router = APIRouter()
router.include_router(auth_router)
router.include_router(me_router)
router.include_router(admin_users_router)

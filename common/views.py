# integrations/views.py
import requests
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from ..assets.models import Organization, SlackWorkspace

SLACK_OAUTH_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_OAUTH_ACCESS_URL = "https://slack.com/api/oauth.v2.access"

def slack_install(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    client_id = settings.SLACK_CLIENT_ID
    scopes = "chat:write,channels:manage,users:read,users:read.email,conversations:write"
    redirect_uri = request.build_absolute_uri("/integrations/slack/oauth/callback/")
    state = f"{org.id}:{request.user.id}"  # include CSRF-like state
    auth_url = f"{SLACK_OAUTH_AUTHORIZE_URL}?client_id={client_id}&scope={scopes}&redirect_uri={redirect_uri}&state={state}"
    return redirect(auth_url)


def slack_oauth_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")  # e.g. "orgid:userid"
    redirect_uri = request.build_absolute_uri("/integrations/slack/oauth/callback/")
    if not code:
        return HttpResponse("Missing code", status=400)

    resp = requests.post(SLACK_OAUTH_ACCESS_URL, data={
        "client_id": settings.SLACK_CLIENT_ID,
        "client_secret": settings.SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
    }).json()

    if not resp.get("ok"):
        # log error
        return HttpResponse(f"Slack OAuth failed: {resp.get('error')}", status=400)

    # Extract team info and bot token
    team = resp.get("team", {})
    team_id = team.get("id")
    team_name = team.get("name")
    bot_token = resp.get("access_token") or resp.get("authed_user", {}).get("access_token")  # v2 returns 'access_token' for bot

    # Map state to organization
    org_id = None
    try:
        if state:
            org_id = int(state.split(":")[0])
    except Exception:
        pass

    if not org_id:
        return HttpResponse("Invalid state", status=400)

    org = get_object_or_404(Organization, id=org_id)

    # Save or update SlackWorkspace
    SLackWs, created = SlackWorkspace.objects.update_or_create(
        slack_team_id=team_id,
        defaults={
            "organization": org,
            "slack_team_name": team_name,
            "bot_access_token": bot_token,
            "active": True,
        }
    )

    # Optionally ensure superuser channel now (async)
    from .tasks import async_ensure_superuser_channel_for_workspace
    async_ensure_superuser_channel_for_workspace.delay(SLackWs.id)

    return JsonResponse({"ok": True, "team": team_name})

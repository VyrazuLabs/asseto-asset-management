# integrations/slack_utils.py
import requests
from django.conf import settings
from .models import SlackWorkspace, SlackIntegration

SLACK_API_BASE = "https://slack.com/api"

def headers(token):
    return {"Authorization": f"Bearer {token}"}

def create_channel_if_not_exists(workspace: SlackWorkspace, channel_name: str, is_private=True):
    """
    Ensure a channel exists in the workspace; return channel_id.
    """
    token = workspace.bot_access_token
    # Try to create
    resp = requests.post(f"{SLACK_API_BASE}/conversations.create", headers=headers(token), data={
        "name": channel_name,
        "is_private": "true" if is_private else "false"
    }).json()

    if resp.get("ok"):
        return resp["channel"]["id"]

    # if name_taken, list and find it
    err = resp.get("error", "")
    if err == "name_taken" or "already_in_channel" in err:
        lst = requests.get(f"{SLACK_API_BASE}/conversations.list", headers=headers(token), params={"limit": 1000}).json()
        for ch in lst.get("channels", []):
            if ch.get("name") == channel_name:
                return ch.get("id")
    # else raise/log
    raise Exception(f"Failed to ensure channel {channel_name}: {resp}")


def invite_user_by_email(workspace: SlackWorkspace, user_email: str, channel_id: str):
    token = workspace.bot_access_token
    # lookup user
    resp = requests.get(f"{SLACK_API_BASE}/users.lookupByEmail", headers=headers(token), params={"email": user_email}).json()
    if not resp.get("ok"):
        # can't find user; may need workspace admin to invite manually
        return {"ok": False, "error": resp.get("error")}
    slack_user_id = resp["user"]["id"]

    invite = requests.post(f"{SLACK_API_BASE}/conversations.invite", headers=headers(token), data={
        "channel": channel_id,
        "users": slack_user_id
    }).json()
    return invite


def post_message(workspace: SlackWorkspace, channel_id: str, text: str, blocks=None):
    token = workspace.bot_access_token
    payload = {"channel": channel_id, "text": text}
    if blocks:
        payload["blocks"] = blocks
    return requests.post(f"{SLACK_API_BASE}/chat.postMessage", headers=headers(token), json=payload).json()

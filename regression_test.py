"""C2C passive-reply correlation must not force a visible quote card."""
import json
import time

import httpx
import pytest

from gateway.config import PlatformConfig
from gateway.platforms.qqbot.adapter import QQAdapter


@pytest.mark.asyncio
@pytest.mark.parametrize('markdown', [False, True])
@pytest.mark.parametrize('chat_type', ['c2c', 'group'])
async def test_passive_reply_keeps_correlation_without_c2c_quote(markdown, chat_type):
    requests = []

    def receive(request):
        requests.append(request)
        return httpx.Response(200, json={'id': 'synthetic-sent-id'})

    adapter = QQAdapter(PlatformConfig(enabled=True, extra={
        'app_id': 'synthetic-app', 'client_secret': 'synthetic-secret',
        'markdown_support': markdown,
    }))
    adapter._access_token = 'synthetic-token'
    adapter._token_expires_at = time.time() + 3600
    text = 'Visible reply without a quote'
    async with httpx.AsyncClient(transport=httpx.MockTransport(receive)) as client:
        adapter._http_client = client
        sender = adapter._send_c2c_text if chat_type == 'c2c' else adapter._send_group_text
        result = await sender('synthetic-recipient', text, 'synthetic-inbound-id')

    assert result.success
    assert len(requests) == 1
    request = requests[0]
    kind = 'users' if chat_type == 'c2c' else 'groups'
    assert request.url.path == f'/v2/{kind}/synthetic-recipient/messages'
    payload = json.loads(request.content)
    assert payload['msg_id'] == 'synthetic-inbound-id'
    assert isinstance(payload['msg_seq'], int)
    if markdown:
        assert payload['msg_type'] == 2
        assert payload['markdown']['content'] == text
    else:
        assert payload['msg_type'] == 0
        assert payload['content'] == text
    if chat_type == 'c2c' or markdown:
        assert 'message_reference' not in payload
    else:
        assert payload['message_reference']['message_id'] == payload['msg_id']

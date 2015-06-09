import pytest
import json
from tests.util.base import (api_client, add_fake_message, default_namespace,
                             new_message_from_synced, mime_message, thread)

__all__ = ['api_client', 'default_namespace']


@pytest.fixture
def stub_message_from_raw(db, thread, new_message_from_synced):
    new_msg = new_message_from_synced
    new_msg.thread = thread
    db.session.add(new_msg)
    db.session.commit()
    return new_msg


# TODO(emfree) clean up fixture dependencies
def test_rfc822_format(stub_message_from_raw, api_client, mime_message):
    """ Test the API response to retreive raw message contents """
    full_path = api_client.full_path('/messages/{}'.format(
        stub_message_from_raw.public_id))

    results = api_client.client.get(full_path,
                                    headers={'Accept': 'message/rfc822'})
    assert results.data == mime_message.to_string()


@pytest.fixture
def stub_message(db, new_message_from_synced, default_namespace, thread):
    message = add_fake_message(db.session, default_namespace.id, thread,
                               subject="Golden Gate Park next Sat",
                               from_addr=[('alice', 'alice@example.com')],
                               to_addr=[('bob', 'bob@example.com')])
    message.snippet = 'Banh mi paleo pickled, sriracha'
    message.body = """
Banh mi paleo pickled, sriracha biodiesel chambray seitan
mumblecore mustache. Raw denim gastropub 8-bit, butcher
PBR sartorial photo booth Pinterest blog Portland roof party
cliche bitters aesthetic. Ugh.
"""

    message = add_fake_message(db.session, default_namespace.id, thread,
                               subject="Re:Golden Gate Park next Sat",
                               from_addr=[('bob', 'bob@example.com')],
                               to_addr=[('alice', 'alice@example.com')],
                               cc_addr=[('Cheryl', 'cheryl@gmail.com')])
    message.snippet = 'Bushwick meggings ethical keffiyeh'
    message.body = """
Bushwick meggings ethical keffiyeh. Chambray lumbersexual wayfarers,
irony Banksy cred bicycle rights scenester artisan tote bag YOLO gastropub.
"""

    draft = add_fake_message(db.session, default_namespace.id, thread,
                             subject="Re:Golden Gate Park next Sat",
                             from_addr=[('alice', 'alice@example.com')],
                             to_addr=[('bob', 'bob@example.com')],
                             cc_addr=[('Cheryl', 'cheryl@gmail.com')])
    draft.snippet = 'Hey there friend writing a draft'
    draft.body = """
DIY tousled Tumblr, VHS meditation 3 wolf moon listicle fingerstache viral
bicycle rights. Thundercats kale chips church-key American Apparel.
"""
    draft.is_draft = True
    draft.reply_to_message = message

    db.session.commit()
    return message


def test_sender_and_participants(stub_message, api_client):
    resp = api_client.client.get(api_client.full_path(
        '/threads/{}'.format(stub_message.thread.public_id)))
    assert resp.status_code == 200
    resp_dict = json.loads(resp.data)
    participants = resp_dict['participants']
    assert len(participants) == 3

    # Not expanded, should only return IDs
    assert 'message' not in resp_dict
    assert 'drafts' not in resp_dict


def test_expanded_threads(stub_message, api_client):
    def _check_json_thread(resp_dict):
        assert 'message_ids' not in resp_dict
        assert 'messages' in resp_dict
        assert 'drafts' in resp_dict
        assert len(resp_dict['participants']) == 3
        assert len(resp_dict['messages']) == 2
        assert len(resp_dict['drafts']) == 1

        for msg_dict in resp_dict['messages']:
            assert 'body' not in msg_dict
            assert msg_dict['object'] == 'message'
            assert msg_dict['thread_id'] == stub_message.thread.public_id
            valid_keys = ['namespace_id', 'to', 'from', 'files', 'unread',
                          'unread', 'date', 'snippet']
            assert all(x in msg_dict for x in valid_keys)

        for draft in resp_dict['drafts']:
            assert 'body' not in draft
            assert draft['object'] == 'draft'
            assert draft['thread_id'] == stub_message.thread.public_id
            valid_keys = ['namespace_id', 'to', 'from', 'files', 'unread',
                          'snippet', 'date', 'version', 'reply_to_message_id']
            assert all(x in draft for x in valid_keys)

    # /threads/<thread_id>
    resp = api_client.client.get(api_client.full_path(
        '/threads/{}?view=expanded'.format(stub_message.thread.public_id)))
    assert resp.status_code == 200
    resp_dict = json.loads(resp.data)
    _check_json_thread(resp_dict)

    # /threads/
    resp = api_client.client.get(api_client.full_path(
        '/threads/?view=expanded'.format(stub_message.thread.public_id)))
    assert resp.status_code == 200
    resp_dict = json.loads(resp.data)

    for thread_json in resp_dict:
        if thread_json['id'] == stub_message.thread.public_id:
            _check_json_thread(thread_json)

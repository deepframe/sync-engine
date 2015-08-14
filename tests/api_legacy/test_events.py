import json
import pytest

from inbox.sqlalchemy_ext.util import generate_public_id
from inbox.models import Event
from tests.util.base import db, calendar, add_fake_event
from tests.api_legacy.base import api_client

__all__ = ['api_client', 'calendar', 'db']


def test_create_event(db, api_client, calendar):
    e_data = {'title': 'subj', 'description': 'body1',
              'calendar_id': calendar.public_id,
              'when': {'time': 1}, 'location': 'InboxHQ'}
    e_data2 = {'title': 'subj2', 'description': 'body2',
               'calendar_id': calendar.public_id,
               'when': {'time': 1}, 'location': 'InboxHQ'}
    api_client.post_data('/events', e_data)
    api_client.post_data('/events', e_data2)
    db.session.commit()


def test_api_list(db, api_client, calendar):
    e_data = {'title': 'subj', 'description': 'body1',
              'calendar_id': calendar.public_id,
              'when': {'time': 1}, 'location': 'InboxHQ'}
    e_data2 = {'title': 'subj2', 'description': 'body2',
               'calendar_id': calendar.public_id,
               'when': {'time': 1}, 'location': 'InboxHQ'}
    api_client.post_data('/events', e_data)
    api_client.post_data('/events', e_data2)

    event_list = api_client.get_data('/events')
    event_titles = [event['title'] for event in event_list]
    assert 'subj' in event_titles
    assert 'subj2' in event_titles

    event_descriptions = [event['description'] for event in event_list]
    assert 'body1' in event_descriptions
    assert 'body2' in event_descriptions

    event_ids = [event['id'] for event in event_list]

    for e_id in event_ids:
        ev = db.session.query(Event).filter_by(public_id=e_id).one()
        db.session.delete(ev)
    db.session.commit()


def test_api_get(db, api_client, calendar):
    e_data = {'title': 'subj', 'when': {'time': 1},
              'calendar_id': calendar.public_id, 'location': 'InboxHQ'}
    e_data2 = {'title': 'subj2', 'when': {'time': 1},
               'calendar_id': calendar.public_id, 'location': 'InboxHQ'}
    api_client.post_data('/events', e_data)
    api_client.post_data('/events', e_data2)

    event_list = api_client.get_data('/events')

    event_ids = [event['id'] for event in event_list]

    c1found = False
    c2found = False
    for c_id in event_ids:
        event = api_client.get_data('/events/' + c_id)

        if event['title'] == 'subj':
            c1found = True

        if event['title'] == 'subj2':
            c2found = True

    assert c1found
    assert c2found


def test_api_create(db, api_client, calendar, default_account):
    e_data = {
        'title': 'Friday Office Party',
        'calendar_id': calendar.public_id,
        'when': {'time': 1407542195},
        'location': 'Inbox HQ',
    }

    e_resp = api_client.post_data('/events', e_data)
    e_resp_data = json.loads(e_resp.data)
    assert e_resp_data['object'] == 'event'
    assert e_resp_data['namespace_id'] == default_account.namespace.public_id
    assert e_resp_data['title'] == e_data['title']
    assert e_resp_data['location'] == e_data['location']
    assert e_resp_data['when']['time'] == e_data['when']['time']
    assert 'id' in e_resp_data
    e_id = e_resp_data['id']
    e_get_resp = api_client.get_data('/events/' + e_id)

    assert e_get_resp['object'] == 'event'
    assert e_get_resp['namespace_id'] == default_account.namespace.public_id
    assert e_get_resp['id'] == e_id
    assert e_get_resp['title'] == e_data['title']
    assert e_get_resp['when']['time'] == e_data['when']['time']


def test_api_create_no_title(db, api_client, calendar, default_account):
    e_data = {
        'title': '',
        'calendar_id': calendar.public_id,
        'when': {'time': 1407542195},
    }

    e_resp = api_client.post_data('/events', e_data)
    e_resp_data = json.loads(e_resp.data)
    assert e_resp_data['object'] == 'event'
    assert e_resp_data['namespace_id'] == default_account.namespace.public_id
    assert e_resp_data['title'] == e_data['title']
    assert e_resp_data['when']['time'] == e_data['when']['time']
    assert 'id' in e_resp_data
    e_id = e_resp_data['id']
    e_get_resp = api_client.get_data('/events/' + e_id)

    assert e_get_resp['object'] == 'event'
    assert e_get_resp['namespace_id'] == default_account.namespace.public_id
    assert e_get_resp['id'] == e_id
    assert e_get_resp['title'] == e_data['title']
    assert e_get_resp['when']['time'] == e_data['when']['time']


def test_api_update_title(db, api_client, calendar, default_account):
    e_data = {
        'title': '',
        'calendar_id': calendar.public_id,
        'when': {'time': 1407542195},
    }

    e_resp = api_client.post_data('/events', e_data)
    e_resp_data = json.loads(e_resp.data)
    assert e_resp_data['object'] == 'event'
    assert e_resp_data['namespace_id'] == default_account.namespace.public_id
    assert e_resp_data['title'] == e_data['title']
    assert e_resp_data['when']['time'] == e_data['when']['time']
    assert 'id' in e_resp_data
    e_id = e_resp_data['id']

    e_update_data = {'title': 'new title'}
    e_put_resp = api_client.put_data('/events/' + e_id, e_update_data)
    e_put_data = json.loads(e_put_resp.data)

    assert e_put_data['object'] == 'event'
    assert e_put_data['namespace_id'] == default_account.namespace.public_id
    assert e_put_data['id'] == e_id
    assert e_put_data['title'] == 'new title'
    assert e_put_data['when']['object'] == 'time'
    assert e_put_data['when']['time'] == e_data['when']['time']


def test_api_update_invalid(db, api_client, calendar):
    e_update_data = {'title': 'new title'}
    e_id = generate_public_id()
    e_put_resp = api_client.put_data('/events/' + e_id, e_update_data)
    assert e_put_resp.status_code != 200


def test_api_delete(db, api_client, calendar, default_account):
    e_data = {
        'title': '',
        'calendar_id': calendar.public_id,
        'when': {'time': 1407542195},
    }

    e_resp = api_client.post_data('/events', e_data)
    e_resp_data = json.loads(e_resp.data)
    assert e_resp_data['object'] == 'event'
    assert e_resp_data['title'] == e_data['title']
    assert e_resp_data['when']['time'] == e_data['when']['time']
    assert 'id' in e_resp_data
    e_id = e_resp_data['id']

    e_delete_resp = api_client.delete('/events/' + e_id)
    assert e_delete_resp.status_code == 200

    e_resp = api_client.get_data('/events/' + e_id)
    assert e_resp['status'] == 'cancelled'


def test_api_delete_invalid(db, api_client, calendar):
    e_id = 'asdf'
    resp = api_client.delete('/events/' + e_id)
    assert resp.status_code != 200

    e_id = generate_public_id()
    resp = api_client.delete('/events/' + e_id)
    assert resp.status_code != 200


def test_api_update_read_only(db, api_client, calendar, default_namespace):
    add_fake_event(db.session, default_namespace.id,
                   calendar=calendar,
                   read_only=True)
    event_list = api_client.get_data('/events')

    read_only_event = None
    for e in event_list:
        if e['read_only']:
            read_only_event = e
            break

    assert read_only_event

    e_id = read_only_event['id']
    e_update_data = {'title': 'new title'}
    e_put_resp = api_client.put_data('/events/' + e_id, e_update_data)
    assert e_put_resp.status_code != 200


# TODO(emfree) setup expected test data
@pytest.mark.xfail
def test_api_filter(db, api_client, calendar):
    # Events in database:
    # description: data1
    # read_only: True
    # namespace_id: 3q4vzllntcsea53vxz4erbnxr
    # object: event
    # when: {u'start_time': 1, u'object': u'timespan', u'end_time':
    #        2678401}
    # participants: []
    # location: InboxHeadquarters
    # calendar_id: 167wjlgf89za2cdhy17p9bsu8
    # id: 6n5fi3kwousrq3m6wl89tidx9
    # title: desc1

    # description: data2
    # read_only: True
    # namespace_id: 3q4vzllntcsea53vxz4erbnxr
    # object: event
    # when: {u'object': u'time', u'time': 1}
    # participants: []
    # location: InboxHeadquarters
    # calendar_id: 167wjlgf89za2bz6fytbzn0zk
    # id: crezzdqaizqv2gt7uomkzu9l6
    # title: desc2

    # description: data3
    # read_only: False
    # namespace_id: 3q4vzllntcsea53vxz4erbnxr
    # object: event
    # when: {u'start_time': 2678401, u'object': u'timespan',
    #        u'end_time': 5097601}
    # participants: []
    # location: InboxHeadquarters
    # calendar_id: 167wjlgf89za2cdhy17p9bsu8
    # id: crezzdqaizqv2gk4tabx3ddze
    # title: desc5

    events = api_client.get_data('/events?offset=%s' % '1')
    assert len(events) == 2

    events = api_client.get_data('/events?limit=%s' % '1')
    assert len(events) == 1

    events = api_client.get_data('/events?description=%s' % 'data')
    assert len(events) == 3

    events = api_client.get_data('/events?description=%s' % 'data1')
    assert len(events) == 1

    events = api_client.get_data('/events?description=%s' % 'bad')
    assert len(events) == 0

    events = api_client.get_data('/events?title=%s' % 'desc')
    assert len(events) == 3

    events = api_client.get_data('/events?title=%s' % 'desc5')
    assert len(events) == 1

    events = api_client.get_data('/events?title=%s' % 'bad')
    assert len(events) == 0

    events = api_client.get_data('/events?location=%s' % 'Inbox')
    assert len(events) == 3

    events = api_client.get_data('/events?location=%s' % 'bad')
    assert len(events) == 0

    _filter = 'event_id=%s' % 'crezzdqaizqv2gk4tabx3ddze'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 1

    _filter = 'starts_before=2'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 2

    _filter = 'starts_after=2'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 1

    _filter = 'ends_before=2700000'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 2

    _filter = 'ends_after=2700000'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 1

    _filter = 'calendar_id=167wjlgf89za2cdhy17p9bsu8'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 2

    _filter = 'calendar_id=0000000000000000000000000'
    events = api_client.get_data('/events?' + _filter)
    assert len(events) == 0

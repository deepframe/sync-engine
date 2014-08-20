from tests.util.base import config

# Need to set up test config before we can import from
# inbox.models.tables.
config()
from inbox.models import Event, Participant

ACCOUNT_ID = 1

# STOPSHIP(emfree): Test multiple distinct remote providers


def _default_event():
    return Event(account_id=ACCOUNT_ID,
                 subject='subject',
                 body='',
                 location='',
                 busy=False,
                 locked=False,
                 reminders='',
                 recurrence='',
                 start=0,
                 end=1,
                 all_day=False,
                 time_zone=0,
                 source='remote')


def test_add_participant(config):
    """Test the basic logic of the merge() function."""
    base = _default_event()
    participant = Participant(email_address="foo@example.com")
    remote = Event(account_id=ACCOUNT_ID,
                   subject='new subject',
                   body='new body',
                   location='new location',
                   busy=True,
                   locked=True,
                   reminders='',
                   recurrence='',
                   start=2,
                   end=3,
                   all_day=False,
                   time_zone=0,
                   source='remote',
                   participants=[participant])

    dest = _default_event()

    dest.merge_from(base, remote)
    assert len(dest.participants) == 1


def test_update_participant_status(config):
    """Test the basic logic of the merge() function."""
    base = _default_event()
    base.participants = [Participant(email_address="foo@example.com")]

    dest = _default_event()
    dest.participants = [Participant(email_address="foo@example.com")]

    participant1 = Participant(email_address="foo@example.com",
                               status="yes")
    remote = Event(account_id=ACCOUNT_ID,
                   subject='new subject',
                   body='new body',
                   location='new location',
                   busy=True,
                   locked=True,
                   reminders='',
                   recurrence='',
                   start=2,
                   end=3,
                   all_day=False,
                   time_zone=0,
                   source='remote',
                   participants=[participant1])

    dest.merge_from(base, remote)
    assert len(dest.participants) == 1
    assert dest.participants[0].status == 'yes'


def test_update_participant_status2(config):
    """Test the basic logic of the merge() function."""
    base = _default_event()
    base.participants = [Participant(email_address="foo@example.com",
                                     status="no")]

    dest = _default_event()
    dest.participants = [Participant(email_address="foo@example.com",
                                     status="no")]

    participant1 = Participant(email_address="foo@example.com",
                               status="yes")
    remote = Event(account_id=ACCOUNT_ID,
                   subject='new subject',
                   body='new body',
                   location='new location',
                   busy=True,
                   locked=True,
                   reminders='',
                   recurrence='',
                   start=2,
                   end=3,
                   all_day=False,
                   time_zone=0,
                   source='remote',
                   participants=[participant1])

    dest.merge_from(base, remote)
    assert len(dest.participants) == 1
    assert dest.participants[0].status == 'yes'


def test_multi_update(config):
    """Test the basic logic of the merge() function."""
    base = _default_event()
    base.participants = [Participant(email_address="foo@example.com",
                                     status="no")]

    dest = _default_event()
    dest.participants = [Participant(email_address="foo@example.com",
                                     status="no"),
                         Participant(email_address="foo2@example.com",
                                     status="no")]

    participant1 = Participant(email_address="foo@example.com",
                               status="yes")
    remote = Event(account_id=ACCOUNT_ID,
                   subject='new subject',
                   body='new body',
                   location='new location',
                   busy=True,
                   locked=True,
                   reminders='',
                   recurrence='',
                   start=2,
                   end=3,
                   all_day=False,
                   time_zone=0,
                   source='remote',
                   participants=[participant1])

    dest.merge_from(base, remote)
    assert len(dest.participants) == 2
    for p in dest.participants:
        if p.email_address == "foo@example.com":
            assert p.status == "yes"
        if p.email_address == "foo2@example.com":
            assert p.status == "no"

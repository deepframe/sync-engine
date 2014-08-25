from datetime import datetime
from icalendar import Calendar

from inbox.models import Event, Participant
from inbox.events.util import MalformedEventError


def events_from_ics(namespace, calendar, ics_str):
    try:
        cal = Calendar.from_ical(ics_str)
    except ValueError:
        raise MalformedEventError()

    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            start = component.get('dtstart').dt
            end = component.get('dtend').dt
            subject = component.get('summary')
            body = str(component.get('description'))
            if isinstance(start, datetime):
                all_day = False
            else:
                all_day = True
                start = datetime.combine(start, datetime.min.time())
                end = datetime.combine(end, datetime.min.time())

            reccur = component.get('rrule')
            if reccur:
                reccur = reccur.to_ical()
            else:
                reccur = ''
            participants = []
            for attendee in component.get('attendee'):
                email = str(attendee)
                # strip mailto: if it exists
                if email.startswith('mailto:'):
                    email = email[7:]
                try:
                    name = attendee.params['CN']
                except KeyError:
                    name = None

                status_map = {'NEEDS-ACTION': 'noreply',
                              'ACCEPTED': 'yes',
                              'DECLINED': 'no',
                              'TENTATIVE': 'maybe'}
                status = 'noreply'
                try:
                    a_status = attendee.params['PARTSTAT']
                    status = status_map[a_status]
                except KeyError:
                    pass

                notes = None
                try:
                    guests = attendee.params['X-NUM-GUESTS']
                    notes = "Guests: {}".format(guests)
                except KeyError:
                    pass

                participant = Participant(email_address=email,
                                          status=status,
                                          name=name,
                                          notes=notes)

                participants.append(participant)
            location = component.get('location')
            organizer = component.get('organizer')
            if(organizer):
                organizer = str(organizer)
                if organizer.startswith('mailto:'):
                    organizer = organizer[7:]

            uid = str(component.get('uid'))
            event = Event(
                account_id=namespace.account_id,
                calendar=calendar,
                uid=uid,
                provider_name='ics',
                raw_data=component.to_ical(),
                subject=subject,
                body=body,
                location=location,
                reminders=str([]),
                recurrence=reccur,
                start=start,
                end=end,
                busy=True,
                all_day=all_day,
                read_only=True,
                source='local')

            event.participants = participants
            events.append(event)
    return events

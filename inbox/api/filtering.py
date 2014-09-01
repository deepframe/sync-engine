from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import joinedload, subqueryload
from inbox.models import (Contact, Event, Calendar, Message,
                          MessageContactAssociation, Thread, Tag,
                          TagItem, Part)


def threads(namespace_id, subject, from_addr, to_addr, cc_addr, bcc_addr,
            any_email, thread_public_id, started_before, started_after,
            last_message_before, last_message_after, filename, tag, limit,
            offset, db_session):
    query = db_session.query(Thread)
    thread_criteria = [Thread.namespace_id == namespace_id]
    if thread_public_id is not None:
        query = query.filter(Thread.public_id == thread_public_id)
        # TODO(emfree): at this point there should be at most one object,
        # so we could just execute the query and check additional filters
        # in Python-land.

    if started_before is not None:
        thread_criteria.append(Thread.subjectdate < started_before)

    if started_after is not None:
        thread_criteria.append(Thread.subjectdate > started_after)

    if last_message_before is not None:
        thread_criteria.append(Thread.recentdate <
                               last_message_before)

    if last_message_after is not None:
        thread_criteria.append(Thread.recentdate > last_message_after)

    if subject is not None:
        thread_criteria.append(Thread.subject == subject)

    thread_predicate = and_(*thread_criteria)
    query = query.filter(thread_predicate)

    if tag is not None:
        tag_query = db_session.query(TagItem).join(Tag). \
            filter(or_(Tag.public_id == tag, Tag.name == tag),
                   Tag.namespace_id == namespace_id).subquery()

        query = query.join(tag_query)

    if any((from_addr, to_addr, cc_addr, bcc_addr)):
        contact_criteria = []
        if from_addr is not None:
            contact_criteria.append(and_(
                Contact.email_address == from_addr,
                MessageContactAssociation.field == 'from_addr'))

        if to_addr is not None:
            contact_criteria.append(and_(
                Contact.email_address == to_addr,
                MessageContactAssociation.field == 'to_addr'))

        if cc_addr is not None:
            contact_criteria.append(and_(
                Contact.email_address == cc_addr,
                MessageContactAssociation.field == 'cc_addr'))

        if bcc_addr is not None:
            contact_criteria.append(and_(
                Contact.email_address == bcc_addr,
                MessageContactAssociation.field == 'bcc_addr'))

        contact_query = db_session.query(Message). \
            join(MessageContactAssociation).join(Contact). \
            filter(or_(*contact_criteria)).subquery()

        query = query.join(contact_query)

    if any_email is not None:
        any_contact_query = db_session.query(Message). \
            join(MessageContactAssociation).join(Contact). \
            filter(Contact.email_address == any_email).subquery()
        query = query.join(any_contact_query)

    if filename is not None:
        files_query = db_session.query(Message). \
            join(Part).filter(Part.filename == filename).subquery()
        query = query.join(files_query)

    # Eager-load some objects in order to make constructing API
    # representations faster.
    query = query.options(
        subqueryload(Thread.messages).
        load_only('public_id', 'is_draft', 'from_addr', 'to_addr',
                  'cc_addr', 'bcc_addr'),
        subqueryload('tagitems').joinedload('tag').
        load_only('public_id', 'name'))

    query = query.order_by(desc(Thread.recentdate)).distinct().limit(limit)
    if offset:
        query = query.offset(offset)
    return query.all()


def messages(namespace_id, subject, from_addr, to_addr, cc_addr, bcc_addr,
             any_email, thread_public_id, started_before, started_after,
             last_message_before, last_message_after, filename, tag, limit,
             offset, db_session):
    query = db_session.query(Message). \
        filter(~Message.is_draft)

    thread_criteria = [Thread.namespace_id == namespace_id]

    if thread_public_id is not None:
        # TODO(emfree) this is a common case that we should handle
        # separately by just fetching the thread's messages and only
        # filtering more if needed.
        thread_criteria.append(Thread.public_id == thread_public_id)

    if started_before is not None:
        thread_criteria.append(Thread.subjectdate < started_before)

    if started_after is not None:
        thread_criteria.append(Thread.subjectdate > started_after)

    if last_message_before is not None:
        thread_criteria.append(Thread.recentdate <
                               last_message_before)

    if last_message_after is not None:
        thread_criteria.append(Thread.recentdate > last_message_after)

    thread_predicate = and_(*thread_criteria)
    thread_query = db_session.query(Thread).filter(thread_predicate)
    if tag is not None:
        thread_query = thread_query.join(TagItem).join(Tag). \
            filter(or_(Tag.public_id == tag, Tag.name == tag),
                   Tag.namespace_id == namespace_id)
    thread_query = thread_query.subquery()

    query = query.join(thread_query)

    if subject is not None:
        query = query.filter(Message.subject == subject)

    if to_addr is not None:
        to_query = db_session.query(Message). \
            join(MessageContactAssociation).join(Contact). \
            filter(MessageContactAssociation.field == 'to_addr',
                   Contact.email_address == to_addr).subquery()
        query = query.join(to_query)

    if from_addr is not None:
        from_query = db_session.query(MessageContactAssociation). \
            join(Contact).filter(
                MessageContactAssociation.field == 'from_addr',
                Contact.email_address == from_addr).subquery()
        query = query.join(from_query)

    if cc_addr is not None:
        cc_query = db_session.query(MessageContactAssociation). \
            join(Contact).filter(
                MessageContactAssociation.field == 'cc_addr',
                Contact.email_address == cc_addr).subquery()
        query = query.join(cc_query)

    if bcc_addr is not None:
        bcc_query = db_session.query(MessageContactAssociation). \
            join(Contact).filter(
                MessageContactAssociation.field == 'bcc_addr',
                Contact.email_address == bcc_addr).subquery()
        query = query.join(bcc_query)

    if any_email is not None:
        any_email_query = db_session.query(
            MessageContactAssociation).join(Contact). \
            filter(Contact.email_address == any_email).subquery()
        query = query.join(any_email_query)

    if filename is not None:
        file_query = db_session.query(Part). \
            filter(Part.filename == filename).subquery()
        query = query.join(file_query)

    # Eager-load some objects in order to make constructing API
    # representations faster.
    query = query.options(
        joinedload(Message.parts).load_only('public_id',
                                            'content_disposition'),
        joinedload(Message.thread).load_only('public_id', 'discriminator'))

    # TODO(emfree) we should really eager-load the namespace too
    # (or just directly store it on the message object)

    query = query.order_by(desc(Message.received_date)).distinct().limit(limit)
    if offset:
        query = query.offset(offset)

    return query.all()


def drafts(namespace_id, thread_public_id, limit, offset, db_session):
    query = db_session.query(Message).filter(Message.is_draft)

    thread_criteria = [Thread.namespace_id == namespace_id]

    if thread_public_id is not None:
        # TODO(emfree) this is a common case that we should handle
        # separately by just fetching the thread's messages and only
        # filtering more if needed.
        thread_criteria.append(Thread.public_id == thread_public_id)

    thread_predicate = and_(*thread_criteria)
    thread_query = db_session.query(Thread).filter(thread_predicate)

    query = query.join(thread_query.subquery())

    # Eager-load some objects in order to make constructing API
    # representations faster.
    query = query.options(
        joinedload(Message.parts).load_only('public_id',
                                            'content_disposition'),
        joinedload(Message.thread).load_only('public_id', 'discriminator'))

    query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    return query.all()


def events(namespace_id, account_id, event_public_id,
           calendar_public_id, title, description, location, starts_before,
           starts_after, ends_before, ends_after, source, limit, offset,
           db_session):

    query = db_session.query(Event). \
        filter(Event.account_id == account_id)
    event_criteria = []
    if event_public_id:
        query = query.filter(Event.public_id == event_public_id)

    if starts_before is not None:
        event_criteria.append(Event.start < starts_before)

    if starts_after is not None:
        event_criteria.append(Event.start > starts_after)

    if ends_before is not None:
        event_criteria.append(Event.end < ends_before)

    if ends_after is not None:
        event_criteria.append(Event.end > ends_after)

    event_predicate = and_(*event_criteria)
    query = query.filter(event_predicate)

    if calendar_public_id is not None:
        query = query.join(Calendar). \
            filter(Calendar.public_id == calendar_public_id,
                   Calendar.account_id == account_id)

    if title is not None:
        query = query.filter(Event.title.like('%{}%'.format(title)))

    if description is not None:
        query = query.filter(Event.description.like('%{}%'
                                                    .format(description)))

    if location is not None:
        query = query.filter(Event.location.like('%{}%'.format(location)))

    if source is not None:
        query = query.filter(Event.source == source)

    # Eager-load some objects in order to make constructing API
    # representations faster.
    query = query.options(
        subqueryload(Event.participants_by_email))

    query = query.order_by(asc(Event.start)).limit(limit)
    if offset:
        query = query.offset(offset)

    return query.all()


def files(namespace_id, message_public_id, filename, limit, offset,
          db_session):
    # Handle the case of fetching attachments on a particular message.
    if message_public_id is not None:
        message = db_session.query(Message).filter(
            Message.public_id == message_public_id).first()
        if not message:
            # There can't be any results.
            return []
        else:
            results = message.attachments
            if filename is not None:
                return [r for r in results if r.filename == filename]
            else:
                return results

    query = db_session.query(Part).filter(
        Part.namespace_id == namespace_id,
        ~Part.content_disposition.is_(None))

    if filename is not None:
        query = query.filter(Part.filename == filename)

    # STOPSHIP(emfree): this doesn't return files that have been uploaded
    # but not attached to a message!

    query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    return query.all()

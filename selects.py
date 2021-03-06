from pony.orm import *
from pony_starting import *
from dateutil import parser as dt_parser


@db_session
def add_user_message(update):
    user = User.get(telegram_id=update.message.from_user.id)
    if user is None:
        user = User.user_from_update(update)
    message = Message.message_from_update(update, user)
    user.messages.add(message)
    return user, message


@db_session
def add_user_message_text(update, text):
    user = User.get(telegram_id=update.message.from_user.id)
    if user is None:
        user = User.user_from_update(update)
    message = Message(
        user=user,
        text=text
    )
    user.messages.add(message)
    return user, message


@db_session
def del_message(id):
    mes = Message.get(id=id)
    # user = mes.user
    # messages_from_user = user.messages
    # messages_from_user.remove(mes)
    # user.set(messages=messages_from_user)
    mes.delete()


@db_session
def update_user_message_text(update, text):
    user = User.get(telegram_id=update.message.from_user.id)
    if user is None:
        user = User.user_from_update(update)
    message = Message.last_messages(user)[0]
    message.text = text
    return user, message


@db_session
def get_user(telegram_id):
    return User.get(telegram_id=telegram_id)


@db_session
def get_user_by_username(username):
    return User.get(username=username)


@db_session
def get_or_create_user(telegram_id):
    temp_workspace = get_user(telegram_id)
    return temp_workspace if temp_workspace is not None else User(telegram_id=telegram_id)


@db_session
def get_workspace(name):
    return Workspace.get(name=name)


@db_session
def get_or_create_workspace(name):
    temp_workspace = get_workspace(name)
    return temp_workspace if temp_workspace is not None else Workspace(name=name)


@db_session
def get_location(name, workspace):
    if not isinstance(workspace, Workspace):
        workspace = get_workspace(workspace)
    if workspace is None:
        return None
    return Location.get(name=name, workspace=workspace)


@db_session
def get_location(name, workspace):
    if not isinstance(workspace, Workspace):
        workspace = get_workspace(workspace)
    if workspace is None:
        return None
    return Location.get(name=name, workspace=workspace)


@db_session
def create_location(name, workspace):
    return Location(
        workspace=workspace,
        name=name
    )


@db_session
def most_popular_locations(workspace, num=5):
    if not isinstance(workspace, Workspace):
        workspace = get_workspace(workspace)
    if workspace is None:
        return []
    return list(Location.select(lambda loc: loc.workspace ==
                                workspace).order_by(lambda loc: desc(len(loc.meetings)))[:num])


@db_session
def most_popular_workspaces(num=5):
    return list(Workspace.select().order_by(lambda w: desc(len(w.users)))[:num])


@db_session
def last_message(user):
    if not isinstance(user, User):
        user = get_user(user)
    if user is None:
        raise ValueError('no such user')
    return Message.last_messages(user)[0]


@db_session
def last_messages(user, count=2):
    if not isinstance(user, User):
        user = get_user(user)
    if user is None:
        raise ValueError('no such user')
    return Message.last_messages(user, count)


@db_session
def add_location_to_workspace(location, workspace_id):
    workspace = Workspace.get(id=workspace_id)
    location = create_location(location, workspace)
    workspace.locations.add(location)


@db_session
def add_user_to_workspace(user, workspace):
    if not isinstance(user, User):
        user = get_user(user)
        if user is None:
            raise ValueError('user is None')
    if not isinstance(workspace, Workspace):
        workspace = get_or_create_workspace(workspace)
    workspace.users.add(user)


@db_session
def add_workspace_to_user(user, workspace):
    if not isinstance(user, User):
        user = get_user(user)
        if user is None:
            raise ValueError('user is None')
    if not isinstance(workspace, Workspace):
        workspace = get_or_create_workspace(workspace)
    user.workspaces.add(workspace)


@db_session
def user_busy(user, dt=datetime.now()):
    if not isinstance(user, User):
        raise ValueError('User should be instance of class User')
    return list(select((meet.start_time, meet.end_time) for meet in Meeting
                       if user in meet.users and meet.start_time.date() == dt.date()))


@db_session
def location_busy(location, dt=datetime.now()):
    if not isinstance(location, Location):
        raise ValueError('Location should be instance of class Location')
    return list(select((meet.start_time, meet.end_time) for meet in Meeting
                       if meet.location == location and meet.start_time.date() == dt.date()))


@db_session
def get_users_timeslots(username):
    user = get_user_by_username(username)
    return user_busy(user) if user is not None else None


@db_session
def get_location_timeslots(name, workspace):
    loc = get_location(name, workspace)
    return location_busy(loc) if loc is not None else None


@db_session
def get_location_timeslots(name, workspace):
    loc = get_location(name, workspace)
    return location_busy(loc) if loc is not None else None


@db_session
def delete_meeting(id):
    meet = Meeting[id]
    meet.delete()
    # users = meet.users
    # location = meet.location
    # meetings = location.meetings
    # meetings.remove(meet)
    # location.set(meetings=meetings)
    # for user in users:
    #     meetings = user.meetings
    #     meetings.remove(meet)
    #     user.set(meetings=meetings)
    # meet.delete()


@db_session
def check_location_busy(loc, start_time, end_time):
    return exists(m for m in Meeting if m.location == loc and (
        (m.start_time < start_time and start_time < m.end_time) or
        (m.start_time < end_time and end_time < m.end_time)
    ))


@db_session
def check_user_busy(user, start_time, end_time):
    return exists(m for m in Meeting if user in m.users and (
        (m.start_time < start_time and start_time < m.end_time) or
        (m.start_time < end_time and end_time < m.end_time)
    ))


@db_session
def add_meeting_to_base(name, users, workspace, location, start_time, end_time):
    loc = get_location(location, workspace)
    if check_location_busy(loc, start_time, end_time):
        return None, None
    meet = Meeting(
        location=loc,
        name=name,
        start_time=start_time,
        end_time=end_time
    )
    loc.meetings.add(meet)
    user_ids = []
    for username in users:
        user = get_user_by_username(username)
        if user is None:
            continue
        if check_user_busy(user, start_time, end_time):
            delete_meeting(meet.id)
            return None, None
        user_ids.append(user.telegram_id)
        user.meetings.add(meet)
        meet.users.add(user)
    return meet, user_ids


@db_session
def get_meeting(id):
    return Meeting.get(id=id)


@db_session
def check_user_in_meeting(username, id):
    user = get_user_by_username(username)
    if user is None:
        return False
    meeting = get_meeting(id)
    return user in meeting.users


@db_session
def meet_ids_user_in_time(user, dt_start, dt_end):
    if not isinstance(user, User):
        raise ValueError('User should be instance of class User')
    return set(list(select(m.id for m in Meeting
                           if user in m.users and
                           (m.start_time > dt_start and dt_end > m.end_time))))


@db_session
def meet_ids_location_in_time(location, dt_start, dt_end):
    if not isinstance(location, Location):
        raise ValueError('location should be instance of class Location')
    return set(list(select(m.id for m in Meeting
                           if location == m.location and
                           (m.start_time > dt_start and dt_end > m.end_time))))


@db_session
def meet_ids_workspace_in_time(workspace, dt_start, dt_end):
    if not isinstance(workspace, Workspace):
        raise ValueError('workspace should be instance of class Workspace')
    return set(list(select(m.id for m in Meeting
                           if m.location in workspace.locations and
                           (m.start_time > dt_start and dt_end > m.end_time))))


@db_session
def meet_ids_in_time(dt_start, dt_end):
    return set(list(select(m.id for m in Meeting
                           if m.start_time > dt_start and dt_end > m.end_time)))

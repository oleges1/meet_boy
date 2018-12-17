from pony.orm import *
from pony_starting import *


@db_session
def add_user_message(update):
    user = User.get(telegram_id=update.message.from_user.id)
    if user is None:
        user = User.user_from_update(update)
        # user = User.get(telegram_id=update.message.from_user.id)
    message = Message.message_from_update(update, user)
    return user, message


@db_session
def add_user_message_text(update, text):
    user = User.get(telegram_id=update.message.from_user.id)
    if user is None:
        user = User.user_from_update(update)
        # user = User.get(telegram_id=update.message.from_user.id)
    message = Message(
        user=user,
        text=text
    )
    return user, message


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
def create_message(user, text):
    if not isinstance(user, User):
        user = get_user(user)
    return Message(
        user=user,
        text=update.message.text.lower().strip()
    )


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
    return Location.get(name=name, workspace=workspace)


@db_session
def create_location(name, workspace):
    return Location(
        workspace=workspace,
        name=name
    )


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
        user = get_or_create_user(user)
    if not isinstance(workspace, Workspace):
        workspace = get_or_create_workspace(workspace)
    workspace.users.add(user)


@db_session
def add_workspace_to_user(user, workspace):
    if not isinstance(user, User):
        user = get_or_create_user(user)
    if not isinstance(workspace, Workspace):
        workspace = get_or_create_workspace(workspace)
    user.workspaces.add(workspace)


@db_session
def user_busy(user, dt=datetime.now()):
    if not isinstance(user, User):
        raise ValueError('User should be instance of class User')
    return select(meet.start_time, meet.end_time for meet in Meeting
                  if meet.user == user and meet.start_time.day() == dt.day())


@db_session
def location_busy(user, dt=datetime.now()):
    if not isinstance(location, Location):
        raise ValueError('Location should be instance of class Location')
    return select(meet.start_time, meet.end_time for meet in Meeting
                  if meet.location == location and meet.start_time.day() == dt.day())


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
def add_meeting(name, users, workspace, location, start_time, end_time):
    loc = get_location(name, workspace)
    meet = Meeting(
        name=name,
        location=loc,
        start_time=start_time,
        end_time=end_time
    )
    loc.meetings.add(meet)
    user_ids = []
    for username in users:
        user = get_user_by_username(username)
        if user is None:
            continue
        user_ids.append(user.id)
        user.meetings.add(meet)
        meet.users.add(user)
    return meet, user_ids

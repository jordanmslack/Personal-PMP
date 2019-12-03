from app.models import *
from app.tasks.forms import *
from app.tasks.methods import Trello

from flask import render_template, Blueprint, request, redirect, url_for, Response
from uuid import uuid4
from decouple import config
from app import nav
import ast

task = Blueprint('task', __name__, url_prefix='')

nav.Bar('top', [
    nav.Item('Home', 'task.home'),
    nav.Item('Projects', 'task.projects'),
    nav.Item('Actions', 'task.actions'),
    nav.Item('Groups', 'task.groups'),
    nav.Item('Users', 'task.users'),
])


@task.route('/', methods=['GET', 'POST'])
def home():

    user = User.query.all()
    users = len(user)

    data = Project.query.all()
    data = len(data)

    groups = Group.query.all()
    groups = len(groups)

    action = ActionItem.query.all()
    actions = len(action)
    # complete = (len([i for i in action if not i.closed]) / len([i for i in action if i.closed])) * 100

    return render_template('dashboard.html', users=users, data=data, groups=groups, actions=actions)


@task.route('/projects', methods=['GET', 'POST'])
def projects():

    projects = Project.query.all()

    return render_template('projects.html', projects=projects)


@task.route('/actions', methods=['GET', 'POST'])
def actions():

    actions = ActionItem.query.all()

    return render_template('actions.html', actions=actions)


@task.route('/groups', methods=['GET', 'POST'])
def groups():

    groups = Group.query.all()

    return render_template('groups.html', groups=groups)


@task.route('/users', methods=['GET', 'POST'])
def users():

    users = User.query.all()

    return render_template('users.html', users=users)


@task.route('/new_group', methods=['GET', 'POST'])
def new_group():

    form = NewGroup()

    if request.method == 'POST':

        trello = Trello(api_key=config('TRELLO_API_KEY'),
                        api_token=config('TRELLO_API_TOKEN'))

        board_id, list_ids = trello.create_group_board(
            group_name=form.name.data,
            description=f'Project management board for {form.name.data}',
            type=form.type.data
        )

        db.session.add(Group(id=str(uuid4()),
                             name=form.name.data,
                             type=form.type.data,
                             trello_id=board_id,
                             list_ids=str(list_ids),
                             created=datetime.now(),
                             last_modified=datetime.now()))
        db.session.commit()

        # webhook = trello.create_webhook(id=card['id'], description=f'Webhook for {action_id}',
        #                       url='https://8798f98b.ngrok.io/webhook_callback')
        # print(webhook)

        return redirect(url_for('task.home'))

    return render_template('new_group.html', form=form)


@task.route('/group/<group_id>', methods=['GET', 'POST'])
def group(group_id):

    group = Group.query.filter(Group.id == group_id).one()
    users = User.query.filter(User.group_id == group_id).all()

    return render_template('group.html', group=group, users=users)


@task.route('/new_user', methods=['GET', 'POST'])
def new_user():
    form = NewUser()

    groups = Group.query.all()

    form.group.choices = [(group.id, group.name) for group in groups]

    if request.method == 'POST':

        group = Group.query.filter(Group.id == form.group.data).one()
        board_id = group.trello_id
        member_id = str(uuid4())

        trello = Trello(api_key=config('TRELLO_API_KEY'), api_token=config('TRELLO_API_TOKEN'))
        trello.add_board_member(board_id=board_id, member_id=member_id)

        db.session.add(User(id=member_id, first_name=form.first_name.data, last_name=form.last_name.data,
                            group_id=form.group.data, fixed_capacity=form.fixed_capacity.data,
                            variable_capacity=form.variable_capacity.data, trello_id=form.trello_id.data,
                            created=datetime.now(), last_modified=datetime.now()))
        db.session.commit()

        return redirect(url_for('task.home'))

    return render_template('new_user.html', form=form)


@task.route('/user/<user_id>', methods=['GET', 'POST'])
def user(user_id):

    data = User.query.filter(User.id == user_id).one()
    actions = ActionItem.query.filter(ActionItem.user_id == user_id).order_by(ActionItem.priority).all()

    if actions:
        percent_complete = (len([i.time for i in actions if i.closed])/len(actions)) *100
    else:
        percent_complete = 0

    trello = Trello(api_key=config('TRELLO_API_KEY'), api_token=config('TRELLO_API_TOKEN'))
    activities = trello.get_member_actions(member_id=data.trello_id)

    return render_template('user.html', data=data, actions=actions, activities=activities,
                           percent_complete=percent_complete)


@task.route('/project/<id>', methods=['GET', 'POST'])
def project(id):

    data = Project.query.filter(Project.id == id).one()
    actions = ActionItem.query.filter(ActionItem.project_id == id).order_by(ActionItem.priority).all()

    return render_template('project.html', data=data, actions=actions)


@task.route('/new_project', methods=['GET', 'POST'])
def new_project():

    form = NewProject()

    if request.method == 'POST':

        db.session.add(Project(
            id=str(uuid4()),
            name=form.name.data,
            type=form.type.data,
            start_date=form.start_date.data,
            created=datetime.now(),
            description=form.description.data,
        ))
        db.session.commit()

        return redirect(url_for('task.home'))

    return render_template('new_project.html', form=form)


@task.route('/user/<user_id>/new_action', methods=['GET', 'POST'])
def new_user_action(user_id):

    form = NewAction()
    projects = Project.query.all()

    form.assignee.choices = user_id
    form.project.choices = [(project.id, project.name) for project in projects]

    if request.method == 'POST':

        user = User.query.filter(User.id == form.assignee.data).one()
        list_ids = ast.literal_eval(user.group.list_ids)

        trello = Trello(api_key=config('TRELLO_API_KEY'), api_token=config('TRELLO_API_TOKEN'))

        card = trello.create_card(member_ids=[user.trello_id], list_id=list_ids.get('assigned', ''), name=form.name.data,
                                  desc=form.description.data)

        if form.priority.data is None:

            action_items = ActionItem.query.filter(ActionItem.user_id == form.assignee.data)
            priority = max([item.priority for item in action_items if action_items], default=0) + 1

        else:
            priority = form.priority.data

            actions = ActionItem.query.filter(ActionItem.user_id == user.id).filter(ActionItem.priority <= priority)
            for a in actions:
                a.priority = a.priority +1

        action_id = str(uuid4())
        action = ActionItem(
            id=action_id,
            name=form.name.data,
            time=form.time.data,
            user_id=form.assignee.data,
            project_id=form.project.data,
            description=form.description.data,
            start_date=form.start_date.data,
            trello_id=card['id'],
            priority=priority,
            last_modified=datetime.now()
        )

        db.session.add(action)
        db.session.commit()

        return redirect(url_for('task.user',  user_id=user_id))

    return render_template('new_action.html', form=form)


@task.route('/new_action', methods=['GET', 'POST'])
def new_action():

    form = NewAction()
    users = User.query.all()
    projects = Project.query.all()

    form.assignee.choices = [(user.id, f'{user.first_name} {user.last_name}') for user in users]
    form.project.choices = [(project.id, project.name) for project in projects]

    if request.method == 'POST':

        user = User.query.filter(User.id == form.assignee.data).one()
        list_ids = ast.literal_eval(user.group.list_ids)
        trello = Trello(api_key=config('TRELLO_API_KEY'), api_token=config('TRELLO_API_TOKEN'))

        card = trello.create_card(member_ids=[user.trello_id], list_id=list_ids.get('assigned', ''),
                                  name=form.name.data, desc=form.description.data)

        if form.priority.data is None:

            action_items = ActionItem.query.filter(ActionItem.user_id == form.assignee.data)
            priority = max([item.priority for item in action_items if action_items], default=0) + 1

        else:
            priority = form.priority.data
            ActionItem.query.filter(ActionItem.user_id == user.id).filter(ActionItem.priority >= priority).update({'priority': priority + 1})
            db.session.commit()

        action_id = str(uuid4())
        action = ActionItem(
            id=action_id,
            name=form.name.data,
            time=form.time.data,
            user_id=form.assignee.data,
            project_id=form.project.data,
            description=form.description.data,
            start_date=form.start_date.data,
            trello_id=card['id'],
            priority=priority,
            last_modified=datetime.now()
        )

        db.session.add(action)
        db.session.commit()

        return redirect(url_for('task.home'))

    return render_template('new_action.html', form=form)


@task.route('/action/<action_id>', methods=['GET', 'POST'])
def action(action_id):

    data = ActionItem.query.filter(ActionItem.id == action_id).one()

    trello = Trello(api_key=config('TRELLO_API_KEY'), api_token=config('TRELLO_API_TOKEN'))
    card = trello.get_card(card_id=data.trello_id)
    list = trello.get_list(list_id=card['idList'])['name']
    assignee = User.query.filter(User.id == data.user_id)

    return render_template('action.html', data=data, assignee=assignee, card=card, list=list)


@task.route('/edit_action/<action_id>', methods=['GET', 'POST'])
def edit_action(action_id):

    action = ActionItem.query.filter(ActionItem.id == action_id).first()
    form = NewAction(obj=action)

    users = User.query.all()
    form.assignee.choices = [(user.id, f'{user.first_name} {user.last_name}') for user in users]

    projects = Project.query.all()
    form.project.choices = [(project.id, project.name) for project in projects]

    if request.method == 'POST':

        action.name = form.name.data,
        action.time = form.time.data,
        action.user_id = form.assignee.data,
        action.project_id = form.project.data,
        action.description = form.description.data,
        action.start_date = form.start_date.data,
        action.priority = form.priority.data,
        action.last_modified = datetime.now()

        db.session.commit()

        return redirect(url_for('task.action', action_id=action_id))

    return render_template('new_action.html', form=form)


@task.route('/webhook_callback', methods=['HEAD', 'POST'])
def webhook_callback():

    print(request.json)
    if request.method == 'POST':

        if request.json['model']['closed'] is True:
            data = ActionItem.query.filter(ActionItem.trello_id == request.json['model']['id']).one()
            data.closed = request.json['model']['dateLastActivity']
            db.session.commit()

    return Response(status=200)

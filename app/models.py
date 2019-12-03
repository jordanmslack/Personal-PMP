from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import os
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from app import db


DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/task')
engine = create_engine(DATABASE_URL, convert_unicode=True)


class Group(db.Model):
    __tablename__ = 'group'

    id = Column(String, unique=True, primary_key=True)
    name = Column(String)
    trello_id = Column(String)
    list_ids = Column(String)
    type = Column(String)
    created = Column(DateTime())
    last_modified = Column(DateTime(), onupdate=datetime.now())
    closed = Column(DateTime())


class User(db.Model):
    __tablename__ = 'user'

    id = Column(String, unique=True, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    capacity = Column(Integer)
    fixed_capacity = Column(Integer)
    variable_capacity = Column(Integer)
    planning_period = Column(Integer)
    trello_id = Column(String)
    group_id = Column(String, ForeignKey('group.id'))
    group = relationship('Group', primaryjoin='User.group_id == Group.id', backref='user')
    created = Column(DateTime())
    last_modified = Column(DateTime(), onupdate=datetime.now())

    def name(self):
        return f'{self.first_name} {self.last_name}'

    def net_fixed_capacity(self):

        actions = ActionItem.query.filter(ActionItem.user_id == self.id).all()
        net_fixed_capacity = (self.fixed_capacity * self.planning_period) - sum([action.time for action in actions])

        return net_fixed_capacity

    def availability(self):

        net_fixed_capacity = self.net_fixed_capacity()
        real_variable_capacity = self.time_period * self.variable_capacity
        availability = self.time_period - (real_variable_capacity * net_fixed_capacity)

        return availability


class Project(db.Model):
    __tablename__ = 'project'

    id = Column(String, unique=True, primary_key=True)
    name = Column(String)
    type = Column(String)
    description = Column(Text)

    status = Column(String)

    created = Column(DateTime())
    start_date = Column(DateTime())
    last_modified = Column(DateTime(), onupdate=datetime.now())
    desired_completion = Column(DateTime(), onupdate=datetime.now())
    closed = Column(DateTime())

    def percent_complete(self):

        action_items = ActionItem.query.filter_by(project_id=self.id).all()
        complete = [i for i in action_items if i.closed]
        total = [i for i in action_items]
        if len(total) > 0:
            percent = round(len(complete) / len(total) * 100, 2)
            return percent
        else:
            return 0

    def isolated_completion(self):

        action_items = ActionItem.query.filter_by(project_id=self.id).all()
        if action_items:
            remaining = sum([i.time for i in action_items if not i.closed])
            hours = (remaining * 3) * (5 / 7)
            return self.start_date + timedelta(hours=hours)
        else:
            return self.start_date

    def contextual_completion(self):

        action_items = ActionItem.query.filter_by(project_id=self.id).all()
        if action_items:
            completion = max([i.contextual_completion() for i in action_items])
            return completion
        else:
            return self.start_date

    def actual_completion(self):

        if self.closed is not None:
            return round((self.closed - self.start_date).days / 24, 2)
        else:
            return "Pending"

    def completion_delta(self):

        action_items = ActionItem.query.filter_by(project_id=self.id)
        completion = sum([i.time for i in action_items])

        if self.closed is not None:
            return round(self.actual_completion() + completion / completion * 100, 2)
        else:
            return "Pending"


action_relationships = db.Table('action_relationships',
    db.Column('parent_id', String, ForeignKey('action.id'), primary_key=True),
    db.Column('child_id', String, ForeignKey('action.id'), primary_key=True)
)


class ActionItem(db.Model):
    __tablename__ = 'action'

    id = Column(String, unique=True, primary_key=True)
    name = Column(String)
    time = Column(Integer)
    priority = Column(Integer)
    description = Column(Text)
    trello_id = Column(String)
    status = Column(String)
    list_id = Column(String)
    high_delta_reason = Column(Text)
    created = Column(DateTime())
    start_date = Column(DateTime())
    last_modified = Column(DateTime(), onupdate=datetime.now())
    closed = Column(DateTime())

    project_id = Column(String, ForeignKey('project.id'))
    project = relationship('Project', primaryjoin='ActionItem.project_id == Project.id', backref='action')

    user_id = Column(String, ForeignKey('user.id'))
    user = relationship('User', primaryjoin='ActionItem.user_id == User.id', backref='action')

    def estimated_start_date(self):

        if self.priority > 1:
            prior_ity = self.priority - 1
            action_item = ActionItem.query.filter_by(priority=prior_ity).one()
            return action_item.contextual_completion()
        else:
            return self.start_date

    def estimated_completion(self):

        hours = (self.time * 3) * (5 / 7)
        return self.start_date + timedelta(hours=hours)

    def contextual_completion(self):

        action_items = ActionItem.query.filter_by(user_id=self.user_id).all()
        completion = sum([i.time for i in action_items if i.priority <= self.priority and i.closed is None])
        hours = ((completion * 3) * (5/7))
        estimated_start_date = self.start_date + timedelta(hours=hours)

        return estimated_start_date

    def actual_completion(self):

        if self.closed is not None:
            return round((self.closed - self.start_date).days / 24, 2)

    def completion_delta(self):

        if self.closed is not None:
            return round(self.actual_completion() + self.time / self.time * 100, 2)

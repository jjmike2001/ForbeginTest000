# -*- encoding: utf-8 -*-
# Copyright 2013 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An :ref:`Action Plan <action_plan_definition>` is a flow of
:ref:`Actions <action_definition>` that should be executed in order to satisfy
a given :ref:`Goal <goal_definition>`.

An :ref:`Action Plan <action_plan_definition>` is generated by Watcher when an
:ref:`Audit <audit_definition>` is successful which implies that the
:ref:`Strategy <strategy_definition>`
which was used has found a :ref:`Solution <solution_definition>` to achieve the
:ref:`Goal <goal_definition>` of this :ref:`Audit <audit_definition>`.

In the default implementation of Watcher, an
:ref:`Action Plan <action_plan_definition>`
is only composed of successive :ref:`Actions <action_definition>`
(i.e., a Workflow of :ref:`Actions <action_definition>` belonging to a unique
branch).

However, Watcher provides abstract interfaces for many of its components,
allowing other implementations to generate and handle more complex
:ref:`Action Plan(s) <action_plan_definition>`
composed of two types of Action Item(s):

-  simple :ref:`Actions <action_definition>`: atomic tasks, which means it
   can not be split into smaller tasks or commands from an OpenStack point of
   view.
-  composite Actions: which are composed of several simple
   :ref:`Actions <action_definition>`
   ordered in sequential and/or parallel flows.

An :ref:`Action Plan <action_plan_definition>` may be described using
standard workflow model description formats such as
`Business Process Model and Notation 2.0 (BPMN 2.0)
<http://www.omg.org/spec/BPMN/2.0/>`_ or `Unified Modeling Language (UML)
<http://www.uml.org/>`_.

An :ref:`Action Plan <action_plan_definition>` has a life-cycle and its current
state may be one of the following:

-  **RECOMMENDED** : the :ref:`Action Plan <action_plan_definition>` is waiting
   for a validation from the :ref:`Administrator <administrator_definition>`
-  **ONGOING** : the :ref:`Action Plan <action_plan_definition>` is currently
   being processed by the :ref:`Watcher Applier <watcher_applier_definition>`
-  **SUCCEEDED** : the :ref:`Action Plan <action_plan_definition>` has been
   executed successfully (i.e. all :ref:`Actions <action_definition>` that it
   contains have been executed successfully)
-  **FAILED** : an error occurred while executing the
   :ref:`Action Plan <action_plan_definition>`
-  **DELETED** : the :ref:`Action Plan <action_plan_definition>` is still
   stored in the :ref:`Watcher database <watcher_database_definition>` but is
   not returned any more through the Watcher APIs.
-  **CANCELLED** : the :ref:`Action Plan <action_plan_definition>` was in
   **PENDING** or **ONGOING** state and was cancelled by the
   :ref:`Administrator <administrator_definition>`
"""

from watcher.common import exception
from watcher.common import utils
from watcher.db import api as db_api
from watcher import objects
from watcher.objects import base
from watcher.objects import fields as wfields


class State(object):
    RECOMMENDED = 'RECOMMENDED'
    PENDING = 'PENDING'
    ONGOING = 'ONGOING'
    FAILED = 'FAILED'
    SUCCEEDED = 'SUCCEEDED'
    DELETED = 'DELETED'
    CANCELLED = 'CANCELLED'


@base.WatcherObjectRegistry.register
class ActionPlan(base.WatcherPersistentObject, base.WatcherObject,
                 base.WatcherObjectDictCompat):

    # Version 1.0: Initial version
    # Version 1.1: Added 'audit' and 'strategy' object field
    # Version 1.2: audit_id is not nullable anymore
    VERSION = '1.2'

    dbapi = db_api.get_instance()

    fields = {
        'id': wfields.IntegerField(),
        'uuid': wfields.UUIDField(),
        'audit_id': wfields.IntegerField(),
        'strategy_id': wfields.IntegerField(),
        'first_action_id': wfields.IntegerField(nullable=True),
        'state': wfields.StringField(nullable=True),
        'global_efficacy': wfields.FlexibleDictField(nullable=True),

        'audit': wfields.ObjectField('Audit', nullable=True),
        'strategy': wfields.ObjectField('Strategy', nullable=True),
    }

    object_fields = {
        'audit': (objects.Audit, 'audit_id'),
        'strategy': (objects.Strategy, 'strategy_id'),
    }

    @base.remotable_classmethod
    def get(cls, context, action_plan_id, eager=False):
        """Find a action_plan based on its id or uuid and return a Action object.

        :param action_plan_id: the id *or* uuid of a action_plan.
        :param eager: Load object fields if True (Default: False)
        :returns: a :class:`Action` object.
        """
        if utils.is_int_like(action_plan_id):
            return cls.get_by_id(context, action_plan_id, eager=eager)
        elif utils.is_uuid_like(action_plan_id):
            return cls.get_by_uuid(context, action_plan_id, eager=eager)
        else:
            raise exception.InvalidIdentity(identity=action_plan_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, action_plan_id, eager=False):
        """Find a action_plan based on its integer id and return a ActionPlan object.

        :param action_plan_id: the id of a action_plan.
        :param eager: Load object fields if True (Default: False)
        :returns: a :class:`ActionPlan` object.
        """
        db_action_plan = cls.dbapi.get_action_plan_by_id(
            context, action_plan_id, eager=eager)
        action_plan = cls._from_db_object(
            cls(context), db_action_plan, eager=eager)
        return action_plan

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid, eager=False):
        """Find a action_plan based on uuid and return a :class:`ActionPlan` object.

        :param uuid: the uuid of a action_plan.
        :param context: Security context
        :param eager: Load object fields if True (Default: False)
        :returns: a :class:`ActionPlan` object.
        """
        db_action_plan = cls.dbapi.get_action_plan_by_uuid(
            context, uuid, eager=eager)
        action_plan = cls._from_db_object(
            cls(context), db_action_plan, eager=eager)
        return action_plan

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None, filters=None,
             sort_key=None, sort_dir=None, eager=False):
        """Return a list of ActionPlan objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param filters: Filters to apply. Defaults to None.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :param eager: Load object fields if True (Default: False)
        :returns: a list of :class:`ActionPlan` object.
        """
        db_action_plans = cls.dbapi.get_action_plan_list(context,
                                                         limit=limit,
                                                         marker=marker,
                                                         filters=filters,
                                                         sort_key=sort_key,
                                                         sort_dir=sort_dir,
                                                         eager=eager)

        return [cls._from_db_object(cls(context), obj, eager=eager)
                for obj in db_action_plans]

    @base.remotable
    def create(self):
        """Create an :class:`ActionPlan` record in the DB.

        :returns: An :class:`ActionPlan` object.
        """
        values = self.obj_get_changes()
        db_action_plan = self.dbapi.create_action_plan(values)
        # Note(v-francoise): Always load eagerly upon creation so we can send
        # notifications containing information about the related relationships
        self._from_db_object(self, db_action_plan, eager=True)

    @base.remotable
    def destroy(self):
        """Delete the action plan from the DB"""
        related_efficacy_indicators = objects.EfficacyIndicator.list(
            context=self._context,
            filters={"action_plan_uuid": self.uuid})

        # Cascade soft_delete of related efficacy indicators
        for related_efficacy_indicator in related_efficacy_indicators:
            related_efficacy_indicator.destroy()

        self.dbapi.destroy_action_plan(self.uuid)
        self.obj_reset_changes()

    @base.remotable
    def save(self):
        """Save updates to this Action plan.

        Updates will be made column by column based on the result
        of self.what_changed().
        """
        updates = self.obj_get_changes()
        db_obj = self.dbapi.update_action_plan(self.uuid, updates)
        obj = self._from_db_object(self, db_obj, eager=False)
        self.obj_refresh(obj)
        self.obj_reset_changes()

    @base.remotable
    def refresh(self, eager=False):
        """Loads updates for this Action plan.

        Loads a action_plan with the same uuid from the database and
        checks for updated attributes. Updates are applied from
        the loaded action_plan column by column, if there are any updates.
        :param eager: Load object fields if True (Default: False)
        """
        current = self.get_by_uuid(self._context, uuid=self.uuid, eager=eager)
        self.obj_refresh(current)

    @base.remotable
    def soft_delete(self):
        """Soft Delete the Action plan from the DB"""
        related_actions = objects.Action.list(
            context=self._context,
            filters={"action_plan_uuid": self.uuid})

        # Cascade soft_delete of related actions
        for related_action in related_actions:
            related_action.soft_delete()

        related_efficacy_indicators = objects.EfficacyIndicator.list(
            context=self._context,
            filters={"action_plan_uuid": self.uuid})

        # Cascade soft_delete of related efficacy indicators
        for related_efficacy_indicator in related_efficacy_indicators:
            related_efficacy_indicator.soft_delete()

        self.state = State.DELETED
        self.save()
        db_obj = self.dbapi.soft_delete_action_plan(self.uuid)
        obj = self._from_db_object(
            self.__class__(self._context), db_obj, eager=False)
        self.obj_refresh(obj)

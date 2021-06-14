"""
Transformers for navigation related events.
"""
from logging import getLogger

from tincan import Activity, ActivityDefinition, ActivityList, Context, ContextActivities, Extensions, LanguageMap

from event_routing_backends.helpers import get_anonymous_user_id_by_username, make_course_url
from event_routing_backends.processors.xapi import constants
from event_routing_backends.processors.xapi.registry import XApiTransformersRegistry
from event_routing_backends.processors.xapi.transformer import XApiTransformer, XApiVerbTransformerMixin

logger = getLogger(__name__)


VERB_MAP = {
    'edx.ui.lms.sequence.next_selected': {
        'id': constants.XAPI_VERB_TERMINATED,
        'display': constants.TERMINATED
    },
    'edx.ui.lms.sequence.previous_selected': {
        'id': constants.XAPI_VERB_TERMINATED,
        'display': constants.TERMINATED
    },
    'edx.ui.lms.sequence.tab_selected': {
        'id': constants.XAPI_VERB_INITIALIZED,
        'display': constants.INITIALIZED
    },
    'edx.ui.lms.link_clicked': {
        'id': constants.XAPI_VERB_EXPERIENCED,
        'display': constants.EXPERIENCED
    },
    'edx.ui.lms.sequence.outline.selected': {
        'id': constants.XAPI_VERB_INITIALIZED,
        'display': constants.INITIALIZED
    },
    'edx.ui.lms.outline.selected': {
        'id': constants.XAPI_VERB_INITIALIZED,
        'display': constants.INITIALIZED
    }
}


class NavigationTransformersMixin(XApiTransformer, XApiVerbTransformerMixin):
    """
    Base transformer class for navigation events.

    This class has the common attributes for all navigation events.
    """
    additional_fields = ('context', )
    verb_map = VERB_MAP


@XApiTransformersRegistry.register('edx.ui.lms.link_clicked')
class LinkClickedTransformer(NavigationTransformersMixin):
    """
    xAPI transformer for event generated when user clicks a link.
    """

    def get_object(self):
        """
        Get object for xAPI transformed event.

        Returns:
            `Activity`
        """
        return Activity(
            id=self.event['data']['target_url'] if 'target_url' in self.event['data'] else None,
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_LINK,
                name=LanguageMap({constants.EN: 'Link name'}),
                extensions=Extensions(**({
                    constants.XAPI_ACTIVITY_POSITION: self.event['data']['target_url']
                } if 'target_url' in self.event['data'] else {}))
            ),
        )

    def get_context(self):
        """
        Get context for xAPI transformed event.

        Returns:
            `Context`
        """

        if not self.extract_username():
            logger.info(
                'In Event %s username not found!',
                self.event
            )
        return Context(
            registration=get_anonymous_user_id_by_username(
                self.extract_username()
            ),
            contextActivities=self.get_context_activities()
        )

    def get_context_activities(self):
        """
        Get context activities for xAPI transformed event.

        Returns:
            `ContextActivities`
        """
        parent_activities = [
            Activity(
                id=make_course_url(self.event['context']['course_id'])
                if 'course_id' in self.event['context'] else None,
                object_type=constants.XAPI_ACTIVITY_COURSE
            ),
        ]
        return ContextActivities(
            parent=ActivityList(parent_activities),
        )


@ XApiTransformersRegistry.register('edx.ui.lms.sequence.outline.selected')
@ XApiTransformersRegistry.register('edx.ui.lms.outline.selected')
class OutlineSelectedTransformer(NavigationTransformersMixin):
    """
    xAPI transformer for Navigation events.
    """
    additional_fields = ('context', )

    def get_object(self):
        """
        Get object for xAPI transformed event.

        Returns:
            `Activity`
        """
        return Activity(
            id=self.event['data']['target_url'],
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_MODULE,
                name=LanguageMap(**({constants.EN: self.event['data']['target_name']}
                                    if 'target_name' in self.event['data'] else {})),
            ),
        )

    def get_context(self):
        """
        Get context for xAPI transformed event.

        Returns:
            `Context`
        """
        return Context(
            registration=get_anonymous_user_id_by_username(
                self.extract_username()
            )
        )


@ XApiTransformersRegistry.register('edx.ui.lms.sequence.next_selected')
@ XApiTransformersRegistry.register('edx.ui.lms.sequence.previous_selected')
@ XApiTransformersRegistry.register('edx.ui.lms.sequence.tab_selected')
class TabNavigationTransformer(NavigationTransformersMixin):
    """
    xAPI transformer for Navigation events.
    """
    additional_fields = ('context', )

    def get_object(self):
        """
        Get object for xAPI transformed event.

        Returns:
            `Activity`
        """
        if self.event['name'] == 'edx.ui.lms.sequence.tab_selected':
            position = self.event['data']['target_tab']
        else:
            position = self.event['data']['current_tab']

        return Activity(
            id=self.event['data']['id'],
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_MODULE,
                extensions=Extensions({
                    constants.XAPI_ACTIVITY_POSITION: position
                })
            ),
        )

    def get_context(self):
        """
        Get context for xAPI transformed event.

        Returns:
            `Context`
        """
        event_name = self.event['name']
        if event_name == 'edx.ui.lms.sequence.tab_selected':
            extensions = Extensions(**({
                constants.XAPI_CONTEXT_STARTING_POSITION: self.event['data']['current_tab'],
            } if 'current_tab' in self.event['data'] else {}))
        elif event_name == 'edx.ui.lms.sequence.next_selected':
            extensions = Extensions({
                constants.XAPI_CONTEXT_ENDING_POSITION: 'next unit',
            })
        else:
            extensions = Extensions({
                constants.XAPI_CONTEXT_ENDING_POSITION: 'previous unit',
            })

        return Context(
            registration=get_anonymous_user_id_by_username(
                self.extract_username()
            ),
            contextActivities=self.get_context_activities(),
            extensions=extensions
        )

    def get_context_activities(self):
        """
        Get context activities for xAPI transformed event.

        Returns:
            `ContextActivities`
        """
        parent_activities = [
            Activity(
                id=self.event['data']['id'],
                object_type=constants.XAPI_ACTIVITY_MODULE
            ),
        ]
        return ContextActivities(
            parent=ActivityList(parent_activities),
        )

"""
Transformers for enrollment related events.
"""

from tincan import Activity, ActivityDefinition, Context, LanguageMap, Verb

from event_routing_backends.helpers import get_anonymous_user_id_by_username, get_course_from_id, make_course_url
from event_routing_backends.processors.xapi import constants
from event_routing_backends.processors.xapi.registry import XApiTransformersRegistry
from event_routing_backends.processors.xapi.transformer import XApiTransformer


class BaseEnrollmentTransformer(XApiTransformer):
    """
    Base transformer for enrollment events.
    """
    additional_fields = ('context', )

    def __init__(self):
        super().__init__(self)
        self.minor_version = '2.1'
        self.backend_name = 'xAPI'

    def get_object(self):
        """
        Get object for xAPI transformed event.

        Returns:
            `Activity`
        """
        course_id = self.get_data('context.course_id', True)
        object_id = make_course_url(course_id)
        course = get_course_from_id(course_id)
        display_name = course['display_name']

        return Activity(
            id=object_id,
            definition=ActivityDefinition(
                type=constants.XAPI_ACTIVITY_COURSE,
                name=LanguageMap(**({constants.EN: display_name} if display_name is not None else {})),
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


@XApiTransformersRegistry.register('edx.course.enrollment.activated')
class EnrollmentActivatedTransformer(BaseEnrollmentTransformer):
    """
    Transformers for event generated when learner enrolls in a course.
    """
    verb = Verb(
        id=constants.XAPI_VERB_REGISTERED,
        display=LanguageMap({constants.EN: constants.REGISTERED}),
    )


@XApiTransformersRegistry.register('edx.course.enrollment.deactivated')
class EnrollmentDeactivatedTransformer(BaseEnrollmentTransformer):
    """
    Transformers for event generated when learner un-enrolls from a course.
    """
    verb = Verb(
        id=constants.XAPI_VERB_UNREGISTERED,
        display=LanguageMap({constants.EN: constants.UNREGISTERED}),
    )

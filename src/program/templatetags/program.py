from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def feedbackbutton(context):
    """ A templatetag to show a suitable button for EventFeedback """
    event = context["event"]
    if event.proposal and event.proposal.user == context.request.user:
        # current user is the event owner, show a link to EventFeedbackList
        return mark_safe("<a class='btn btn-primary' href='%s'><i class='fas fa-comments'></i> Read Feedback (%s)</a>" % (
            reverse("program:eventfeedback_list", kwargs={
                "camp_slug": event.camp.slug,
                "event_slug": event.slug
            }),
            event.feedbacks.filter(approved=True).count(),
        ))
    # FIXME: for some reason this triggers a lookup even though all feedbacks have been prefetched..
    elif event.feedbacks.filter(user=context.request.user).exists():
        # this user already submitted feedback for this event, show a link to DetailView
        return mark_safe("<a class='btn btn-default' href='%s'><i class='fas fa-comment-dots'></i> Change Feedback</a>" % (
            reverse("program:eventfeedback_detail", kwargs={"camp_slug": event.camp.slug, "event_slug": event.slug})
        ))
    else:
        # this user has not submitted feedback yet, show a link to CreateView
        return mark_safe("<a class='btn btn-success' href='%s'><i class='fas fa-comment'></i> Add Feedback</a>" % (
            reverse("program:eventfeedback_create", kwargs={"camp_slug": event.camp.slug, "event_slug": event.slug})
        ))


from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView

from camps.mixins import CampViewMixin
from tokens.models import Token
from .models import Feedback


class FeedbackCreate(LoginRequiredMixin, CampViewMixin, CreateView):
    model = Feedback
    fields = ['feedback']

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.user = self.request.user
        thanks_message = "Thank you! Your feedback is highly appreciated!"
        try:
            token = Token.objects.get(
                camp=self.camp,
                description="Feedback thanks"
            )
            thanks_message += " And for your efforts, here is a token: {}".format(token.token)
        except Token.DoesNotExist:
            pass

        messages.success(self.request, thanks_message)

        return HttpResponseRedirect(reverse("feedback", kwargs={"camp_slug": self.camp.slug}))

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import SingleObjectMixin

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http import HttpResponse


class EnsureWritableCampMixin(SingleObjectMixin):
    def dispatch(self, request: HttpRequest, *args: list[Any], **kwargs: dict[str, Any]) -> HttpResponse:
        # do not permit view if camp is in readonly mode
        if self.camp.read_only:
            messages.error(request, "No thanks")
            return redirect(
                reverse("village_list", kwargs={"camp_slug": self.camp.slug}),
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)

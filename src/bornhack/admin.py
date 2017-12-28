from django.contrib import admin
from django.contrib.auth.decorators import login_required

# Ensure users go through the allauth workflow when logging into admin.
admin.site.login = login_required(admin.site.login)
# Run the standard admin set-up.
admin.autodiscover()
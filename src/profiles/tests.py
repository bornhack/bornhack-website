from collections import namedtuple
from django.contrib.auth.models import AnonymousUser
from django.template import Context
from django.template import Template

from teams.models import TeamMember
from utils.tests import BornhackTestBase


class TestTemplateTags(BornhackTestBase):
    """Class for grouping `templatetags` tests."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        super().setUpTestData()
        cls.profile = cls.users[9].profile
        cls.profile.public_credit_name_approved = False

        cls.public_fallback = "Unnamed"
        cls.user = cls.users[8]
        cls.FakeRequest = namedtuple("FakeRequest", ["user"])
        cls.fake_request = cls.FakeRequest(user=cls.user)

    def test_display_name_for_anon_user(self) -> None:
        """Test `display_name` for an anonymous user."""
        context = {"user": self.profile}
        # Profile without approved `public_credit_name`
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.public_fallback

        # Profile with approved `public_credit_name`
        self.profile.public_credit_name_approved = True
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.public_credit_name

    def test_display_name_for_volunteer(self) -> None:
        """Test `display_name` for a volunteer (team member)."""
        context = {
            "user": self.profile,
            "request": self.fake_request,
            "camp": self.camp,
        }
        # Profile with `name`
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.name

        # Profile with approved `public_credit_name`
        self.profile.name = None
        self.profile.public_credit_name_approved = True
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.public_credit_name

        # Profile without name and approved `public_credit_name`
        self.profile.name = None
        self.profile.public_credit_name_approved = False
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.user.username

    def test_display_name_handling_team_member_by_camp(self) -> None:
        """Test `display_name` handles a user being volunteer at another camp."""
        context = {
            "user": self.profile,
            "request": self.fake_request,
            "camp": self.camp,
        }
        # Team member of related camp
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.private_name

        # Team member of previous camp
        TeamMember.objects.filter(user=self.user, team__camp=self.camp).delete()
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.public_name

        # Not a Team member of any camps
        fake_request = self.FakeRequest(user=self.users[13])
        context.update({"request": fake_request})
        result = Template(
            "{% load profile_display %}"
            "{% display_name user %}"
        ).render(Context(context))

        assert result == self.profile.public_name


class TestProfileModel(BornhackTestBase):
    """Class for grouping `ProfileModel` tests."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        super().setUpTestData()
        cls.profile = cls.users[10].profile
        cls.profile.public_credit_name_approved = False

    def test_approving_public_credit_name(self) -> None:
        """Test `approve_public_credit_name` changes object state."""
        assert self.profile.public_credit_name_approved is False

        self.profile.approve_public_credit_name()

        assert self.profile.public_credit_name_approved is True

    def test_return_approved_public_credit_name(self) -> None:
        """
        Test `public_name` property returns the approved `public_credit_name`.
        """
        self.profile.public_credit_name_approved = True

        assert self.profile.public_name == self.profile.public_credit_name

    def test_public_name_not_approved_return_unnamed(self) -> None:
        """
        Test `public_name` property returns `Unnamed`
        when `public_credit_name` isn't approved.
        """
        assert self.profile.public_name == "Unnamed"

    def test_private_name_returns_display_name(self) -> None:
        """Test `private_name` property returns `name` when set."""
        expected = "Test"
        self.profile.name = expected

        assert self.profile.private_name == expected

        self.profile.public_credit_name_approved = True

        assert self.profile.private_name == expected

    def test_private_name_return_public_credit_name(self) -> None:
        """
        Test `private_name` property returns the approved public_credit_name,
        when no `name` is set.
        """
        self.profile.name = None
        self.profile.public_credit_name_approved = True

        assert self.profile.private_name == self.profile.public_credit_name

    def test_private_name_return_username_as_fallback(self) -> None:
        """
        Test `private_name` property return the username as a fallback,
        when no profile name or public_credit_name is added.
        """
        self.profile.name = None
        self.profile.public_credit_name = None

        assert self.profile.private_name == self.profile.user.username

    def test_get_display_name_handling_team_member_by_related_camp(self) -> None:
        """Test `get_display_name` handles a user being volunteer at related camp."""
        user = self.users[8]

        result = self.profile.get_display_name(user, self.camp)

        assert result == self.profile.private_name

    def test_get_display_name_handling_team_member_by_previous_camp(self) -> None:
        """Test `get_display_name` handles a user being volunteer at previous camp."""
        user = self.users[8]
        TeamMember.objects.filter(user=user, team__camp=self.camp).delete()

        result = self.profile.get_display_name(user, self.camp)

        assert result == self.profile.public_name

    def test_get_display_name_handling_not_a_team_member_in_any_camp(self) -> None:
        """Test `get_display_name` handles a user not being a team member in any camps."""
        user = self.users[13]

        result = self.profile.get_display_name(user, self.camp)

        assert result == self.profile.public_name

    def test_get_display_name_with_unauthenticated_user(self) -> None:
        """
        Test `get_display_name` return public name when user is unauthenticated.
        """
        user = AnonymousUser()

        result = self.profile.get_display_name(user, self.camp)

        assert result == self.profile.public_name

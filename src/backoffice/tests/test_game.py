import pytest

from django.urls import reverse

from tokens.models import TokenCategory


class TestTokenCategoryListView:
    """Class for grouping TokenCategoryListView tests."""

    @pytest.fixture
    def url(self, camp) -> str:
        """Reverse URL for view."""
        kwargs = {"camp_slug": camp.slug}
        return reverse("backoffice:token_category_list", kwargs=kwargs)

    @pytest.fixture
    def mixed_categories(self, token_category_factory, token_factory) -> list:
        """Fixture for categories with and without related tokens."""
        categories = []
        for i in range(5):
            category = token_category_factory(persist=True, name=f"category{i}")

            if i % 2 == 0:
                token_factory(persist=True, category=category)

            categories.append(category)

        return categories

    @pytest.mark.usefixtures("mixed_categories")
    def test_all_categories_exist_in_queryset(self, admin_client):
        """Test if all categories with and without Tokens exist in queryset."""
        expected = TokenCategory.objects.all()

        response = admin_client.get(admin_client.url)
        result = response.context.get("object_list")

        assert result.count() == expected.count()

    def test_annotate_token_count_for_current_camp(
        self,
        admin_client,
        token_category,
        token_factory,
        test_camps
    ):
        """Test the object list has annotated token count for current camp."""
        expected = 0

        response = admin_client.get(admin_client.url)
        result = response.context.get("object_list")

        assert result.get(pk=token_category.pk).token_count == expected

        token_count = 6
        expected = token_count / len(test_camps)
        for i in range(token_count):
            token_factory(persist=True, camp=test_camps[i % 3])

        response = admin_client.get(admin_client.url)
        result = response.context.get("object_list")

        assert result.get(pk=token_category.pk).token_count == expected


class TestTokenCategoryDetailView:
    """Class for grouping TokenCategoryDetailView tests."""

    @pytest.fixture
    def url(self, camp, token_category) -> str:
        """Reverse URL for view."""
        kwargs = {"camp_slug": camp.slug, "pk": token_category.pk}
        return reverse("backoffice:token_category_detail", kwargs=kwargs)

    def test_add_category_tokens_for_current_camp_to_context(
        self,
        admin_client,
        token_category,
        token_category_factory,
        test_camps,
        token_factory
    ):
        """Test only tokens for this category and camp is added to context."""
        category2 = token_category_factory(persist=True, name="test")

        expected = []
        for camp in list(test_camps):
            for _ in range(3):
                if camp == test_camps.current:
                    expected.append(
                        token_factory(persist=True, camp=camp, category=token_category)
                    )
                token_factory(persist=True, camp=camp, category=category2)

        response = admin_client.get(admin_client.url)
        result = response.context.get("category_tokens")

        assert list(result) == expected


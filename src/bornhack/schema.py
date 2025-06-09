from __future__ import annotations

from graphene import ObjectType
from graphene import Schema
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from camps.models import Camp
from program.schema import ProgramQuery


class CampNode(DjangoObjectType):
    class Meta:
        model = Camp
        interfaces = (relay.Node,)
        filter_fields = {"title": ["icontains", "iexact"]}
        only_fields = (
            "title",
            "slug",
            "tagline",
            "shortslug",
            "buildup",
            "camp",
            "teardown",
            "colour",
        )

    def resolve_buildup(self, info):
        return [self.buildup.lower, self.buildup.upper]

    def resolve_camp(self, info):
        return [self.camp.lower, self.camp.upper]

    def resolve_teardown(self, info):
        return [self.teardown.lower, self.teardown.upper]


class CampQuery:
    camp = relay.Node.Field(CampNode)
    all_camps = DjangoFilterConnectionField(CampNode)


class Query(CampQuery, ProgramQuery, ObjectType):
    pass


schema = Schema(query=Query)

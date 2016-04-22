from django.contrib import admin

from .models import Camp, Day, Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    pass


class ExpenseInlineAdmin(admin.TabularInline):
    model = Expense


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    pass


class DayInlineAdmin(admin.TabularInline):
    model = Day


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    inlines = [
        DayInlineAdmin,
        ExpenseInlineAdmin,
    ]

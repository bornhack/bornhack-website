from django.contrib import admin

from .models import Camp, Day, Expense, Signup


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    pass


class ExpenseInlineAdmin(admin.TabularInline):
    model = Expense


@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    pass


class SignupInlineAdmin(admin.TabularInline):
    model = Signup


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
        SignupInlineAdmin
    ]

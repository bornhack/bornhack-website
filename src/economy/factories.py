import factory

from .models import Bank, BankAccount, BankTransaction


class BankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bank

    name = factory.Faker("company")


class BankAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BankAccount

    bank = factory.Iterator(Bank.objects.all())
    name = factory.Faker("word")
    reg_no = factory.Faker("numerify", text="####")
    account_no = factory.Faker("numerify", text="########")


class BankTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BankTransaction

    bank_account = factory.Iterator(BankAccount.objects.all())
    date = factory.Faker("date_between", start_date="-6y")
    text = factory.Faker("sentence")
    amount = factory.Faker(
        "pydecimal", right_digits=2, min_value=-100000, max_value=100000
    )
    balance = factory.Faker(
        "pydecimal", right_digits=2, min_value=-100000, max_value=100000
    )

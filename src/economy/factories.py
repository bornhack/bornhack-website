from __future__ import annotations

import random

import factory
import faker
from django.contrib.auth.models import User
from django.utils import timezone
from utils.slugs import unique_slugify

from camps.models import Camp
from teams.models import Team

from .models import Bank
from .models import BankAccount
from .models import BankTransaction
from .models import Chain
from .models import ClearhausSettlement
from .models import CoinifyBalance
from .models import CoinifyInvoice
from .models import CoinifyPaymentIntent
from .models import CoinifyPayout
from .models import CoinifySettlement
from .models import Credebtor
from .models import EpayTransaction
from .models import Expense
from .models import MobilePayTransaction
from .models import Pos
from .models import Revenue
from .models import ZettleBalance
from .models import ZettleReceipt

fake = faker.Faker()

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
        "pydecimal",
        right_digits=2,
        min_value=-100000,
        max_value=100000,
    )
    balance = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=-100000,
        max_value=100000,
    )


class CoinifyInvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoinifyInvoice

    coinify_id = factory.Faker("random_int", min=100000, max=200000)
    coinify_id_alpha = factory.Faker("pystr", min_chars=5, max_chars=8)
    coinify_created = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    payment_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=10000,
    )
    payment_currency = "DKK"
    payment_btc_amount = factory.Faker(
        "pydecimal",
        right_digits=8,
        min_value=1,
        max_value=4,
    )
    description = factory.Faker("sentence")
    custom = {}
    credited_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=10000,
    )
    credited_currency = "EUR"
    state = "complete"
    payment_type = factory.Faker(
        "random_element",
        elements=["normal", "normal", "extra"],
    )


class CoinifyPaymentIntentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoinifyPaymentIntent

    coinify_id = factory.Faker("uuid4")
    coinify_created = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    reference_type = "payment_intent"
    merchant_id = factory.Faker("uuid4")
    merchant_name = "Sandbox Factory"
    subaccount_id = ""
    subaccount_name = ""
    state = "completed"
    state_reason = "completed_exact_amount"
    original_order_id = factory.Faker("random_int", min=100000, max=200000)
    order = None
    api_payment_intent = None
    customer_email = "coinifycustomer@example.com"
    requested_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=10000,
    )
    requested_currency = "DKK"
    amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=10000,
    )
    currency = "DKK"


class CoinifyPayoutFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoinifyPayout

    coinify_id = factory.Faker("random_int", min=100000, max=200000)
    coinify_created = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    amount = factory.Faker("pydecimal", right_digits=2, min_value=1000, max_value=10000)
    fee = factory.Faker("pydecimal", right_digits=2, min_value=1000, max_value=10000)
    transferred = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=1000,
        max_value=10000,
    )
    currency = "EUR"


class CoinifySettlementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoinifySettlement

    settlement_id = factory.Faker("uuid4")
    account = factory.Faker("word")
    create_time = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    gross_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=1000,
        max_value=10000,
    )
    fee = factory.Faker("pydecimal", right_digits=2, min_value=1, max_value=10)
    net_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=1000,
        max_value=10000,
    )
    payout_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=1000,
        max_value=10000,
    )


class CoinifyBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CoinifyBalance

    date = factory.Sequence(lambda _: fake.unique.date_between(start_date="-6y"))
    btc = factory.Faker("pydecimal", right_digits=8, min_value=1, max_value=4)
    dkk = factory.Faker("pydecimal", right_digits=2, min_value=100, max_value=10000)
    eur = factory.Faker("pydecimal", right_digits=2, min_value=100, max_value=10000)


class EpayTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EpayTransaction

    merchant_id = "1024488"
    transaction_id = factory.Faker("random_int", min=100000, max=200000)
    order_id = factory.Faker("random_int", min=1000, max=2000)
    currency = "DKK"
    auth_date = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    auth_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=500,
        max_value=3000,
    )
    captured_date = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    captured_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=500,
        max_value=3000,
    )
    card_type = factory.Faker(
        "random_element",
        elements=[
            "Mastercard (udenlandsk)",
            "Visa/Electron (udenlandsk)",
            "Mastercard",
        ],
    )
    description = factory.Faker("sentence")
    transaction_fee = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=2,
        max_value=5,
    )


class ClearhausSettlementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClearhausSettlement

    merchant_id = "2003656"
    merchant_name = "BornHack ApS"
    clearhaus_uuid = factory.Faker("uuid4")
    settled = factory.Faker("random_element", elements=[True, True, True, False])
    currency = "DKK"
    period_start_date = factory.Faker("date_between", start_date="-6y")
    period_end_date = factory.Faker("date_between", start_date="-6y")
    payout_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    payout_date = factory.Faker("date_between", start_date="-6y")
    summary_sales = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    summary_credits = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    summary_refunds = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    summary_chargebacks = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    summary_fees = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    summary_other_postings = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    summary_net = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    reserve_amount = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    reserve_date = factory.Faker("date_between", start_date="-6y")
    fees_sales = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_refunds = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_authorisations = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_credits = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_minimum_processing = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_service = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_wire_transfer = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_chargebacks = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_retrieval_requests = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    payout_reference_number = factory.Faker("random_int", min=100000, max=200000)
    payout_descriptor = factory.Faker("sentence")
    reserve_reference_number = factory.Faker("random_int", min=100000, max=200000)
    reserve_descriptor = factory.Faker("sentence")
    fees_interchange = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )
    fees_scheme = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=100,
        max_value=20000,
    )


class ZettleBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ZettleBalance

    statement_time = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    payment_time = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    payment_reference = factory.Faker("random_int", min=4000, max=5000)
    description = factory.Faker("sentence")
    amount = factory.Faker("pydecimal", right_digits=2, min_value=500, max_value=3000)
    balance = factory.Faker(
        "pydecimal",
        right_digits=2,
        min_value=5000,
        max_value=30000,
    )


class ZettleReceiptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ZettleReceipt

    zettle_created = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    receipt_number = factory.Faker("random_int", min=4000, max=5000)
    vat = factory.Faker("pydecimal", right_digits=2, min_value=500, max_value=3000)
    total = factory.Faker("pydecimal", right_digits=2, min_value=500, max_value=3000)
    fee = factory.Faker("pydecimal", right_digits=2, min_value=500, max_value=3000)
    net = factory.Faker("pydecimal", right_digits=2, min_value=500, max_value=3000)
    payment_method = factory.Faker(
        "random_element",
        elements=[
            "Cash",
            "Contactless",
            "MobilePay",
            "Chip",
        ],
    )
    card_issuer = factory.Faker(
        "random_element",
        elements=[
            "Mastercard",
            "Visa/Electron",
            "Mastercard",
        ],
    )
    staff = factory.Faker("word")
    description = factory.Faker("sentence")
    sold_via = "POS"


class MobilePayTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MobilePayTransaction

    event = factory.Faker(
        "random_element",
        elements=[
            "Refund",
            "Transfer",
            "Payment",
            "Retainable",
        ],
    )
    currency = "DKK"
    amount = factory.Faker("pydecimal", right_digits=2, min_value=50, max_value=3000)
    mobilepay_created = factory.Faker(
        "date_time_between",
        start_date="-6y",
        tzinfo=timezone.utc,
    )
    comment = factory.Faker("sentence")
    transaction_id = factory.Faker("numerify", text="###E############")
    transfer_id = factory.Faker("numerify", text="####################")
    payment_point = "BornHack 2021"
    myshop_number = "18291"
    bank_account = factory.Faker("numerify", text="####00000######")


class PosFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pos

    team = factory.SubFactory("teams.factories.TeamFactory")
    name = factory.Faker("name")
    external_id = factory.Faker("word")


class ChainFactory(factory.django.DjangoModelFactory):
    """Factory for creating chains."""

    class Meta:
        """Meta."""

        model = Chain

    name = factory.Faker("company")
    slug = factory.LazyAttribute(
        lambda f: unique_slugify(
            f.name,
            Chain.objects.all().values_list("slug", flat=True),
        ),
    )


class CredebtorFactory(factory.django.DjangoModelFactory):
    """Factory for creating Creditors and debitors."""

    class Meta:
        """Meta."""

        model = Credebtor

    chain = factory.SubFactory(ChainFactory)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(
        lambda f: unique_slugify(
            f.name,
            Credebtor.objects.all().values_list("slug", flat=True),
        ),
    )
    address = factory.Faker("address", locale="dk_DK")
    notes = factory.Faker("text")

class ExpenseFactory(factory.django.DjangoModelFactory):
    """Factory for creating expense data."""

    class Meta:
        """Meta."""

        model = Expense

    camp = factory.Faker("random_element", elements=Camp.objects.all())
    creditor = factory.Faker("random_element", elements=Credebtor.objects.all())
    user = factory.Faker("random_element", elements=User.objects.all())
    amount = factory.Faker("random_int", min=20, max=20000)
    description = factory.Faker("text")
    paid_by_bornhack = factory.Faker("random_element", elements=[True, True, False])
    invoice = factory.django.ImageField(
        color=random.choice(["#ff0000", "#00ff00", "#0000ff"]),
    )
    invoice_date = factory.Faker("date")
    responsible_team = factory.Faker("random_element", elements=Team.objects.all())
    approved = factory.Faker("random_element", elements=[True, True, False, None])
    notes = factory.Faker("text")


class RevenueFactory(factory.django.DjangoModelFactory):
    """Factory for creating revenue data."""

    class Meta:
        """Meta."""

        model = Revenue

    camp = factory.Faker("random_element", elements=Camp.objects.all())
    debtor = factory.Faker("random_element", elements=Credebtor.objects.all())
    user = factory.Faker("random_element", elements=User.objects.all())
    amount = factory.Faker("random_int", min=20, max=20000)
    description = factory.Faker("text")
    invoice = factory.django.ImageField(
        color=random.choice(["#ff0000", "#00ff00", "#0000ff"]),
    )
    invoice_date = factory.Faker("date")
    responsible_team = factory.Faker("random_element", elements=Team.objects.all())
    approved = factory.Faker("random_element", elements=[True, True, False])
    notes = factory.Faker("text")

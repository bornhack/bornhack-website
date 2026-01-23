from __future__ import annotations

import csv
import datetime
import io
import logging
import tempfile
from decimal import Decimal
from decimal import InvalidOperation
from os.path import basename
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from camps.utils import get_closest_camp
from economy.models import BankAccount
from economy.models import ClearhausSettlement
from economy.models import CoinifyBalance
from economy.models import CoinifyInvoice
from economy.models import CoinifyPaymentIntent
from economy.models import CoinifyPayout
from economy.models import CoinifySettlement
from economy.models import EpayTransaction
from economy.models import Expense
from economy.models import MobilePayTransaction
from economy.models import Pos
from economy.models import PosProduct
from economy.models import PosProductCost
from economy.models import PosSale
from economy.models import PosTransaction
from economy.models import Reimbursement
from economy.models import Revenue
from economy.models import ZettleBalance
from economy.models import ZettleReceipt
from shop.models import CoinifyAPIPaymentIntent
from shop.models import CreditNote
from shop.models import CustomOrder
from shop.models import Invoice
from shop.models import Order
from zoneinfo import ZoneInfo

# we need the Danish timezone here and there
cph = ZoneInfo("Europe/Copenhagen")
logger = logging.getLogger(f"bornhack.{__name__}")


def import_epay_csv(csvreader):
    """Import an ePay CSV file. Assumes a CSV structure like this:

    "transactionID";"status";"merchantnumber";"orderID";"authamount";"currency";"authdate";"cardtypeID";"CompanyTransactionGroupID";"testTransaction";"FraudControl";"description";"CardHolder";"cardname";"display_short_name";"transaction_group_name";"CurrencyCodeA";"MinorUnit";"CurrencyName";"capturedamount";"creditedAmount";"capturedDate";"creditedDate";"isBooked";"fee";"tcardnumber";"authReferenceNumber"
    "212670400";"2";"1024488";"123";"1200.00";"208";"14-05-2019 19:37";"2";"0";"0";"0";"Order #123";"";"Visa/Dankort";"Visa/Dankort";"";"DKK";"2";"Danish Krone";"1200.00";"0.00";"14-05-2019 19:37";"";"1";"0.00";"098765XXXXXX0987";"20000"
    "213652781";"2";"1024488";"456";"1337.00";"208";"22-05-2019 17:58";"5";"0";"0";"0";"Order #456";"";"Mastercard (udenlandsk)";"MASTERCARD";"";"DKK";"2";"Danish Krone";"1337.00";"0.00";"22-05-2019 17:58";"";"1";"0.00";"543210XXXXXX4321";"20000"
    "214301864";"2";"1024488";"789";"1200.00";"208";"27-05-2019 21:31";"3";"0";"0";"0";"Order #789";"";"Visa/Electron (udenlandsk)";"VISA/ELECTRON";"";"DKK";"2";"Danish Krone";"1200.00";"0.00";"27-05-2019 21:31";"";"1";"0.00";"123456XXXXXX1234";"20000"

    Not all columns are imported. ePay CSV dialect includes a header line, is semicolon seperated, and uses "" for quoting.

    This function expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.
    """
    create_count = 0
    # skip header row
    next(csvreader)
    for row in csvreader:
        et, created = EpayTransaction.objects.get_or_create(
            transaction_id=row[0],
            merchant_id=row[2],
            order_id=row[3],
            auth_amount=Decimal(row[4]),
            currency=row[16],
            auth_date=timezone.make_aware(
                datetime.datetime.strptime(row[6], "%d-%m-%Y %H:%M"),
                timezone=cph,
            ),
            description=row[11],
            card_type=row[13],
            captured_amount=Decimal(row[19]),
            captured_date=timezone.make_aware(
                datetime.datetime.strptime(row[21], "%d-%m-%Y %H:%M"),
                timezone=cph,
            ),
            transaction_fee=row[24],
        )
        if created:
            create_count += 1
    return create_count


class CoinifyCSVImporter:
    @staticmethod
    def import_coinify_payment_intent_csv(csvreader):
        """Import a CSV file from Coinify payment intents exported from there webinterface.

        Assumes a CSV structure like this:
        referenceId,referenceType,merchantId,merchantName,subaccountId,subaccountName,state,stateReason,orderId,customerEmail,requestedAmount,requestedCurrency,createTime,amount,currency
        5166a422-4ac6-4077-8a82-d6b8c5948aea,payment_intent,8bb8d156-f7ad-4c52-9372-a383ae06f8c4,Sandbox Business,,,completed,completed_exact_amount,54,coinifycustomer@example.com,100,DKK,2025-02-15T17:07:50.811Z,100,DKK
        2666cbe3-ff7d-4fa6-aa49-b86784c3ecb4,payment_intent,8bb8d156-f7ad-4c52-9372-a383ae06f8c4,Sandbox Business,,,failed,failed_overpaid,55,coinifycustomer@example.com,100,DKK,2025-02-15T17:14:30.887Z,,

        """
        create_count = 0
        # skip header row
        next(csvreader)
        for row in csvreader:
            ci, created = CoinifyPaymentIntent.objects.get_or_create(
                coinify_id=row[0],
                reference_type=row[1],
                merchant_id=row[2],
                merchant_name=row[3],
                subaccount_id=row[4],
                subaccount_name=row[5],
                state=row[6],
                state_reason=row[7],
                original_order_id=row[8],
                customer_email=row[9],
                requested_amount=Decimal(row[10]),
                requested_currency=row[11],
                coinify_created=datetime.datetime.fromisoformat(row[12]),
                amount=Decimal(row[13]) if row[13] else Decimal(0),
                currency=row[14],
                order=Order.objects.filter(pk=row[8]).first(),
                api_payment_intent=CoinifyAPIPaymentIntent.objects.filter(
                    coinify_id=row[0],
                ).first(),
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def import_coinify_invoice_csv(csvreader):
        """Import a CSV file with Coinify invoices exported from their webinterface.

        Assumes a CSV structure like this:

        id,id_alpha,created,payment_amount,payment_currency,payment_btc_amount,description,custom,credited_amount,credited_currency,state,payment_type,original_payment_id
        54276,sdJGd,"2020-02-06 16:53:51",1234,DKK,0.08345575,"BornHack order id #3527",{},154.94,EUR,complete,normal,
        54018,yfgGh,"2020-01-13 04:17:59",4567,DKK,0.07225667,"BornHack order id #7541",{},761.23,EUR,complete,normal,
        54430,dhdff,"2020-01-08 18:42:27",53459.02,DKK,0.0782233,"BornHack order id #3678",{},0.0782233,BTC,complete,extra,54554
        54448,4mWbd,"2020-01-05 18:27:44",1337,DKK,0.00233121,"BornHack order id #1234",{},178.77,EUR,complete,normal,

        The Coinify CSV dialect includes a header line, is comma seperated, and uses "" for quoting.

        This method expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.
        """
        create_count = 0
        # skip header row
        next(csvreader)
        for row in csvreader:
            ci, created = CoinifyInvoice.objects.get_or_create(
                coinify_id=row[0],
                coinify_id_alpha=row[1],
                coinify_created=timezone.make_aware(
                    datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
                    timezone=datetime.UTC,
                ),
                payment_amount=Decimal(row[3]),
                payment_currency=row[4],
                payment_btc_amount=Decimal(row[5]),
                description=row[6],
                custom=row[7],
                credited_amount=row[8],
                credited_currency=row[9],
                state=row[10],
                payment_type=row[11],
                original_payment_id=row[12] or None,
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def import_coinify_settlements_csv(csvreader):
        """Settlement ID,Account,Gross amount,Fee,Net amount,Payout amount,Create Time."""
        create_count = 0
        next(csvreader)
        for row in csvreader:
            cs, created = CoinifySettlement.objects.get_or_create(
                settlement_id=row[0],
                account=row[1],
                gross_amount=Decimal(row[2]),
                fee=Decimal(row[3]),
                net_amount=Decimal(row[4]),
                payout_amount=Decimal(row[5]),
                create_time=row[6],
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def import_coinify_payout_csv(csvreader):
        """Import a CSV file with Coinify payouts exported from their webinterface.

        Assumes a CSV structure like this:

        id,created,amount,fee,transfer,currency,btc_txid
        124487,"2021-07-14 09:03:03",1116.1,0,1116.1,EUR,
        126509,"2021-08-25 10:59:13",1517.46,0,1517.46,EUR,

        The Coinify CSV dialect includes a header line, is comma seperated, and uses "" for quoting.

        This method expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.
        """
        create_count = 0
        # skip header row
        next(csvreader)
        for row in csvreader:
            ci, created = CoinifyPayout.objects.get_or_create(
                coinify_id=row[0],
                coinify_created=timezone.make_aware(
                    datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"),
                    timezone=datetime.UTC,
                ),
                amount=Decimal(row[2]),
                fee=Decimal(row[3]),
                transferred=Decimal(row[4]),
                currency=row[5],
                btc_txid=row[6] or None,
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def import_coinify_balance_csv(csvreader):
        """Import a CSV file with Coinify balances exported from their webinterface.

        Assumes a CSV structure like this:

        date,BTC,DKK,EUR
        2021-07-05,0.00000000,0.00,0.00
        2021-07-06,0.00000000,0.00,0.00
        2021-07-07,0.00000000,0.00,454.93
        2021-07-08,0.00000000,0.00,454.93
        2021-07-09,0.00000000,0.00,454.93
        2021-07-10,0.00000000,0.00,454.93
        2021-07-11,0.00000000,0.00,454.93
        2021-07-12,0.00000000,0.00,454.93
        2021-07-13,0.00000000,0.00,1116.10
        2021-07-14,0.00000000,0.00,1116.10
        2021-07-15,0.00000000,0.00,0.00
        2021-07-16,0.00000000,0.00,0.00

        The Coinify CSV dialect includes a header line, is comma seperated, and uses "" for quoting.

        This method expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.
        """
        create_count = 0
        # skip header row
        next(csvreader)
        for row in csvreader:
            ci, created = CoinifyBalance.objects.get_or_create(
                date=row[0],
                btc=Decimal(row[1]),
                dkk=Decimal(row[2]),
                eur=Decimal(row[3]),
            )
            if created:
                create_count += 1
        return create_count


def import_clearhaus_csv(csvreader):
    """Import a Clearhaus settlements CSV file. Assumes a CSV structure like this:

    "merchant_id","merchant_name","id","settled","currency","period_start_date","period_end_date","payout_amount","payout_date","summary_sales","summary_credits","summary_refunds","summary_chargebacks","summary_fees","summary_other_postings","summary_net","reserve_amount","reserve_date","fees_sales","fees_refunds","fees_authorisations","fees_credits","fees_minimum_processing","fees_service","fees_wire_transfer","fees_chargebacks","fees_retrieval_requests","payout_reference_number","payout_descriptor","reserve_reference_number","reserve_descriptor","fees_interchange","fees_scheme"
    "1234567","BornHack ApS","abcdef09-1234-5678-90ab-987654332102","false","DKK","2021-08-31","","","","0.00","0.00","0.00","0.00","0.00","0.00","0.00","","","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","","","","","0.00","0.00"
    "1234567","BornHack ApS","abcdef19-1234-5678-90ab-987654332105","true","DKK","2021-08-24","2021-08-30","985.50","2021-09-02","1000.00","0.00","0.00","0.00","-14.50","0.00","985.50","","","-14.50","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","1234567808","CH1234567 2021-09-02","","","0.00","0.00"
    "1234567","BornHack ApS","abcdef29-1234-5678-90ab-987654332104","true","DKK","2021-08-17","2021-08-23","39018.54","2021-08-26","39807.51","0.00","0.00","0.00","-788.97","0.00","39018.54","","","-788.97","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","1234567899","CH1234567 2021-08-26","","","0.00","0.00"

    All columns are imported. Clearhaus CSV dialect includes a header line, is comma seperated, and uses "" for quoting.

    This function expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.
    """
    create_count = 0
    # skip header row
    next(csvreader)
    for row in csvreader:
        # use create_or_update() so we can import CSV with the same settlements and update stuff like payout_date
        cs, created = ClearhausSettlement.objects.update_or_create(
            clearhaus_uuid=row[2],
            defaults={
                "merchant_id": row[0],
                "merchant_name": row[1],
                "settled": row[3] == "true",
                "currency": row[4],
                "period_start_date": row[5],
                "period_end_date": row[6] if row[6] else None,
                "payout_amount": Decimal(row[7]) if row[7] else None,
                "payout_date": row[8] if row[8] else None,
                "summary_sales": Decimal(row[9]),
                "summary_credits": Decimal(row[10]),
                "summary_refunds": Decimal(row[11]),
                "summary_chargebacks": Decimal(row[12]),
                "summary_fees": Decimal(row[13]),
                "summary_other_postings": Decimal(row[14]),
                "summary_net": Decimal(row[15]),
                "reserve_amount": Decimal(row[16]) if row[16] else None,
                "reserve_date": row[17] if row[17] else None,
                "fees_sales": Decimal(row[18]),
                "fees_refunds": Decimal(row[19]),
                "fees_authorisations": Decimal(row[20]),
                "fees_credits": Decimal(row[21]),
                "fees_minimum_processing": Decimal(row[22]),
                "fees_service": Decimal(row[23]),
                "fees_wire_transfer": Decimal(row[24]),
                "fees_chargebacks": Decimal(row[25]),
                "fees_retrieval_requests": Decimal(row[26]),
                "payout_reference_number": row[27] if row[27] else None,
                "payout_descriptor": row[28] if row[28] else None,
                "reserve_reference_number": row[29] if row[29] else None,
                "reserve_descriptor": row[30] if row[30] else None,
                "fees_interchange": Decimal(row[31]),
                "fees_scheme": Decimal(row[32]),
            },
        )
        if created:
            create_count += 1
    return create_count


def optional_int(value):
    if not pd.isnull(value):
        return value
    return None


def to_decimal(value):
    try:
        # converting from float introduces a shitton of decimals
        return round(Decimal(value), 2)
    except ValueError:
        pass


class ZettleExcelImporter:
    @staticmethod
    def load_zettle_receipts_excel(fh):
        """Load an Excel file with Zettle receipts (from POS sales).

        Zettle exports data in Excel files (not CSV), so this importer uses pandas for the file parsing.

        The receipts sheet has 16 rows header and 3 rows footer to skip.
        Also skip columns B (redundant) and J (part of cardnumber).

        Column titles as of September 2025:
        A=Dato
        B=Tid
        C=Kvitteringsnummer
        D=Moms (25.0%)
        E=Total
        F=Afgift
        G=Netto
        H=Betalingsmetode
        I=Hændelsestype
        J=Kortudsteder
        K=Sidste cifre
        L=Personale
        M=Beskrivelse
        N=Solgt via

        """
        return pd.read_excel(
            fh,
            skiprows=16,
            skipfooter=3,
            usecols="A,C:H,J,L:N",
            parse_dates=True,
            dtype={
                "Betalingsmetode": str,  # H
                "Kortudsteder": str,  # J
                "Personale": str,  # L
                "Beskrivelse": str,  # M
                "Solgt via": str,  # N
            },
            converters={
                "Kvitteringsnummer": optional_int,  # C
                "Moms (25.0%)": to_decimal,  # D
                "Total": to_decimal,  # E
                "Afgift": to_decimal,  # F
                "Netto": to_decimal,  # G
            },
        )

    @staticmethod
    def import_zettle_receipts_df(df):
        """Import a pandas dataframe with Zettle receipts (from POS sales)."""
        create_count = 0
        for _index, row in df.iterrows():
            zr, created = ZettleReceipt.objects.get_or_create(
                zettle_created=pd.to_datetime(row["Dato"]).replace(tzinfo=cph),
                receipt_number=row["Kvitteringsnummer"],
                vat=row["Moms (25.0%)"],
                total=row["Total"],
                fee=row["Afgift"],
                net=row["Netto"],
                payment_method=row["Betalingsmetode"],
                card_issuer=(row["Kortudsteder"] if not pd.isnull(row["Kortudsteder"]) else None),
                staff=row["Personale"],
                description=row["Beskrivelse"],
                sold_via=row["Solgt via"],
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def load_zettle_balances_excel(fh):
        """Load an Excel file with Zettle balances and account movements.

        Zettle exports data in Excel files (not CSV), so this importer uses pandas for the file parsing.

        The balances sheet has no header or footer rows, and no columns to skip.

        Column titles as of September 2025:
          A=Afregningsdato
          B=Betalingsdato
          C=Reference
          D=Type
          E=Netto
          F=Saldo
        """
        return pd.read_excel(
            fh,
            parse_dates=True,
            dtype={
                "Type": str,  # D
            },
            converters={
                "Reference": optional_int,  # C
                "Netto": to_decimal,  # E
                "Saldo": to_decimal,  # F
            },
        )

    @staticmethod
    def import_zettle_balances_df(df):
        """Import a pandas dataframe with Zettle account statements and balances."""
        create_count = 0
        for _index, row in df.iterrows():
            # create balance
            zb, created = ZettleBalance.objects.get_or_create(
                statement_time=timezone.make_aware(row["Afregningsdato"], timezone=cph),
                payment_time=(
                    timezone.make_aware(row["Betalingsdato"], timezone=cph)
                    if not pd.isnull(row["Betalingsdato"])
                    else None
                ),
                payment_reference=(row["Reference"] if not pd.isnull(row["Reference"]) else None),
                description=row["Type"],
                amount=row["Netto"],
                balance=row["Saldo"],
            )
            if created:
                create_count += 1
        return create_count


class MobilePayCSVImporter:
    @staticmethod
    def import_mobilepay_transfer_csv(csvreader):
        """Import a CSV file with MobilePay transactions.

        Assumes a CSV structure like in testdata/MobilePay_Transfer_overview_csv_MyShop_25-08-2021_14-09-2021.csv with these headers:

        Event;Currency;Amount;Date and time;Customer name;MP-number;Comment;TransactionID;TransferID;Payment point;MyShop-Number;Bank account;Date;Time

        The MobilePay CSV dialect includes a header line, is semicolon seperated, and uses "" for quoting. Numbers use comma for decimal seperator so we replace with .

        This method expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.

        We skip the columns with Customer name, MP-number and the last two date/time columns (redundant)
        """
        create_count = 0
        # skip header row
        next(csvreader)
        for row in csvreader:
            mt, created = MobilePayTransaction.objects.get_or_create(
                event=row[0],
                currency=row[1],
                amount=Decimal(row[2].replace(",", ".")),
                mobilepay_created=row[3],
                comment=row[6],
                transaction_id=row[7] or None,
                payment_point=row[9],
                myshop_number=row[10],
                defaults={
                    "transfer_id": row[8] or None,
                    "bank_account": row[11],
                },
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def import_mobilepay_sales_csv(csvreader):
        """Import a CSV file with MobilePay sales and refunds. The sales CSV may contain transactions
        which are not yet included in a transfer (bank payout) so they do not show up in the
        transfers CSV yet.

        Assumes a CSV structure like in testdata/MobilePay_Sales_overview_csv_MyShop_25-08-2021_14-09-2021.csv with these headers, it is identical to the transfers CSV except the "TransferID" and "Bank account" columns are missing:

        Event;Currency;Amount;Date and time;Customer name;MP-number;Comment;TransactionID;Payment point;MyShop-Number;Date;Time

        The MobilePay CSV dialect includes a header line, is semicolon seperated, and uses "" for quoting. Numbers use comma for decimal seperator so we replace with .

        This method expects an initiated csvreader object, or alternatively some other iterable with the data in the right index locations.

        We skip the columns with Customer name, MP-number and the last two date/time columns (redundant)
        """
        create_count = 0
        # skip header row
        next(csvreader)
        for row in csvreader:
            mt, created = MobilePayTransaction.objects.get_or_create(
                event=row[0],
                currency=row[1],
                amount=Decimal(row[2].replace(",", ".")),
                mobilepay_created=row[3],
                comment=row[6],
                transaction_id=row[7] or None,
                payment_point=row[8],
                myshop_number=row[9],
                defaults={
                    "transfer_id": None,
                    "bank_account": None,
                },
            )
            if created:
                create_count += 1
        return create_count


class AccountingExporter:
    """A class with methods for exporting all the financial data for the bookkeeper."""

    def __init__(self, startdate, enddate) -> None:
        """Requires startdate and enddate."""
        self.period = DateTimeTZRange(startdate, enddate)

    def doit(self) -> None:
        """Do all the things."""
        with tempfile.TemporaryDirectory(prefix="django-accounting-") as tmpdir:
            workdir = Path(tmpdir)
            # bank
            self.bankaccounts = self.bank_csv_export(workdir)
            # website stuff
            self.paid_invoices = self.invoice_csv_export(workdir, paid=True)
            self.unpaid_invoices = self.invoice_csv_export(workdir, paid=False)
            self.paid_creditnotes = self.creditnote_csv_export(workdir, paid=True)
            self.unpaid_creditnotes = self.creditnote_csv_export(workdir, paid=False)
            self.orders = self.shoporder_csv_export(workdir)
            self.customorders = self.customorder_csv_export(workdir)
            self.expenses = self.expense_csv_export(workdir)
            self.revenues = self.revenue_csv_export(workdir)
            self.reimbursements = self.reimbursement_csv_export(workdir)
            self.pos = self.pos_csv_export(workdir)
            # PSPs
            self.coinify = self.coinify_csv_export(workdir)
            self.epay = self.epay_csv_export(workdir)
            self.clearhaus = self.clearhaus_csv_export(workdir)
            self.zettle = self.zettle_csv_export(workdir)
            self.mobilepay = self.mobilepay_csv_export(workdir)
            # wrap up
            self.create_index_html(workdir)
            self.create_archive(workdir)

    def bank_csv_export(self, workdir):
        """Export bank accounting data in CSV files."""
        files = []
        for ba in (
            BankAccount.objects.all()
            .exclude(start_date__gte=self.period.upper)
            .exclude(end_date__lte=self.period.lower)
        ):
            files.append(ba.export_csv(self.period, workdir))
        return files

    def invoice_csv_export(self, workdir, paid=True, filename=None):
        """Export invoices in our system."""
        if not filename:
            paid_str = "paid" if paid else "unpaid"
            filename = f"bornhack_{paid_str}_invoices_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                ["invoice_date", "invoice_number", "order", "amount", "vat"],
            )
            invoices = Invoice.objects.filter(
                created__gte=self.period.lower,
                created__lte=self.period.upper,
            )
            count = 0
            for invoice in invoices:
                if invoice.get_order.paid != paid:
                    continue
                if invoice.order:
                    amount = invoice.order.total
                    vat = True
                else:
                    amount = invoice.customorder.amount
                    vat = invoice.customorder.danish_vat
                writer.writerow(
                    [
                        invoice.created.date(),
                        invoice.id,
                        invoice.get_order,
                        amount,
                        vat,
                    ],
                )
                count += 1
        return (filename, count)

    def creditnote_csv_export(self, workdir, paid=True, filename=None):
        """Export creditnotes in our system."""
        if not filename:
            paid_str = "paid" if paid else "unpaid"
            filename = f"bornhack_{paid_str}_creditnotes_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "creditnote_date",
                    "creditnote_number",
                    "customer",
                    "text",
                    "amount",
                    "vat",
                ],
            )
            creditnotes = CreditNote.objects.filter(
                paid=paid,
                created__gte=self.period.lower,
                created__lte=self.period.upper,
            )
            for creditnote in creditnotes:
                writer.writerow(
                    [
                        creditnote.created.date(),
                        creditnote.id,
                        creditnote.user if creditnote.user else creditnote.customer,
                        creditnote.text,
                        creditnote.amount,
                        creditnote.danish_vat,
                    ],
                )
        return (filename, creditnotes.count())

    def shoporder_csv_export(self, workdir, filename=None):
        """Export webshop orders in our system. Only paid orders are interesting for accounting."""
        if not filename:
            filename = f"bornhack_paid_webshop_orders_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "id",
                    "amount",
                    "vat",
                    "payment_method",
                    "cancelled",
                    "refunded",
                    "notes",
                    "invoice",
                ],
            )
            orders = Order.objects.filter(
                paid=True,
                created__gte=self.period.lower,
                created__lte=self.period.upper,
            )
            for order in orders:
                invoiceid = order.invoice.id if order.invoice else "N/A"
                writer.writerow(
                    [
                        order.id,
                        order.total,
                        True,
                        order.payment_method,
                        order.cancelled,
                        order.refunded,
                        order.notes,
                        invoiceid,
                    ],
                )
        return (filename, orders.count())

    def customorder_csv_export(self, workdir, filename=None):
        """Export customorders in our system."""
        if not filename:
            filename = f"bornhack_custom_orders_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(["id", "amount", "vat", "paid", "customer"])
            orders = CustomOrder.objects.filter(
                created__gte=self.period.lower,
                created__lte=self.period.upper,
            )
            for order in orders:
                writer.writerow(
                    [
                        order.id,
                        order.amount,
                        order.danish_vat,
                        order.paid,
                        order.customer,
                    ],
                )
        return (filename, orders.count())

    def expense_csv_export(self, workdir, filename=None):
        """Export expenses in our system."""
        if not filename:
            filename = f"bornhack_expenses_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "uuid",
                    "camp",
                    "creating_user",
                    "creditor",
                    "amount",
                    "description",
                    "paid_by_bornhack",
                    "invoice",
                    "invoice_date",
                    "reimbursement",
                    "notes",
                ],
            )
            expenses = Expense.objects.filter(
                invoice_date__gte=self.period.lower,
                invoice_date__lte=self.period.upper,
            )
            for expense in expenses:
                writer.writerow(
                    [
                        expense.uuid,
                        expense.camp.title,
                        expense.user,
                        expense.creditor,
                        expense.amount,
                        expense.description,
                        expense.paid_by_bornhack,
                        expense.invoice.path,
                        expense.invoice_date,
                        expense.reimbursement,
                        expense.notes,
                    ],
                )
        return (filename, expenses.count())

    def revenue_csv_export(self, workdir, filename=None):
        """Export revenues in our system."""
        if not filename:
            filename = f"bornhack_revenues_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "uuid",
                    "camp",
                    "creating_user",
                    "debtor",
                    "amount",
                    "description",
                    "invoice",
                    "invoice_date",
                    "notes",
                ],
            )
            revenues = Revenue.objects.filter(
                invoice_date__gte=self.period.lower,
                invoice_date__lte=self.period.upper,
            )
            for revenue in revenues:
                writer.writerow(
                    [
                        revenue.uuid,
                        revenue.camp.title,
                        revenue.user,
                        revenue.debtor,
                        revenue.amount,
                        revenue.description,
                        revenue.invoice.path,
                        revenue.invoice_date,
                        revenue.notes,
                    ],
                )
        return (filename, revenues.count())

    def reimbursement_csv_export(self, workdir, filename=None):
        """Export reimbursements in our system."""
        if not filename:
            filename = f"bornhack_reimbursements_{self.period.lower}_{self.period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "uuid",
                    "created_by",
                    "created_for",
                    "notes",
                    "paid",
                    "covered_expenses",
                    "payback_expense",
                ],
            )
            count = 0
            for reimbursement in Reimbursement.objects.filter(paid=True):
                if not reimbursement.payback_expense:
                    continue
                if reimbursement.payback_expense.invoice_date < self.period.lower:
                    continue
                if reimbursement.payback_expense.invoice_date > self.period.upper:
                    continue
                writer.writerow(
                    [
                        reimbursement.uuid,
                        reimbursement.user,
                        reimbursement.reimbursement_user,
                        reimbursement.notes,
                        reimbursement.paid,
                        reimbursement.expenses.exclude(
                            paid_by_bornhack=True,
                        ).values_list("uuid", flat=True),
                        reimbursement.payback_expense.uuid,
                    ],
                )
                count += 1
        return (filename, count)

    def pos_csv_export(self, workdir):
        """Export PoS data in CSV files."""
        files = []
        for pos in Pos.objects.filter(pos_reports__period__overlap=self.period):
            files.append(pos.export_csv(self.period, workdir))
        return files

    def coinify_csv_export(self, workdir):
        """Export coinify data in our system. Three different CSV files is created."""
        # invoices
        invoices_filename = f"bornhack_coinify_invoices_{self.period.lower}_{self.period.upper}.csv"
        invoices = CoinifyInvoice.objects.filter(
            coinify_created__gte=self.period.lower,
            coinify_created__lte=self.period.upper,
        )
        with open(workdir / invoices_filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "coinify_id",
                    "coinify_id_alpha",
                    "coinify_created",
                    "payment_amount",
                    "payment_currency",
                    "payment_btc_amount",
                    "description",
                    "credited_amount",
                    "credited_currency",
                    "state",
                    "payment_type",
                    "original_payment_id",
                ],
            )
            for ci in invoices:
                writer.writerow(
                    [
                        ci.pk,
                        ci.coinify_id,
                        ci.coinify_id_alpha,
                        ci.coinify_created,
                        ci.payment_amount,
                        ci.payment_currency,
                        ci.payment_btc_amount,
                        ci.description,
                        ci.credited_amount,
                        ci.credited_currency,
                        ci.state,
                        ci.payment_type,
                        ci.original_payment_id,
                    ],
                )

        # payouts
        payouts_filename = f"bornhack_coinify_payouts_{self.period.lower}_{self.period.upper}.csv"
        payouts = CoinifyPayout.objects.filter(
            coinify_created__gte=self.period.lower,
            coinify_created__lte=self.period.upper,
        )
        with open(workdir / payouts_filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "coinify_id",
                    "coinify_created",
                    "amount",
                    "fee",
                    "transferred",
                    "currency",
                    "amount_dkk",
                    "fee_dkk",
                    "transferred_dkk",
                ],
            )
            for cp in payouts:
                writer.writerow(
                    [
                        cp.pk,
                        cp.coinify_id,
                        cp.coinify_created,
                        cp.amount,
                        cp.fee,
                        cp.transferred,
                        cp.currency,
                        cp.amount_dkk,
                        cp.fee_dkk,
                        cp.transferred_dkk,
                    ],
                )

        # balances
        balances_filename = f"bornhack_coinify_balances_{self.period.lower}_{self.period.upper}.csv"
        balances = CoinifyBalance.objects.filter(
            date__gte=self.period.lower,
            date__lte=self.period.upper,
        )
        with open(workdir / balances_filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "date",
                    "btc",
                    "dkk",
                    "eur",
                ],
            )
            for balance in balances:
                writer.writerow(
                    [balance.pk, balance.date, balance.btc, balance.dkk, balance.eur],
                )
        return (
            (balances_filename, balances.count()),
            (payouts_filename, payouts.count()),
            (invoices_filename, invoices.count()),
        )

    def epay_csv_export(self, workdir):
        """Export ePay/bambora transactions in our system."""
        filename = f"bornhack_epay_transactions_{self.period.lower}_{self.period.upper}.csv"
        transactions = EpayTransaction.objects.filter(
            auth_date__gte=self.period.lower,
            auth_date__lte=self.period.upper,
        )
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "merchant_id",
                    "transaction_id",
                    "order_id",
                    "currency",
                    "auth_date",
                    "auth_amount",
                    "captured_date",
                    "captured_amount",
                    "card_type",
                    "description",
                    "transaction_fee",
                ],
            )
            for et in transactions:
                writer.writerow(
                    [
                        et.pk,
                        et.merchant_id,
                        et.transaction_id,
                        et.order_id,
                        et.currency,
                        et.auth_date,
                        et.auth_amount,
                        et.captured_date,
                        et.captured_amount,
                        et.card_type,
                        et.description,
                        et.transaction_fee,
                    ],
                )
        return (filename, transactions.count())

    def clearhaus_csv_export(self, workdir):
        """Export Clearhaus settlements in our system."""
        filename = f"bornhack_clearhaus_settlements_{self.period.lower}_{self.period.upper}.csv"
        settlements = ClearhausSettlement.objects.filter(
            payout_date__gte=self.period.lower,
            payout_date__lte=self.period.upper,
        )
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "merchant_id",
                    "merchant_name",
                    "clearhaus_uuid",
                    "settled",
                    "currency",
                    "period_start_date",
                    "period_end_date",
                    "payout_amount",
                    "payout_date",
                    "summary_sales",
                    "summary_credits",
                    "summary_refunds",
                    "summary_chargebacks",
                    "summary_fees",
                    "summary_other_postings",
                    "summary_net",
                    "reserve_amount",
                    "reserve_date",
                    "fees_sales",
                    "fees_refunds",
                    "fees_authorisations",
                    "fees_credits",
                    "fees_minimum_processing",
                    "fees_service",
                    "fees_wire_transfer",
                    "fees_chargebacks",
                    "fees_retrieval_requests",
                    "payout_reference_number",
                    "payout_descriptor",
                    "reserve_reference_number",
                    "reserve_descriptor",
                    "fees_interchange",
                    "fees_scheme",
                ],
            )
            for s in settlements:
                writer.writerow(
                    [
                        s.pk,
                        s.merchant_id,
                        s.merchant_name,
                        s.clearhaus_uuid,
                        s.settled,
                        s.currency,
                        s.period_start_date,
                        s.period_end_date,
                        s.payout_amount,
                        s.payout_date,
                        s.summary_sales,
                        s.summary_credits,
                        s.summary_refunds,
                        s.summary_chargebacks,
                        s.summary_fees,
                        s.summary_other_postings,
                        s.summary_net,
                        s.reserve_amount,
                        s.reserve_date,
                        s.fees_sales,
                        s.fees_refunds,
                        s.fees_authorisations,
                        s.fees_credits,
                        s.fees_minimum_processing,
                        s.fees_service,
                        s.fees_wire_transfer,
                        s.fees_chargebacks,
                        s.fees_retrieval_requests,
                        s.payout_reference_number,
                        s.payout_descriptor,
                        s.reserve_reference_number,
                        s.reserve_descriptor,
                        s.fees_interchange,
                        s.fees_scheme,
                    ],
                )
        return (filename, settlements.count())

    def zettle_csv_export(self, workdir):
        """Export Zettle data in our system. Two different CSV files will be created."""
        # balances
        balances_filename = f"bornhack_zettle_balances_{self.period.lower}_{self.period.upper}.csv"
        balances = ZettleBalance.objects.filter(
            statement_time__gte=self.period.lower,
            statement_time__lte=self.period.upper,
        )
        with open(workdir / balances_filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "statement_time",
                    "payment_time",
                    "payment_reference",
                    "description",
                    "amount",
                    "balance",
                ],
            )
            for balance in balances:
                writer.writerow(
                    [
                        balance.pk,
                        balance.statement_time,
                        balance.payment_reference,
                        balance.description,
                        balance.amount,
                        balance.balance,
                    ],
                )

        # receipts
        receipts_filename = f"bornhack_zettle_receipts_{self.period.lower}_{self.period.upper}.csv"
        receipts = ZettleReceipt.objects.filter(
            zettle_created__gte=self.period.lower,
            zettle_created__lte=self.period.upper,
        )
        with open(workdir / receipts_filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "zettle_created",
                    "receipt_number",
                    "vat",
                    "total",
                    "fee",
                    "net",
                    "payment_method",
                    "card_issuer",
                    "staff",
                    "description",
                    "sold_via",
                ],
            )
            for re in receipts:
                writer.writerow(
                    [
                        re.pk,
                        re.zettle_created,
                        re.receipt_number,
                        re.vat,
                        re.total,
                        re.fee,
                        re.net,
                        re.payment_method,
                        re.card_issuer,
                        re.staff,
                        re.description,
                        re.sold_via,
                    ],
                )

        return (
            (balances_filename, balances.count()),
            (receipts_filename, receipts.count()),
        )

    def mobilepay_csv_export(self, workdir):
        """Export MobilePay transactions in our system."""
        filename = f"bornhack_mobilepay_transactions_{self.period.lower}_{self.period.upper}.csv"
        transactions = MobilePayTransaction.objects.filter(
            mobilepay_created__gte=self.period.lower,
            mobilepay_created__lte=self.period.upper,
        )
        with open(workdir / filename, "w", newline="") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "event",
                    "currency",
                    "amount",
                    "mobilepay_created",
                    "comment",
                    "transaction_id",
                    "transfer_id",
                    "payment_point",
                    "myshop_number",
                    "bank_account",
                ],
            )
            for mt in transactions:
                writer.writerow(
                    [
                        mt.pk,
                        mt.event,
                        mt.currency,
                        mt.amount,
                        mt.mobilepay_created,
                        mt.comment,
                        mt.transaction_id,
                        mt.transfer_id,
                        mt.payment_point,
                        mt.myshop_number,
                        mt.bank_account,
                    ],
                )
        return (filename, transactions.count())

    def create_index_html(self, workdir) -> None:
        """Create a HTML file with links for everything."""
        context = {
            "period": self.period,
            "bankaccounts": self.bankaccounts,
            "paid_invoices": self.paid_invoices,
            "unpaid_invoices": self.unpaid_invoices,
            "paid_creditnotes": self.paid_creditnotes,
            "unpaid_creditnotes": self.unpaid_creditnotes,
            "orders": self.orders,
            "customorders": self.customorders,
            "expenses": self.expenses,
            "revenues": self.revenues,
            "reimbursements": self.reimbursements,
            "coinify": self.coinify,
            "epay": self.epay,
            "clearhaus": self.clearhaus,
            "zettle": self.zettle,
            "mobilepay": self.mobilepay,
        }
        rendered = render_to_string("accounting_export.html", context)
        with open(workdir / "index.html", "w") as f:
            f.write(rendered)

    def create_archive(self, workdir) -> None:
        """Create an in-memory zip-file with all the CSV data and the HTML file."""
        self.archivedata = io.BytesIO()
        subdir = "bornhack_accounting_export"
        with ZipFile(self.archivedata, "w") as zh:
            # add everything in the workdir
            for filename in workdir.glob("*"):
                zh.write(filename, f"{subdir}/{basename(filename)}")
            # add support files for styling
            for filepath in [
                "css/bootstrap.min.css",
                "css/jquery.dataTables.1.10.20.min.css",
                "js/jquery-3.3.1.min.js",
                "js/jquery.dataTables.1.10.20.min.js",
                "js/bootstrap.min.js",
            ]:
                # generate an absolute path
                fullpath = Path(settings.BASE_DIR) / "static_src" / filepath
                zh.write(fullpath, f"{subdir}/{basename(fullpath)}")


def import_pos_sales_json(transactions):
    """Importer for sales details from the Pos system.

    Expects a list of dicts like so:

        {'_id': 'eKCFbcn6fvi5eaTJJ', 'userId': 'Y7NgNzTJRxPKupCv5', 'locationId': 'bTasxE2YYXZh35wtQ', 'currency': 'HAX', 'country': 'DK', 'amount': 55, 'timestamp': {'$date': '2021-08-23T18:11:05.379Z'}, 'products': [{'_id': '7oCSE2xt6szw5cZYQ', 'createdAt': {'$date': '2021-08-21T13:41:32.073Z'}, 'brandName': 'Gamma', 'name': 'Tap: Bando', 'description': 'IPA', 'salePrice': '35', 'unitSize': '40', 'sizeUnit': 'cl', 'abv': '6.5', 'tags': ['beer', 'tap'], 'shopPrices': [{'buyPrice': 17.5, 'timestamp': {'$date': '2021-08-21T13:41:32.073Z'}}], 'locationIds': ['bTasxE2YYXZh35wtQ'], 'updatedAt': {'$date': '2021-08-23T11:27:05.459Z'}, 'tap': '1'}, {'_id': 'Z4ZxsPPEDfDbTLHsz', 'createdAt': {'$date': '2021-08-21T13:27:25.47Z'}, 'brandName': 'Vestfyen', 'name': 'Tap: Pilsner', 'description': '', 'salePrice': '20', 'unitSize': '40', 'sizeUnit': 'cl', 'abv': '4.6', 'tags': ['tap', 'beer'], 'shopPrices': [{'buyPrice': 8.65, 'timestamp': {'$date': '2021-08-21T13:27:25.471Z'}}], 'tap': '2', 'updatedAt': {'$date': '2021-08-23T14:46:27.259Z'}, 'locationIds': ['bTasxE2YYXZh35wtQ']}]}

    """
    new_transactions = 0
    new_products = 0
    new_sales = 0
    new_costs = 0
    # loop over transactions
    logger.info(f"Importing {len(transactions)} transactions...")
    for tx in transactions:
        # parse timestamp
        try:
            # with ms
            timestamp = datetime.datetime.strptime(
                tx["timestamp"]["$date"],
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ).replace(tzinfo=datetime.UTC)
        except ValueError:
            # without ms
            timestamp = datetime.datetime.strptime(
                tx["timestamp"]["$date"],
                "%Y-%m-%dT%H:%M:%SZ",
            ).replace(tzinfo=datetime.UTC)
        # find the Pos related to the camp during which the transaction happened
        camp = get_closest_camp(timestamp)
        pos = Pos.objects.get(
            external_id=tx["locationId"],
            team__camp=camp,
        )

        # create or get the transaction
        transaction, created = PosTransaction.objects.get_or_create(
            external_transaction_id=tx["_id"],
            defaults={
                "pos": pos,
                "external_user_id": tx.get("userId", ""),
                "timestamp": timestamp,
            },
        )
        if not created:
            continue
        new_transactions += 1
        logger.debug(
            f"Found new transaction with txid {transaction.external_transaction_id} as PosTransaction {transaction.pk} - importing products and sales...",
        )
        # loop over each sale in the transaction
        for sale in tx["products"]:
            if sale["salePrice"] == 0:
                # skip sales where the sales_price is 0, these are typically pre-sold special
                # event sales like for birthdays and weddings
                continue
            # get abv when possible
            try:
                abv = Decimal(str(sale.get("abv", 0)))
            except (ValueError, InvalidOperation):
                # handle stuff like 'abv': {'$numberDouble': 'NaN'}
                abv = 0
            # get tags (sometimes a list and sometimes a comma seperated string, we want the latter)
            tags = sale.get("tags", [])
            if isinstance(tags, list):
                tags = ",".join(tags)
            # create or update the PosProduct
            product, created = PosProduct.objects.update_or_create(
                external_id=sale["_id"],
                defaults={
                    "brand_name": sale["brandName"],
                    "name": sale["name"],
                    "description": sale.get("description", ""),
                    "sales_price": int(sale["salePrice"]),
                    "unit_size": Decimal(sale["unitSize"]),
                    "size_unit": sale["sizeUnit"],
                    "abv": abv,
                    "tags": tags,
                },
            )
            if created:
                logger.debug(
                    f"Created new product {product.external_id} as PosProduct {product.pk}: {product.brand_name} - {product.name}",
                )
                new_products += 1
            # create PosProductCost objects
            if "shopPrices" in sale:
                for cost in sale["shopPrices"]:
                    # parse timestamp
                    try:
                        # with ms
                        timestamp = datetime.datetime.strptime(
                            cost["timestamp"]["$date"],
                            "%Y-%m-%dT%H:%M:%S.%fZ",
                        ).replace(tzinfo=datetime.UTC)
                    except ValueError:
                        # without ms
                        timestamp = datetime.datetime.strptime(
                            cost["timestamp"]["$date"],
                            "%Y-%m-%dT%H:%M:%SZ",
                        ).replace(tzinfo=datetime.UTC)
                    camp = get_closest_camp(timestamp)
                    # parse price
                    try:
                        price = Decimal(str(round(cost["buyPrice"], 2)))
                    except (ValueError, InvalidOperation, TypeError):
                        # skip stuff like 'abv': {'$numberDouble': 'NaN'}
                        continue
                    # create cost as needed
                    cost, created = PosProductCost.objects.get_or_create(
                        camp=camp,
                        product=product,
                        timestamp=timestamp,
                        product_cost=price,
                    )
                    if created:
                        logger.debug(
                            f"Created new PosProductCost object {cost.pk} for product {product} at price {cost.product_cost}",
                        )
                        new_costs += 1

            # create the PosSale object
            possale = PosSale.objects.create(
                transaction=transaction,
                product=product,
                sales_price=int(sale["salePrice"]),
            )
            new_sales += 1
            logger.debug(
                f"Created new PosSale {possale.pk} for PosProduct {product.brand_name} - {product.name} sold for {possale.sales_price} HAX",
            )
    # all done
    return new_products, new_transactions, new_sales, new_costs

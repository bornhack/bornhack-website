from __future__ import annotations

import csv

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Bank
from .models import BankAccount
from .utils import CoinifyCSVImporter
from .utils import MobilePayCSVImporter
from .utils import ZettleExcelImporter
from .utils import import_clearhaus_csv
from .utils import import_epay_csv


class BankAccountCsvImportTest(TestCase):
    """Test importing a CSV file with bank transactions."""

    def test_bank_account_csv_import(self):
        bank = Bank.objects.create(
            name="NiceBank",
        )
        account = BankAccount.objects.create(
            bank=bank,
            name="kasse",
            reg_no="1234",
            account_no="12345678",
        )

        # make sure we create 6 transactions
        with open("testdata/bank.csv", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = account.import_csv(reader)
            self.assertEqual(created, 6)

        # make sure we create 0 if we load the same file again
        with open("testdata/bank.csv", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = account.import_csv(reader)
            self.assertEqual(created, 0)

        # make sure we refuse transactions before start_date of the account
        account.transactions.all().delete()
        account.start_date = timezone.now()
        account.save()
        with self.assertRaises(
            ValidationError,
            msg="Transaction on 2021-09-01 is before the bank accounts start_date. Transaction text is 'c051c94d-0762-422b-a453-e14402' and amount is -250.00",
        ):
            with open("testdata/bank.csv", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=";", quotechar='"')
                created = account.import_csv(reader)


class CoinifyCSVImportTest(TestCase):
    def test_coinify_invoice_csv_import(self):
        # make sure we create 4 invoices
        with open(
            "testdata/coinify-invoices-20200101-20200630.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_invoice_csv(reader)
            self.assertEqual(created, 4)

        # make sure we create 0 invoices if the same csv is imported again
        with open(
            "testdata/coinify-invoices-20200101-20200630.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_invoice_csv(reader)
            self.assertEqual(created, 0)

    def test_coinify_payout_csv_import(self):
        # make sure we create 2 payouts
        with open(
            "testdata/coinify-payouts-20210701-20210904.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_payout_csv(reader)
            self.assertEqual(created, 2)

        # make sure we create 0 payouts if the same csv is imported again
        with open(
            "testdata/coinify-payouts-20210701-20210904.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_payout_csv(reader)
            self.assertEqual(created, 0)

    def test_coinify_balance_csv_import(self):
        # make sure we create 66 balances
        with open(
            "testdata/coinify-account-balances-20210701-20210904.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_balance_csv(reader)
            self.assertEqual(created, 66)

        # make sure we create 0 balances if the same csv is imported again
        with open(
            "testdata/coinify-account-balances-20210701-20210904.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_balance_csv(reader)
            self.assertEqual(created, 0)


class EpayCSVImportTest(TestCase):
    def test_epay_csv_import(self):
        # make sure we create 4 epay transactions
        with open("testdata/epay_test.csv", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = import_epay_csv(reader)
            self.assertEqual(created, 3)

        # make sure we create 0 if the same csv is imported again
        with open("testdata/epay_test.csv", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = import_epay_csv(reader)
            self.assertEqual(created, 0)


class ClearhausCSVImportTest(TestCase):
    def test_clearhaus_csv_import(self):
        # make sure we create 10 clearhaus settlements
        with open("testdata/clearhaus_settlements.csv", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = import_clearhaus_csv(reader)
            self.assertEqual(created, 9)

        # make sure we create 0 if the same csv is imported again
        with open("testdata/clearhaus_settlements.csv", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            created = import_clearhaus_csv(reader)
            self.assertEqual(created, 0)


class ZettleImportTest(TestCase):
    def test_zettle_receipts_import(self):
        with open("testdata/Zettle-Receipts-Report-20210101-20210910.xlsx", "rb") as f:
            df = ZettleExcelImporter.load_zettle_receipts_excel(f)
        created = ZettleExcelImporter.import_zettle_receipts_df(df)
        self.assertEqual(created, 6)
        # import the same df again to make sure we don't create duplicates
        created = ZettleExcelImporter.import_zettle_receipts_df(df)
        self.assertEqual(created, 0)

    def test_zettle_balances_import(self):
        with open("testdata/Zettle-Account-Statement-Report-20230901-20250903.xlsx", "rb") as f:
            df = ZettleExcelImporter.load_zettle_balances_excel(f)
        created = ZettleExcelImporter.import_zettle_balances_df(df)
        self.assertEqual(created, 4059)
        # import the same df again to make sure we don't create duplicates
        created = ZettleExcelImporter.import_zettle_balances_df(df)
        self.assertEqual(created, 0)


class MobilePayImportTest(TestCase):
    def test_mobilepay_import(self):
        with open(
            "testdata/MobilePay_Transfer_overview_csv_MyShop_25-08-2021_14-09-2021.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = MobilePayCSVImporter.import_mobilepay_transfer_csv(reader)
            self.assertEqual(created, 8)

        # make sure we create 0 if the same csv is imported again
        with open(
            "testdata/MobilePay_Transfer_overview_csv_MyShop_25-08-2021_14-09-2021.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = MobilePayCSVImporter.import_mobilepay_transfer_csv(reader)
            self.assertEqual(created, 0)

        # now test importing sales CSV, 3 out of 4 lines are already in from above import
        with open(
            "testdata/MobilePay_Sales_overview_csv_MyShop_25-08-2021_14-09-2021.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = MobilePayCSVImporter.import_mobilepay_sales_csv(reader)
            # the CSV contains three sales and a refund but the sales are already in the db
            self.assertEqual(
                created,
                1,
                "more than 1 new mobilepay tx was created, something is fucky",
            )
        # make sure we create 0 if the same csv is imported again
        with open(
            "testdata/MobilePay_Sales_overview_csv_MyShop_25-08-2021_14-09-2021.csv",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.reader(f, delimiter=";", quotechar='"')
            created = MobilePayCSVImporter.import_mobilepay_sales_csv(reader)
            self.assertEqual(created, 0)

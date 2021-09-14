from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytz
from django.utils import timezone

from economy.models import (
    ClearhausSettlement,
    CoinifyBalance,
    CoinifyInvoice,
    CoinifyPayout,
    EpayTransaction,
    MobilePayTransaction,
    ZettleBalance,
    ZettleReceipt,
)

# we need the Danish timezone here and there
cph = pytz.timezone("Europe/Copenhagen")


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
                datetime.strptime(row[6], "%d-%m-%Y %H:%M"),
                timezone=cph,
            ),
            description=row[11],
            card_type=row[13],
            captured_amount=Decimal(row[19]),
            captured_date=timezone.make_aware(
                datetime.strptime(row[21], "%d-%m-%Y %H:%M"),
                timezone=cph,
            ),
            transaction_fee=row[24],
        )
        if created:
            create_count += 1
    return create_count


class CoinifyCSVImporter:
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
                    datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
                    timezone=timezone.utc,
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
                    datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"),
                    timezone=timezone.utc,
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
    "1234567","BornHack IVS","abcdef09-1234-5678-90ab-987654332102","false","DKK","2021-08-31","","","","0.00","0.00","0.00","0.00","0.00","0.00","0.00","","","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","","","","","0.00","0.00"
    "1234567","BornHack IVS","abcdef19-1234-5678-90ab-987654332105","true","DKK","2021-08-24","2021-08-30","985.50","2021-09-02","1000.00","0.00","0.00","0.00","-14.50","0.00","985.50","","","-14.50","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","1234567808","CH1234567 2021-09-02","","","0.00","0.00"
    "1234567","BornHack IVS","abcdef29-1234-5678-90ab-987654332104","true","DKK","2021-08-17","2021-08-23","39018.54","2021-08-26","39807.51","0.00","0.00","0.00","-788.97","0.00","39018.54","","","-788.97","0.00","0.00","0.00","0.00","0.00","0.00","0.00","0.00","1234567899","CH1234567 2021-08-26","","","0.00","0.00"

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
                "settled": True if row[3] == "true" else "False",
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
        """
        df = pd.read_excel(
            fh,
            skiprows=16,
            skipfooter=3,
            usecols="A,C:I,K:M",
            dtype={
                "Dato": datetime,  # A
                "Betalingsmetode": str,  # H
                "Kortudsteder": str,  # I
                "Personale": str,  # K
                "Beskrivelse": str,  # L
                "Solgt via": str,  # M
            },
            converters={
                "Kvitteringsnummer": optional_int,  # C
                "Moms (25%)": to_decimal,  # D
                "Total": to_decimal,  # E
                "Afgift": to_decimal,  # F
                "Netto": to_decimal,  # G
            },
        )
        return df

    @staticmethod
    def import_zettle_receipts_df(df):
        """Import a pandas dataframe with Zettle receipts (from POS sales)."""
        create_count = 0
        for index, row in df.iterrows():
            zr, created = ZettleReceipt.objects.get_or_create(
                zettle_created=pd.to_datetime(row["Dato"]).replace(tzinfo=cph),
                receipt_number=row["Kvitteringsnummer"],
                vat=to_decimal(row[2]),
                total=row["Total"],
                fee=row["Afgift"],
                net=row["Netto"],
                payment_method=row["Betalingsmetode"],
                card_issuer=row["Kortudsteder"]
                if not pd.isnull(row["Kortudsteder"])
                else None,
                staff=row["Personale"],
                description=row["Beskrivelse"],
                sold_via=row["Solgt via"],
            )
            if created:
                create_count += 1
        return create_count

    @staticmethod
    def load_zettle_balances_excel(fh):
        """Load an Excel file wi th Zettle balances and account movements.

        Zettle exports data in Excel files (not CSV), so this importer uses pandas for the file parsing.

        The receipts sheet has no header or footer rows, and no columns to skip.
        """
        df = pd.read_excel(
            fh,
            dtype={
                "Opgørelsesdato": datetime,  # A
                "Betalingsdato": datetime,  # B
                "Type": str,  # D
            },
            converters={
                "Reference": optional_int,  # C
                "Beløb": to_decimal,  # E
                "Saldo": to_decimal,  # F
            },
        )
        return df

    @staticmethod
    def import_zettle_balances_df(df):
        """Import a pandas dataframe with Zettle account statements and balances."""
        create_count = 0
        for index, row in df.iterrows():
            # create balance
            zb, created = ZettleBalance.objects.get_or_create(
                statement_time=timezone.make_aware(row["Opgørelsesdato"], timezone=cph),
                payment_time=timezone.make_aware(row["Betalingsdato"], timezone=cph)
                if not pd.isnull(row["Betalingsdato"])
                else None,
                payment_reference=row["Reference"]
                if not pd.isnull(row["Reference"])
                else None,
                description=row["Type"],
                amount=row["Beløb"],
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

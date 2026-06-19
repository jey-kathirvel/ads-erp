from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.accounts.models import LedgerEntry

from app.accounts.schemas import AccountCreate


class AccountService:

    @staticmethod
    def get_all(db: Session):

        return (

            db.query(Account)

            .order_by(

                Account.account_name

            )

            .all()

        )

    @staticmethod
    def get_by_id(

        db: Session,

        account_id: int

    ):

        return (

            db.query(Account)

            .filter(

                Account.id == account_id

            )

            .first()

        )

    @staticmethod
    def create(

        db: Session,

        data: AccountCreate

    ):

        count = db.query(Account).count() + 1

        account = Account(

            account_code=f"ACC{count:04}",

            account_name=data.account_name,

            account_group=data.account_group,

            opening_balance=data.opening_balance

        )

        db.add(account)

        db.commit()

        db.refresh(account)

        return account


class LedgerService:

    @staticmethod
    def post(

        db: Session,

        voucher_no,

        account_id,

        debit,

        credit,

        remarks,

        reference_type,

        reference_id

    ):

        ledger = LedgerEntry(

            voucher_no=voucher_no,

            account_id=account_id,

            debit=debit,

            credit=credit,

            remarks=remarks,

            reference_type=reference_type,

            reference_id=reference_id

        )

        db.add(ledger)

        db.commit()

        db.refresh(ledger)

        return ledger

    @staticmethod
    def get_account_entries(

        db: Session,

        account_id: int

    ):

        return (

            db.query(LedgerEntry)

            .filter(

                LedgerEntry.account_id == account_id

            )

            .order_by(

                LedgerEntry.id.desc()

            )

            .all()

        )
class AutoPostingService:

    @staticmethod
    def post_purchase(

        db: Session,

        purchase

    ):

        inventory = (

            db.query(Account)

            .filter(

                Account.account_name == "Inventory"

            )

            .first()

        )

        purchase_account = (

            db.query(Account)

            .filter(

                Account.account_name == "Purchase"

            )

            .first()

        )

        supplier = (

            db.query(Account)

            .filter(

                Account.account_name == "Supplier"

            )

            .first()

        )

        if inventory:

            LedgerService.post(

                db=db,

                voucher_no=purchase.purchase_no,

                account_id=inventory.id,

                debit=purchase.taxable_amount,

                credit=0,

                remarks="Purchase",

                reference_type="PURCHASE",

                reference_id=purchase.id

            )

        if purchase_account:

            LedgerService.post(

                db=db,

                voucher_no=purchase.purchase_no,

                account_id=purchase_account.id,

                debit=purchase.taxable_amount,

                credit=0,

                remarks="Purchase Expense",

                reference_type="PURCHASE",

                reference_id=purchase.id

            )

        if supplier:

            LedgerService.post(

                db=db,

                voucher_no=purchase.purchase_no,

                account_id=supplier.id,

                debit=0,

                credit=purchase.grand_total,

                remarks="Supplier Outstanding",

                reference_type="PURCHASE",

                reference_id=purchase.id

            )

    @staticmethod
    def post_sales(

        db: Session,

        invoice

    ):

        sales = (

            db.query(Account)

            .filter(

                Account.account_name == "Sales"

            )

            .first()

        )

        customer = (

            db.query(Account)

            .filter(

                Account.account_name == "Customer"

            )

            .first()

        )

        gst = (

            db.query(Account)

            .filter(

                Account.account_name == "GST Output"

            )

            .first()

        )

        if customer:

            LedgerService.post(

                db,

                invoice.invoice_no,

                customer.id,

                invoice.grand_total,

                0,

                "Customer Invoice",

                "SALES",

                invoice.id

            )

        if sales:

            LedgerService.post(

                db,

                invoice.invoice_no,

                sales.id,

                0,

                invoice.taxable_amount,

                "Sales",

                "SALES",

                invoice.id

            )

        if gst:

            LedgerService.post(

                db,

                invoice.invoice_no,

                gst.id,

                0,

                invoice.cgst + invoice.sgst + invoice.igst,

                "GST Output",

                "SALES",

                invoice.id

            )
class PaymentPostingService:

    @staticmethod
    def supplier_payment(

        db,

        payment

    ):

        supplier = (

            db.query(Account)

            .filter(

                Account.account_name == "Supplier"

            )

            .first()

        )

        cash = (

            db.query(Account)

            .filter(

                Account.account_name == "Cash"

            )

            .first()

        )

        if supplier:

            LedgerService.post(

                db=db,

                voucher_no=payment.payment_no,

                account_id=supplier.id,

                debit=payment.amount,

                credit=0,

                remarks="Supplier Payment",

                reference_type="SUPPLIER_PAYMENT",

                reference_id=payment.id

            )

        if cash:

            LedgerService.post(

                db=db,

                voucher_no=payment.payment_no,

                account_id=cash.id,

                debit=0,

                credit=payment.amount,

                remarks="Cash Paid",

                reference_type="SUPPLIER_PAYMENT",

                reference_id=payment.id

            )
class ReceiptPostingService:

    @staticmethod
    def customer_receipt(

        db,

        receipt

    ):

        customer = (

            db.query(Account)

            .filter(

                Account.account_name == "Customer"

            )

            .first()

        )

        cash = (

            db.query(Account)

            .filter(

                Account.account_name == "Cash"

            )

            .first()

        )

        if cash:

            LedgerService.post(

                db=db,

                voucher_no=receipt.receipt_no,

                account_id=cash.id,

                debit=receipt.amount,

                credit=0,

                remarks="Customer Receipt",

                reference_type="CUSTOMER_RECEIPT",

                reference_id=receipt.id

            )

        if customer:

            LedgerService.post(

                db=db,

                voucher_no=receipt.receipt_no,

                account_id=customer.id,

                debit=0,

                credit=receipt.amount,

                remarks="Customer Receipt",

                reference_type="CUSTOMER_RECEIPT",

                reference_id=receipt.id

            )

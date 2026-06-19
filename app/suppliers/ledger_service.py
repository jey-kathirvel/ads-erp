from sqlalchemy import func
from sqlalchemy.orm import Session

from app.suppliers.models import Supplier
from app.purchase.models import Purchase


class SupplierLedgerService:

    @staticmethod
    def get_supplier_summary(

        db: Session,

        supplier_id: int

    ):

        supplier = (

            db.query(Supplier)

            .filter(

                Supplier.id == supplier_id

            )

            .first()

        )

        purchase_total = (

            db.query(

                func.coalesce(

                    func.sum(

                        Purchase.grand_total

                    ),

                    0

                )

            )

            .filter(

                Purchase.supplier_id == supplier_id

            )

            .scalar()

        )

        opening = float(

            supplier.opening_balance or 0

        )

        outstanding = opening + float(

            purchase_total or 0

        )

        return {

            "supplier": supplier,

            "opening": opening,

            "purchase_total": float(

                purchase_total or 0

            ),

            "outstanding": outstanding

        }

    @staticmethod
    def get_all_outstanding(

        db: Session

    ):

        suppliers = (

            db.query(Supplier)

            .order_by(

                Supplier.supplier_name

            )

            .all()

        )

        result = []

        for supplier in suppliers:

            purchase_total = (

                db.query(

                    func.coalesce(

                        func.sum(

                            Purchase.grand_total

                        ),

                        0

                    )

                )

                .filter(

                    Purchase.supplier_id == supplier.id

                )

                .scalar()

            )

            opening = float(

                supplier.opening_balance or 0

            )

            outstanding = opening + float(

                purchase_total or 0

            )

            result.append({

                "supplier": supplier,

                "purchase_total": purchase_total,

                "opening": opening,

                "outstanding": outstanding

            })

        return result

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.products.schemas import ProductCreate
from app.products.service import ProductService
from app.auth.dependencies import login_required

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ---------------------------------
# Product List
# ---------------------------------

@router.get(
    "/products",
    response_class=HTMLResponse
)
async def product_list(
    request: Request,

    user=Depends(login_required),

    db: Session = Depends(get_db)

):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    products = ProductService.get_all(db)

    return templates.TemplateResponse(
        request=request,
        name="products/list.html",
        context={
            "products": products
        }
    )


# ---------------------------------
# Add Product Page
# ---------------------------------

@router.get(
    "/products/create",
    response_class=HTMLResponse
)
async def create_product_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="products/create.html"
    )


# ---------------------------------
# Save Product
# ---------------------------------

@router.post("/products/create")
async def create_product(

    product_name: str = Form(...),
    category_id: int = Form(1),
    unit_id: int = Form(1),
    hsn_code: str = Form(""),
    gst_percentage: float = Form(18),
    purchase_price: float = Form(0),
    selling_price: float = Form(0),
    opening_stock: float = Form(0),
    minimum_stock: float = Form(0),
    barcode: str = Form(""),
    description: str = Form(""),

    db: Session = Depends(get_db)

):

    product = ProductCreate(

        product_name=product_name,
        category_id=category_id,
        unit_id=unit_id,
        hsn_code=hsn_code,
        gst_percentage=gst_percentage,
        purchase_price=purchase_price,
        selling_price=selling_price,
        opening_stock=opening_stock,
        minimum_stock=minimum_stock,
        barcode=barcode,
        description=description

    )

    ProductService.create(
        db,
        product
    )

    return RedirectResponse(
        "/products",
        status_code=303
    )


# ---------------------------------
# View Product
# ---------------------------------

@router.get(
    "/products/{product_id}",
    response_class=HTMLResponse
)
async def view_product(

    product_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    product = ProductService.get_by_id(
        db,
        product_id
    )

    return templates.TemplateResponse(
        request=request,
        name="products/view.html",
        context={
            "product": product
        }
    )


# ---------------------------------
# Edit Product Page
# ---------------------------------

@router.get(
    "/products/{product_id}/edit",
    response_class=HTMLResponse
)
async def edit_product_page(

    product_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    product = ProductService.get_by_id(
        db,
        product_id
    )

    return templates.TemplateResponse(
        request=request,
        name="products/edit.html",
        context={
            "product": product
        }
    )


# ---------------------------------
# Update Product
# ---------------------------------

@router.post(
    "/products/{product_id}/edit"
)
async def update_product(

    product_id: int,

    product_name: str = Form(...),
    category_id: int = Form(1),
    unit_id: int = Form(1),
    hsn_code: str = Form(""),
    gst_percentage: float = Form(18),
    purchase_price: float = Form(0),
    selling_price: float = Form(0),
    opening_stock: float = Form(0),
    minimum_stock: float = Form(0),
    barcode: str = Form(""),
    description: str = Form(""),

    db: Session = Depends(get_db)

):

    product = ProductCreate(

        product_name=product_name,
        category_id=category_id,
        unit_id=unit_id,
        hsn_code=hsn_code,
        gst_percentage=gst_percentage,
        purchase_price=purchase_price,
        selling_price=selling_price,
        opening_stock=opening_stock,
        minimum_stock=minimum_stock,
        barcode=barcode,
        description=description

    )

    ProductService.update(
        db,
        product_id,
        product
    )

    return RedirectResponse(
        "/products",
        status_code=303
    )


# ---------------------------------
# Delete Product
# ---------------------------------

@router.get(
    "/products/{product_id}/delete"
)
async def delete_product(

    product_id: int,

    db: Session = Depends(get_db)

):

    ProductService.delete(
        db,
        product_id
    )

    return RedirectResponse(
        "/products",
        status_code=303
    )

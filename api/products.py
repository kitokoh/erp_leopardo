from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path, Request
from typing import List, Optional, Dict, Any
import os # For URL construction if base URL comes from env

# Assuming db is structured to allow from db import cruds or similar
# Or from ..db import cruds if api is a subdir of a main app package
# For this subtask, let's assume db.cruds gives access to modules
import db.cruds.products_crud as products_crud
import db.cruds.product_media_links_crud as product_media_links_crud
from ..models import ( # Relative import from parent models.py
    ProductResponse, ProductCreate, ProductUpdate, ProductBase,
    LinkMediaToProductRequest, ProductImageLinkResponse, ProductImageLinkUpdateRequest,
    ReorderProductMediaLinksRequest,
    UserInDB # For authentication
)
from .auth import get_current_active_user # Assuming auth is in the same directory

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
    responses={404: {"description": "Not found"}},
)

def construct_media_url(request: Request, relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    media_url_prefix = "/static_media_placeholder/" # Placeholder
    return f"{media_url_prefix}{relative_path.lstrip('/')}"


def format_product_response(db_product: Dict[str, Any], request: Request) -> ProductResponse:
    media_links_response = []
    if db_product.get('media_links'):
        for link_data in db_product['media_links']:
            media_links_response.append(ProductImageLinkResponse(
                link_id=link_data['link_id'],
                media_item_id=link_data['media_item_id'],
                display_order=link_data['display_order'],
                alt_text=link_data['alt_text'],
                image_url=construct_media_url(request, link_data.get('media_filepath')),
                thumbnail_url=construct_media_url(request, link_data.get('media_thumbnail_path')),
                media_title=link_data.get('media_title')
            ))

    product_data_for_model = {key: db_product[key] for key in ProductBase.__fields__ if key in db_product}
    product_data_for_model['product_id'] = db_product['product_id']

    return ProductResponse(
        **product_data_for_model,
        media_links=media_links_response
    )

@router.post("", response_model=ProductResponse, status_code=201)
async def create_product_api(
    product: ProductCreate,
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    product_dict = product.dict(exclude_unset=True)
    db_product_result = products_crud.add_product(product_data=product_dict)
    if not db_product_result.get('success'):
        error_detail = db_product_result.get('error', "Failed to create product.")
        raise HTTPException(status_code=400, detail=error_detail)
    db_product_id = db_product_result.get('id')
    if db_product_id is None:
        raise HTTPException(status_code=500, detail="Product creation succeeded but no ID was returned.")
    created_product = products_crud.get_product_by_id(id=db_product_id)
    if not created_product:
        raise HTTPException(status_code=500, detail="Product created but could not be retrieved.")
    return format_product_response(created_product, request)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_api(
    product_id: int = Path(..., description="The ID of the product to retrieve"),
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    db_product = products_crud.get_product_by_id(id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return format_product_response(db_product, request)

@router.get("/code/{product_code}", response_model=ProductResponse)
async def get_product_by_code_api(
    product_code: str = Path(..., description="The product code of the product to retrieve"),
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    db_product = products_crud.get_product_by_code(product_code=product_code)
    if db_product is None:
        raise HTTPException(status_code=404, detail=f"Product with code '{product_code}' not found")
    return format_product_response(db_product, request)

@router.get("", response_model=List[ProductResponse])
async def get_all_products_api(
    request: Request, # Corrected: request is first, no default
    category: Optional[str] = Query(None),
    language_code: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: UserInDB = Depends(get_current_active_user)
):
    filters = {}
    if category is not None: filters['category'] = category
    if language_code is not None: filters['language_code'] = language_code
    if is_active is not None: filters['is_active'] = is_active
    db_products = products_crud.get_all_products(filters=filters)
    return [format_product_response(p, request) for p in db_products]

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product_api(
    product_id: int,
    product_update: ProductUpdate,
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    update_data = product_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided.")
    update_result = products_crud.update_product(product_id=product_id, data=update_data)
    if not update_result.get('success'):
        error_detail = update_result.get('error', "Failed to update product.")
        existing_product_check = products_crud.get_product_by_id(id=product_id)
        if not existing_product_check:
            raise HTTPException(status_code=404, detail="Product not found, cannot update.")
        raise HTTPException(status_code=400, detail=error_detail)
    updated_product = products_crud.get_product_by_id(id=product_id)
    if not updated_product:
         raise HTTPException(status_code=404, detail="Product not found after update attempt.")
    return format_product_response(updated_product, request)

@router.delete("/{product_id}", status_code=204)
async def delete_product_api(
    product_id: int,
    current_user: UserInDB = Depends(get_current_active_user)
):
    existing_product = products_crud.get_product_by_id(id=product_id, include_deleted=True)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    if existing_product.get('is_deleted') == 1 or existing_product.get('is_deleted') is True:
        return
    delete_result = products_crud.delete_product(product_id=product_id)
    if not delete_result.get('success'):
        error_detail = delete_result.get('error', "Failed to delete product.")
        raise HTTPException(status_code=500, detail=error_detail)
    return

@router.post("/{product_id}/media_links", response_model=ProductImageLinkResponse, status_code=201)
async def link_media_to_product_api(
    product_id: int,
    link_request: LinkMediaToProductRequest,
    request_obj: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    db_product = products_crud.get_product_by_id(id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    link_id = product_media_links_crud.link_media_to_product(
        product_id=product_id,
        media_item_id=link_request.media_item_id,
        display_order=link_request.display_order,
        alt_text=link_request.alt_text
    )
    if link_id is None:
        raise HTTPException(status_code=400, detail="Failed to link media to product.")
    all_links = product_media_links_crud.get_media_links_for_product(product_id)
    newly_linked_info = next((l for l in all_links if l['media_item_id'] == link_request.media_item_id and l['link_id'] == link_id), None)
    if not newly_linked_info:
        raise HTTPException(status_code=500, detail="Media linked, but could not retrieve link details.")
    return ProductImageLinkResponse(
        link_id=newly_linked_info['link_id'],
        media_item_id=newly_linked_info['media_item_id'],
        display_order=newly_linked_info['display_order'],
        alt_text=newly_linked_info['alt_text'],
        image_url=construct_media_url(request_obj, newly_linked_info.get('media_filepath')),
        thumbnail_url=construct_media_url(request_obj, newly_linked_info.get('media_thumbnail_path')),
        media_title=newly_linked_info.get('media_title')
    )

@router.put("/media_links/{link_id}", response_model=ProductImageLinkResponse)
async def update_product_media_link_api(
    link_id: int,
    update_request: ProductImageLinkUpdateRequest,
    request_obj: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if update_request.display_order is None and update_request.alt_text is None:
        raise HTTPException(status_code=400, detail="No update data provided.")
    existing_link = product_media_links_crud.get_media_link_by_link_id(link_id=link_id)
    if not existing_link:
        raise HTTPException(status_code=404, detail="Product media link not found.")
    success = product_media_links_crud.update_media_link(
        link_id=link_id,
        display_order=update_request.display_order,
        alt_text=update_request.alt_text
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update product media link.")
    product_id = existing_link['product_id']
    all_product_links = product_media_links_crud.get_media_links_for_product(product_id)
    updated_link_info = next((l for l in all_product_links if l['link_id'] == link_id), None)
    if not updated_link_info:
        raise HTTPException(status_code=500, detail="Link updated, but could not retrieve details.")
    return ProductImageLinkResponse(
        link_id=updated_link_info['link_id'],
        media_item_id=updated_link_info['media_item_id'],
        display_order=updated_link_info['display_order'],
        alt_text=updated_link_info['alt_text'],
        image_url=construct_media_url(request_obj, updated_link_info.get('media_filepath')),
        thumbnail_url=construct_media_url(request_obj, updated_link_info.get('media_thumbnail_path')),
        media_title=updated_link_info.get('media_title')
    )

@router.delete("/media_links/{link_id}", status_code=204)
async def unlink_media_from_product_api(
    link_id: int,
    current_user: UserInDB = Depends(get_current_active_user)
):
    existing_link = product_media_links_crud.get_media_link_by_link_id(link_id=link_id)
    if not existing_link:
        raise HTTPException(status_code=404, detail="Product media link not found.")
    success = product_media_links_crud.unlink_media_from_product(link_id=link_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unlink media from product.")
    return

@router.post("/{product_id}/media_links/reorder", response_model=List[ProductImageLinkResponse])
async def reorder_product_media_links_api(
    product_id: int,
    reorder_request: ReorderProductMediaLinksRequest,
    request_obj: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    db_product = products_crud.get_product_by_id(id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    success = product_media_links_crud.update_product_media_display_orders(
        product_id=product_id,
        ordered_media_item_ids=reorder_request.ordered_media_item_ids
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reorder media links.")
    updated_links_raw = product_media_links_crud.get_media_links_for_product(product_id)
    response_links = []
    for link_data in updated_links_raw:
        response_links.append(ProductImageLinkResponse(
            link_id=link_data['link_id'],
            media_item_id=link_data['media_item_id'],
            display_order=link_data['display_order'],
            alt_text=link_data['alt_text'],
            image_url=construct_media_url(request_obj, link_data.get('media_filepath')),
            thumbnail_url=construct_media_url(request_obj, link_data.get('media_thumbnail_path')),
            media_title=link_data.get('media_title')
        ))
    return response_links

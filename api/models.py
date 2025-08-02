import uuid
import enum
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class TemplateInfo(BaseModel):
    template_id: int = Field(..., description="Unique identifier for the template")
    template_name: str = Field(..., description="Display name of the template")
    description: Optional[str] = Field(None, description="Optional description of the template")
    template_type: str = Field(..., description="Type of the template, e.g., 'document_excel', 'document_word', 'html_cover_page'")
    language_code: Optional[str] = Field(None, description="Language code of the template, e.g., 'en', 'fr'")

class DocumentGenerationRequest(BaseModel):
    template_id: int = Field(..., description="ID of the template to use for generation")
    client_id: str = Field(..., description="ID of the client for whom the document is generated")
    project_id: Optional[str] = Field(None, description="Optional ID of the project related to this document")
    company_id: str = Field(..., description="ID of the company (seller/our company) generating the document")
    target_language_code: str = Field(..., description="Target language for the document content, e.g., 'fr', 'en'")
    document_title: Optional[str] = Field(None, description="Optional title for the document, overrides template default if provided")
    line_items: Optional[List[Dict[str, Any]]] = Field(None, description="List of line items, e.g., products with quantities and prices")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Other context-specific data needed for the document")

class DocumentGenerationResponse(BaseModel):
    message: str = Field(..., description="Status message of the generation process")
    document_id: Optional[str] = Field(None, description="Unique ID of the generated document record in the database")
    client_id: str = Field(..., description="ID of the client for whom the document was generated")
    file_name: Optional[str] = Field(None, description="Name of the generated file")
    download_url: Optional[str] = Field(None, description="URL to download the generated document")

class TemplateVisibilityInfo(BaseModel):
    template_id: int # Matches TemplateInfo.template_id and DB schema
    template_name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[str] = None
    language_code: Optional[str] = None
    is_visible: bool

class UpdateTemplateVisibilityItem(BaseModel):
    template_id: int # Matches TemplateInfo.template_id
    is_visible: bool

class UpdateTemplateVisibilityRequest(BaseModel):
    preferences: List[UpdateTemplateVisibilityItem]

class Token(BaseModel):
    access_token: str = Field(..., description="The JWT access token string.")
    token_type: str = Field("bearer", description="The type of token, typically 'bearer'.")

class TokenData(BaseModel):
    username: Optional[str] = Field(None, description="The username extracted from the token.")

class UserInDB(BaseModel): # For current user dependency and user info
    username: str = Field(..., description="The user's unique username.")
    email: Optional[str] = Field(None, description="The user's email address.")
    full_name: Optional[str] = Field(None, description="The user's full name.")
    role: str = Field(..., description="The user's role, determining permissions.")
    is_active: bool = Field(..., description="Flag indicating if the user account is active.")
    user_id: str = Field(..., description="The unique identifier for the user.")

class ProductImageLinkBase(BaseModel):
    media_item_id: str = Field(..., description="ID of the linked media item (image).")
    display_order: Optional[int] = Field(0, description="Display order of the image for the product.")
    alt_text: Optional[str] = Field(None, description="Alternative text for the image.")

class ProductImageLinkCreate(ProductImageLinkBase):
    pass

class ProductImageLinkUpdateRequest(BaseModel):
    display_order: Optional[int] = Field(None, description="New display order of the image.")
    alt_text: Optional[str] = Field(None, description="New alternative text for the image.")

class ProductImageLinkResponse(ProductImageLinkBase):
    link_id: int = Field(..., description="Unique ID of the product-media link.")
    image_url: Optional[str] = Field(None, description="Full URL to the original image.")
    thumbnail_url: Optional[str] = Field(None, description="Full URL to the image thumbnail.")
    media_title: Optional[str] = Field(None, description="Title of the media item.")

    class Config:
        from_attributes = True

# --- Company Facture Models (Added for Expense Management) ---

class CompanyFactureBasePydantic(BaseModel): # Renamed to avoid conflict if a SQLAlchemy model with same name exists
    original_file_name: str = Field(..., example="facture_proveedor_XYZ_2023-10-28.pdf")
    stored_file_path: str = Field(..., example="/secure_storage/factures/facture_proveedor_XYZ_2023-10-28_uuid.pdf")
    file_mime_type: Optional[str] = Field(None, example="application/pdf")
    extraction_status: str = Field(default='pending_review', example="pending_review")
    extracted_data_json: Optional[str] = Field(None, example='{"amount": "120.50", "date": "2023-10-25", "vendor": "Proveedor XYZ"}')

class CompanyFactureCreatePydantic(CompanyFactureBasePydantic):
    pass

class CompanyFactureReadPydantic(CompanyFactureBasePydantic):
    facture_id: int
    upload_date: datetime
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False # Include soft delete status

    class Config:
        from_attributes = True

class CompanyFactureUpdatePydantic(BaseModel):
    original_file_name: Optional[str] = None
    stored_file_path: Optional[str] = None
    file_mime_type: Optional[str] = None
    extraction_status: Optional[str] = None
    extracted_data_json: Optional[str] = None


# --- Company Expense Models (Added for Expense Management) ---

class CompanyExpenseBasePydantic(BaseModel): # Renamed
    expense_date: date = Field(..., example="2023-10-28")
    amount: float = Field(..., gt=0, example=120.50)
    currency: str = Field(..., min_length=3, max_length=3, example="USD")
    recipient_name: str = Field(..., example="Proveedor XYZ S.A.")
    description: Optional[str] = Field(None, example="Monthly subscription for accounting software")

class CompanyExpenseCreatePydantic(CompanyExpenseBasePydantic):
    facture_id: Optional[int] = None # Can be created without a facture initially

class CompanyExpenseReadPydantic(CompanyExpenseBasePydantic):
    expense_id: int
    facture_id: Optional[int] = None
    created_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False # Include soft delete status
    facture: Optional[CompanyFactureReadPydantic] = None # To hold linked facture details

    class Config:
        from_attributes = True

class CompanyExpenseUpdatePydantic(BaseModel):
    expense_date: Optional[date] = None
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    recipient_name: Optional[str] = None
    description: Optional[str] = None
    # To update/link a facture, use a dedicated endpoint or ensure this field is handled carefully.
    # Explicitly allowing facture_id to be set to None to unlink.
    facture_id: Optional[int] = Field(None, allow_none=True)


# For linking a facture to an expense via an existing expense
class LinkFactureToExpenseRequestPydantic(BaseModel): # Renamed
    facture_id: int


# Pydantic Models for HR Reporting Responses

class HeadcountReportItem(BaseModel):
    department: Optional[str] = "N/A" # Department name, or "N/A" if not set
    count: int

class HeadcountReportResponse(BaseModel):
    report_name: str = "Department Headcount"
    generated_at: datetime # from datetime import datetime
    data: List[HeadcountReportItem]

class AnniversaryReportItem(BaseModel):
    employee_id: str # UUID as string
    full_name: str # Combine first_name and last_name
    anniversary_date: date # The upcoming anniversary date, from datetime import date
    years_of_service: int

class AnniversaryReportResponse(BaseModel):
    report_name: str = "Upcoming Work Anniversaries"
    generated_at: datetime # from datetime import datetime
    time_window_days: int # The number of upcoming days the report covers (e.g., 30, 60)
    data: List[AnniversaryReportItem]

class LeaveSummaryReportItem(BaseModel):
    leave_type_name: str
    total_days_taken_or_requested: float # Could be approved days, or pending days depending on query
    number_of_requests: int

class LeaveSummaryReportResponse(BaseModel):
    report_name: str = "Leave Summary"
    generated_at: datetime # from datetime import datetime
    filter_status: Optional[str] = None # e.g., "approved", "pending"
    data: List[LeaveSummaryReportItem]


# Pydantic Models for Employee
class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pydantic Models for Employee Document Management

# DocumentCategory
class DocumentCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class DocumentCategoryCreate(DocumentCategoryBase):
    pass

class DocumentCategoryResponse(DocumentCategoryBase):
    id: int

    class Config:
        from_attributes = True

# EmployeeDocument
class EmployeeDocumentBase(BaseModel):
    employee_id: str # UUID as string, matches Employee.id
    document_category_id: Optional[int] = None
    description: Optional[str] = None
    # file_name, file_path_or_key, file_type, file_size are typically set by server during upload

class EmployeeDocumentCreate(EmployeeDocumentBase):
    # This model is for creating the metadata record.
    # Actual file upload might be handled separately (e.g. FastAPI UploadFile)
    # and these fields would be populated by the server.
    # If client needs to send filename, it can be added here.
    pass

class EmployeeDocumentUpdate(BaseModel):
    document_category_id: Optional[int] = None
    description: Optional[str] = None

class EmployeeDocumentResponse(EmployeeDocumentBase):
    id: str # UUID as string
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None # in bytes
    uploaded_at: datetime # from datetime import datetime
    uploaded_by_id: Optional[str] = None # UUID as string for User.id

    document_category: Optional[DocumentCategoryResponse] = None # Nested
    employee: Optional[EmployeeResponse] = None # Optional for context, EmployeeResponse already defined

    download_url: Optional[str] = None # To be constructed by API endpoint logic

    class Config:
        from_attributes = True


# Pydantic Models for Performance Review Module

# Goal
class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None # from datetime import date
    status: Optional[str] = Field("open", description="Status of the goal")

class GoalCreate(GoalBase):
    employee_id: str # Employee this goal is for (UUID as string)
    set_by_id: Optional[str] = None # User who set goal (UUID as string), can be inferred from current_user

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None # Allow updating status, should map to GoalStatusEnum values

class GoalResponse(GoalBase):
    id: int
    employee_id: str # UUID as string
    set_by_id: Optional[str] = None # UUID as string
    created_at: datetime # from datetime import datetime
    updated_at: datetime # from datetime import datetime
    employee: Optional[EmployeeResponse] = None # Optional nesting

    class Config:
        from_attributes = True

# ReviewCycle
class ReviewCycleBase(BaseModel):
    name: str
    start_date: date # from datetime import date
    end_date: date   # from datetime import date
    is_active: Optional[bool] = True

class ReviewCycleCreate(ReviewCycleBase):
    pass

class ReviewCycleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class ReviewCycleResponse(ReviewCycleBase):
    id: int

    class Config:
        from_attributes = True

# PerformanceReview
class PerformanceReviewBase(BaseModel):
    review_cycle_id: Optional[int] = None
    review_date: Optional[date] = None # from datetime import date
    overall_rating: Optional[int] = Field(None, ge=1, le=5) # Example 1-5 rating
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    employee_comments: Optional[str] = None
    manager_comments: Optional[str] = None
    status: Optional[str] = Field("draft", description="Status of the review")

class PerformanceReviewCreate(PerformanceReviewBase):
    employee_id: str # UUID as string
    reviewer_id: Optional[str] = None # Manager (UUID as string), can be inferred or set

class PerformanceReviewUpdate(BaseModel): # Fields that can be updated at different stages
    review_cycle_id: Optional[int] = None
    review_date: Optional[date] = None
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    employee_comments: Optional[str] = None
    manager_comments: Optional[str] = None
    status: Optional[str] = None # Should map to PerformanceReviewStatusEnum values
    goal_ids_to_link: Optional[List[int]] = None # For linking goals to review
    goal_ids_to_unlink: Optional[List[int]] = None # For unlinking goals

class PerformanceReviewResponse(PerformanceReviewBase):
    id: int
    employee_id: str # UUID as string
    reviewer_id: Optional[str] = None # UUID as string
    created_at: datetime # from datetime import datetime
    updated_at: datetime # from datetime import datetime
    employee: Optional[EmployeeResponse] = None # Optional nesting
    reviewer: Optional[UserInDB] = None # Optional nesting for reviewer info (UserInDB defined in this file)
    review_cycle: Optional[ReviewCycleResponse] = None # Optional nesting
    goals_reviewed: List[GoalResponse] = [] # List of linked goals

    class Config:
        from_attributes = True


# Pydantic Models for Leave Management

class LeaveRequestStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

# LeaveType
class LeaveTypeBase(BaseModel):
    name: str
    default_days_entitled: Optional[int] = None

class LeaveTypeCreate(LeaveTypeBase):
    pass

class LeaveTypeResponse(LeaveTypeBase):
    id: int

    class Config:
        from_attributes = True

# LeaveBalance
class LeaveBalanceBase(BaseModel):
    employee_id: str # UUID as string
    leave_type_id: int
    year: int
    entitled_days: float
    used_days: float = 0.0

class LeaveBalanceCreate(LeaveBalanceBase):
    pass

class LeaveBalanceUpdate(BaseModel):
    entitled_days: Optional[float] = None
    used_days: Optional[float] = None

class LeaveBalanceResponse(LeaveBalanceBase):
    id: int
    leave_type: LeaveTypeResponse
    employee: EmployeeResponse # Nested Employee details

    class Config:
        from_attributes = True

# LeaveRequest
class LeaveRequestBase(BaseModel):
    leave_type_id: int
    start_date: date # from datetime import date
    end_date: date   # from datetime import date
    reason: Optional[str] = None
    num_days: float # Client might send this, or API calculates it

class LeaveRequestCreate(LeaveRequestBase):
    # employee_id will be set from path or current user, not in request body typically
    pass

class LeaveRequestUpdate(BaseModel): # For admin/manager to update status/comments
    status: Optional[str] = None # Should map to LeaveRequestStatusEnum values
    comments: Optional[str] = None

class LeaveRequestResponse(LeaveRequestBase):
    id: int
    employee_id: str # UUID as string
    status: str # Enum value as string
    request_date: datetime # from datetime import datetime
    approved_by_id: Optional[str] = None # UUID as string
    processed_date: Optional[datetime] = None
    comments: Optional[str] = None
    leave_type: LeaveTypeResponse # Nested LeaveType details
    employee: EmployeeResponse    # Nested Employee details

    class Config:
        from_attributes = True


# Pydantic Models for Employee
class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    product_name: str = Field(..., description="Name of the product.")
    description: Optional[str] = Field(None, description="Description of the product.")
    category: Optional[str] = Field(None, description="Product category.")
    language_code: Optional[str] = Field("fr", description="Language code for the product details.")
    base_unit_price: Optional[float] = Field(None, description="Base unit price of the product.")
    unit_of_measure: Optional[str] = Field(None, description="Unit of measure (e.g., pcs, kg).")
    weight: Optional[float] = Field(None, description="Weight of the product.")
    dimensions: Optional[str] = Field(None, description="Dimensions of the product (e.g., LxWxH cm).")
    is_active: Optional[bool] = Field(True, description="Whether the product is currently active.")
    product_code: str = Field(..., description="Unique code for the product.")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    language_code: Optional[str] = None
    base_unit_price: Optional[float] = None
    unit_of_measure: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int = Field(..., description="Unique identifier for the product.") # This was int, but Product SQLAlchemy model uses String ID.
    media_links: List[ProductImageLinkResponse] = Field([], description="List of associated media items (images).")
    # product_code will be inherited from ProductBase and is required.

    class Config:
        from_attributes = True

class LinkMediaToProductRequest(BaseModel):
    media_item_id: str = Field(..., description="The ID of the MediaItem to link.")
    display_order: Optional[int] = Field(0, description="Desired display order for this media.")
    alt_text: Optional[str] = Field(None, description="Alternative text for this media link.")

class ReorderProductMediaLinksRequest(BaseModel):
    ordered_media_item_ids: List[str] = Field(..., description="List of media_item_ids in the new desired display order.")

# Models for Invoices
class InvoiceBase(BaseModel):
    client_id: str
    project_id: Optional[str] = None
    document_id: Optional[str] = None
    invoice_number: str
    issue_date: date
    due_date: date
    total_amount: float
    currency: str
    payment_status: Optional[str] = "unpaid"
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    document_id: Optional[str] = None
    invoice_number: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payment_status: Optional[str] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

class Invoice(InvoiceBase):
    invoice_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

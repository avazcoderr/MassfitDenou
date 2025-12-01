from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.formatters import format_price
from math import ceil


def get_admin_panel_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Barcha mahsulotlar", callback_data="admin_view_products")],
            [InlineKeyboardButton(text="➕ Yangi mahsulot qo'shish", callback_data="admin_add_product")],
            [InlineKeyboardButton(text="✏️ Mahsulotni tahrirlash", callback_data="admin_edit_product")],
            [InlineKeyboardButton(text="🗑 Mahsulotni o'chirish", callback_data="admin_delete_product")],
            [InlineKeyboardButton(text="🏢 Filiallarni boshqarish", callback_data="admin_branches")],
            [InlineKeyboardButton(text="📢 Barcha foydalanuvchilarga habar yuborish", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🔙 Asosiy menyuga qaytish", callback_data="admin_back_main")]
        ]
    )
    return keyboard


def get_product_list_keyboard(products, page=0, items_per_page=10):
    """Get paginated product list keyboard"""
    total_pages = ceil(len(products) / items_per_page)
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]
    
    keyboard = []
    for product in page_products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {format_price(product.price)} so'm", 
                callback_data=f"product_view_{product.id}"
            )
        ])
    
    # Pagination controls
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"products_page_{page-1}"))
        
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="page_info"))
        
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"products_page_{page+1}"))
        
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_edit_keyboard(products, page=0, items_per_page=10):
    """Get paginated product edit keyboard"""
    total_pages = ceil(len(products) / items_per_page)
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]
    
    keyboard = []
    for product in page_products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name}", 
                callback_data=f"product_edit_{product.id}"
            )
        ])
    
    # Pagination controls
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"edit_page_{page-1}"))
        
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="edit_page_info"))
        
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"edit_page_{page+1}"))
        
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_delete_keyboard(products, page=0, items_per_page=10):
    """Get paginated product delete keyboard"""
    total_pages = ceil(len(products) / items_per_page)
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]
    
    keyboard = []
    for product in page_products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {product.name}", 
                callback_data=f"product_delete_{product.id}"
            )
        ])
    
    # Pagination controls
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"delete_page_{page-1}"))
        
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="delete_page_info"))
        
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"delete_page_{page+1}"))
        
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_detail_keyboard(product_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"product_edit_{product_id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"product_delete_{product_id}")],
            [InlineKeyboardButton(text="🔙 Mahsulotlarga qaytish", callback_data="admin_view_products")]
        ]
    )
    return keyboard


def get_confirm_delete_keyboard(product_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"product_confirm_delete_{product_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_view_products")
            ]
        ]
    )
    return keyboard


def get_cancel_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel")]
        ]
    )
    return keyboard


def get_branches_panel_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Barcha filiallar", callback_data="admin_view_branches")],
            [InlineKeyboardButton(text="➕ Yangi filial qo'shish", callback_data="admin_add_branch")],
            [InlineKeyboardButton(text="✏️ Filialni tahrirlash", callback_data="admin_edit_branch")],
            [InlineKeyboardButton(text="🗑 Filialni o'chirish", callback_data="admin_delete_branch")],
            [InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_panel")]
        ]
    )
    return keyboard


def get_branch_list_keyboard(branches):
    keyboard = []
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{branch.name}", 
                callback_data=f"branch_view_{branch.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Filiallar paneliga qaytish", callback_data="admin_branches")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_branch_edit_keyboard(branches):
    keyboard = []
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{branch.name}", 
                callback_data=f"branch_edit_{branch.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Filiallar paneliga qaytish", callback_data="admin_branches")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_branch_delete_keyboard(branches):
    keyboard = []
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {branch.name}", 
                callback_data=f"branch_delete_{branch.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Filiallar paneliga qaytish", callback_data="admin_branches")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_branch_detail_keyboard(branch_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"branch_edit_{branch_id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"branch_delete_{branch_id}")],
            [InlineKeyboardButton(text="🔙 Filiallarga qaytish", callback_data="admin_view_branches")]
        ]
    )
    return keyboard


def get_confirm_delete_branch_keyboard(branch_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"branch_confirm_delete_{branch_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_view_branches")
            ]
        ]
    )
    return keyboard


def get_broadcast_confirm_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="broadcast_cancel")
            ]
        ]
    )
    return keyboard

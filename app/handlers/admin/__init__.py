from aiogram import Router
from .panel import router as panel_router
from .products import router as products_router
from .branches import router as branches_router
from .broadcast import router as broadcast_router
from .statistics import router as statistics_router

router = Router()
router.include_router(panel_router)
router.include_router(products_router)
router.include_router(branches_router)
router.include_router(broadcast_router)
router.include_router(statistics_router)

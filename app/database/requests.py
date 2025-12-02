from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User, Order
from datetime import datetime, timedelta


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, tg_id: int, username: str = None, 
                     first_name: str = None, last_name: str = None, 
                     full_name: str = None, phone_number: str = None) -> User:
    user = User(
        tg_id=tg_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        phone_number=phone_number
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_phone(session: AsyncSession, tg_id: int, phone_number: str) -> User:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        user.phone_number = phone_number
        await session.commit()
        await session.refresh(user)
    return user


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


# Statistics functions
async def get_total_users_count(session: AsyncSession) -> int:
    """Get total number of users"""
    result = await session.execute(select(func.count(User.id)))
    return result.scalar()


async def get_weekly_users_stats(session: AsyncSession) -> dict:
    """Get weekly user statistics"""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    
    # Users added in the last week
    result = await session.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    new_users_this_week = result.scalar()
    
    # Users that existed a week ago
    result = await session.execute(
        select(func.count(User.id)).where(User.created_at < week_ago)
    )
    users_week_ago = result.scalar()
    
    return {
        'new_users_this_week': new_users_this_week,
        'users_week_ago': users_week_ago
    }


async def get_monthly_users_stats(session: AsyncSession) -> dict:
    """Get monthly user statistics"""
    now = datetime.now()
    month_ago = now - timedelta(days=30)
    
    # Users added in the last month
    result = await session.execute(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )
    new_users_this_month = result.scalar()
    
    return {
        'new_users_this_month': new_users_this_month
    }


async def get_daily_revenue(session: AsyncSession) -> float:
    """Get revenue from last 24 hours (delivered orders only)"""
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    
    result = await session.execute(
        select(func.sum(Order.total_price)).where(
            Order.status == 'delivered',
            Order.updated_at >= day_ago
        )
    )
    revenue = result.scalar()
    return float(revenue or 0)


async def get_weekly_revenue(session: AsyncSession) -> float:
    """Get revenue from last 7 days (delivered orders only)"""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    
    result = await session.execute(
        select(func.sum(Order.total_price)).where(
            Order.status == 'delivered',
            Order.updated_at >= week_ago
        )
    )
    revenue = result.scalar()
    return float(revenue or 0)


async def get_monthly_revenue(session: AsyncSession) -> float:
    """Get revenue from beginning of current month (delivered orders only)"""
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    
    result = await session.execute(
        select(func.sum(Order.total_price)).where(
            Order.status == 'delivered',
            Order.updated_at >= start_of_month
        )
    )
    revenue = result.scalar()
    return float(revenue or 0)


async def get_daily_cancelled_orders(session: AsyncSession) -> dict:
    """Get cancelled orders and revenue from last 24 hours"""
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    
    # Count cancelled orders
    count_result = await session.execute(
        select(func.count(Order.id)).where(
            Order.status == 'cancelled',
            Order.updated_at >= day_ago
        )
    )
    count = count_result.scalar()
    
    # Sum revenue of cancelled orders
    revenue_result = await session.execute(
        select(func.sum(Order.total_price)).where(
            Order.status == 'cancelled',
            Order.updated_at >= day_ago
        )
    )
    revenue = revenue_result.scalar()
    
    return {
        'count': count,
        'revenue': float(revenue or 0)
    }


async def get_weekly_cancelled_orders(session: AsyncSession) -> dict:
    """Get cancelled orders and revenue from last 7 days"""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    
    # Count cancelled orders
    count_result = await session.execute(
        select(func.count(Order.id)).where(
            Order.status == 'cancelled',
            Order.updated_at >= week_ago
        )
    )
    count = count_result.scalar()
    
    # Sum revenue of cancelled orders
    revenue_result = await session.execute(
        select(func.sum(Order.total_price)).where(
            Order.status == 'cancelled',
            Order.updated_at >= week_ago
        )
    )
    revenue = revenue_result.scalar()
    
    return {
        'count': count,
        'revenue': float(revenue or 0)
    }


async def get_monthly_cancelled_orders(session: AsyncSession) -> dict:
    """Get cancelled orders and revenue from beginning of current month"""
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    
    # Count cancelled orders
    count_result = await session.execute(
        select(func.count(Order.id)).where(
            Order.status == 'cancelled',
            Order.updated_at >= start_of_month
        )
    )
    count = count_result.scalar()
    
    # Sum revenue of cancelled orders
    revenue_result = await session.execute(
        select(func.sum(Order.total_price)).where(
            Order.status == 'cancelled',
            Order.updated_at >= start_of_month
        )
    )
    revenue = revenue_result.scalar()
    
    return {
        'count': count,
        'revenue': float(revenue or 0)
    }

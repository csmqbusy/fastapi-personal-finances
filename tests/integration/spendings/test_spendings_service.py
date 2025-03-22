from contextlib import nullcontext
from datetime import date, datetime
from itertools import cycle
from random import choice, randint
from typing import ContextManager

import pytest
from dirty_equals import IsApprox
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import CategoryNotFound
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.models import UserModel
from app.schemas.common_schemas import SAmountRange, SDatetimeRange
from app.schemas.transaction_category_schemas import SCategoryQueryParams
from app.schemas.transactions_schemas import (
    BasePeriodTransactionsSummary,
    DayTransactionsSummary,
    DayTransactionsSummaryCSV,
    MonthTransactionsSummary,
    MonthTransactionsSummaryCSV,
    STransactionResponse,
    STransactionsSortParams,
)
from app.services import spendings_service, user_spend_cat_service
from tests.factories import (
    SpendingsFactory,
    STransactionCreateFactory,
    STransactionsSummaryFactory,
    STransactionUpdateFactory,
    UsersSpendingCategoriesFactory,
)
from tests.helpers import (
    add_default_spendings_category,
    add_obj_to_db,
    add_obj_to_db_all,
    create_batch,
    create_n_categories,
    create_test_spendings,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "to_default_category",
    [True, False],
)
async def test_add_transaction_to_db(
    db_session: AsyncSession,
    user: UserModel,
    to_default_category: bool,
):
    await user_spend_cat_service.add_user_default_category(user.id, db_session)
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)

    category_name = category.category_name
    if to_default_category:
        category_name = None

    spending = await spendings_service.add_transaction_to_db(
        STransactionCreateFactory(category_name=category_name),
        user.id,
        db_session,
    )
    assert spending is not None
    assert type(spending) is STransactionResponse
    if category_name:
        assert spending.category_name == category_name
    else:
        assert (
            spending.category_name == settings.app.default_spending_category_name
        )


@pytest.mark.asyncio
async def test_update_transaction__success(
    db_session: AsyncSession,
    user: UserModel,
):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    new_category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db_all([category, new_category], db_session)

    spending = SpendingsFactory(user_id=user.id, category_id=category.id)
    await add_obj_to_db(spending, db_session)

    spending_update = STransactionUpdateFactory(
        category_name=new_category.category_name,
    )
    updated_spending = await spendings_service.update_transaction(
        spending.id,
        user.id,
        spending_update,
        db_session,
    )
    assert updated_spending.amount == spending_update.amount
    assert updated_spending.description == spending_update.description
    assert updated_spending.date == spending_update.date
    assert updated_spending.category_name == spending_update.category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_category_name, wrong_spending_id, expectation",
    [
        ("wrong", False, pytest.raises(CategoryNotFound)),
        (None, True, pytest.raises(TransactionNotFound)),
    ],
)
async def test_update_transaction__error(
    db_session: AsyncSession,
    user: UserModel,
    wrong_category_name: str | None,
    wrong_spending_id: bool,
    expectation: ContextManager,
):
    default_cat = await add_default_spendings_category(user.id, db_session)
    new_category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(new_category, db_session)

    spending = SpendingsFactory(user_id=user.id, category_id=default_cat.id)
    await add_obj_to_db(spending, db_session)

    spending_update = STransactionUpdateFactory(
        category_name=wrong_category_name or new_category.category_name,
    )
    with expectation:
        await spendings_service.update_transaction(
            spending.id + wrong_spending_id,
            user.id,
            spending_update,
            db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_spending_id, wrong_user_id, expectation",
    [
        (False, False, nullcontext()),
        (True, False, pytest.raises(TransactionNotFound)),
        (False, True, pytest.raises(TransactionNotFound)),
    ],
)
async def test_get_transaction(
    db_session: AsyncSession,
    user: UserModel,
    wrong_spending_id: bool,
    wrong_user_id: bool,
    expectation: ContextManager,
):
    default_cat = await add_default_spendings_category(user.id, db_session)

    spending = SpendingsFactory(user_id=user.id, category_id=default_cat.id)
    await add_obj_to_db(spending, db_session)

    with expectation:
        spending_from_db = await spendings_service.get_transaction(
            spending.id + wrong_spending_id,
            user.id + wrong_user_id,
            db_session,
        )
        assert spending_from_db.id == spending.id


@pytest.mark.asyncio
async def test_delete_transaction__success(
    db_session: AsyncSession,
    user: UserModel,
):
    default_cat = await add_default_spendings_category(user.id, db_session)

    spending = SpendingsFactory(user_id=user.id, category_id=default_cat.id)
    await add_obj_to_db(spending, db_session)

    await spendings_service.delete_transaction(spending.id, user.id, db_session)

    with pytest.raises(TransactionNotFound):
        await spendings_service.get_transaction(spending.id, user.id, db_session)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_spending_id, wrong_user_id",
    [
        (True, False),
        (False, True),
    ],
)
async def test_delete_transaction__error(
    db_session: AsyncSession,
    user: UserModel,
    wrong_spending_id: bool,
    wrong_user_id: bool,
):
    default_cat = await add_default_spendings_category(user.id, db_session)

    spending = SpendingsFactory(user_id=user.id, category_id=default_cat.id)
    await add_obj_to_db(spending, db_session)

    with pytest.raises(TransactionNotFound):
        await spendings_service.delete_transaction(
            spending.id + wrong_spending_id,
            user.id + wrong_user_id,
            db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_category_name, expectation",
    [
        (None, nullcontext()),
        ("wrong", pytest.raises(CategoryNotFound)),
    ],
)
async def test__get_category_id(
    db_session: AsyncSession,
    user: UserModel,
    wrong_category_name: str | None,
    expectation: ContextManager,
):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)

    with expectation:
        category_id = await spendings_service._get_category_id(
            user.id,
            wrong_category_name or category.category_name,
            db_session,
        )
        assert category.id == category_id


@pytest.mark.asyncio
async def test_get_transactions__error(
    db_session: AsyncSession,
    user: UserModel,
):
    category_name = "wrong"
    with pytest.raises(CategoryNotFound):
        await spendings_service.get_transactions(
            user_id=user.id,
            categories_params=[SCategoryQueryParams(category_name=category_name)],
            session=db_session,
        )


@pytest.mark.asyncio
async def test_get_transactions__category_id_priority(
    db_session: AsyncSession,
    user: UserModel,
):
    spendings_qty = 5
    category1 = UsersSpendingCategoriesFactory(user_id=user.id)
    category2 = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db_all([category1, category2], db_session)

    for category in [category1, category2]:
        await create_batch(
            db_session,
            spendings_qty,
            SpendingsFactory,
            dict(user_id=user.id, category_id=category.id),
        )

    category_params = SCategoryQueryParams(
        category_id=category1.id,
        category_name=category2.category_name,
    )
    spendings = await spendings_service.get_transactions(
        user_id=user.id,
        categories_params=[category_params],
        session=db_session,
    )
    assert len(spendings) == spendings_qty
    spendings_category_name = set(s.category_name for s in spendings)
    assert len(spendings_category_name) == 1
    assert category1.category_name in spendings_category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "search_term, datetime_from, datetime_to, expected_spendings_qty",
    [
        (
            "term",
            datetime(year=2022, month=1, day=1),
            datetime(year=2027, month=1, day=1, hour=23, minute=59, second=59),
            3,
        ),
        (
            "vodka",
            None,
            None,
            4,
        ),
    ],
)
async def test_get_transactions__success(
    db_session: AsyncSession,
    user: UserModel,
    search_term: str,
    datetime_from: datetime | None,
    datetime_to: datetime | None,
    expected_spendings_qty: int,
):
    amounts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000]
    datetimes = [
        datetime(year=2020 + i, month=1, day=1, hour=12) for i in range(9)
    ]
    descs = [f"{search_term.title()}{i}" if i % 2 else "txt" for i in range(9)]
    categories_ids = await create_n_categories(randint(1, 5), user.id, db_session)

    for amount, dt, desc in zip(amounts, datetimes, descs):
        spending = SpendingsFactory(
            amount=amount,
            description=desc,
            date=dt,
            user_id=user.id,
            category_id=choice(categories_ids),
        )
        await add_obj_to_db(spending, db_session)

    cat_params = [SCategoryQueryParams(category_id=i) for i in categories_ids]

    spendings = await spendings_service.get_transactions(
        user_id=user.id,
        categories_params=cat_params,
        search_term=search_term,
        datetime_range=SDatetimeRange(start=datetime_from, end=datetime_to),
        sort_params=STransactionsSortParams(
            sort_by=["id", "date", "some non existent field"],
        ),
        amount_params=SAmountRange(
            min_amount=min(amounts),
            max_amount=max(amounts),
        ),
        session=db_session,
    )
    assert len(spendings) == expected_spendings_qty
    for s in spendings:
        if datetime_from and datetime_to:
            assert datetime_from <= s.date <= datetime_to
        assert search_term.lower() in s.description.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "datetime_from, datetime_to, wrong_category, expectation, expected_sum_amount",
    [
        (
            None,
            None,
            False,
            nullcontext(),
            4500,
        ),
        (
            datetime(year=2022, month=1, day=1),
            datetime(year=2027, month=1, day=1, hour=23, minute=59, second=59),
            False,
            nullcontext(),
            3300,
        ),
        (
            None,
            None,
            True,
            pytest.raises(CategoryNotFound),
            0,
        ),
    ],
)
async def test_get_summary(
    db_session: AsyncSession,
    user: UserModel,
    datetime_from: datetime | None,
    datetime_to: datetime | None,
    wrong_category: bool,
    expected_sum_amount: int,
    expectation: ContextManager,
):
    search_term = "term"
    amounts = [100, 200, 300, 400, 500, 600, 700, 800, 900]
    datetimes = [
        datetime(year=2020 + i, month=1, day=1, hour=12) for i in range(9)
    ]
    categories_ids = await create_n_categories(3, user.id, db_session)

    for amount, dt, cat_id in zip(amounts, datetimes, cycle(categories_ids)):
        spending = SpendingsFactory(
            amount=amount,
            description=search_term,
            date=dt,
            user_id=user.id,
            category_id=cat_id,
        )
        await add_obj_to_db(spending, db_session)

    cat_params = [SCategoryQueryParams(category_id=i) for i in categories_ids]
    if wrong_category:
        cat_params.append(SCategoryQueryParams(category_name="##wrong"))

    with expectation:
        summary = await spendings_service.get_summary(
            user_id=user.id,
            categories_params=cat_params,
            search_term=search_term,
            datetime_range=SDatetimeRange(start=datetime_from, end=datetime_to),
            amount_params=SAmountRange(
                min_amount=min(amounts),
                max_amount=max(amounts),
            ),
            session=db_session,
        )
        assert len(summary) == len(categories_ids)
        assert sum(s.amount for s in summary) == expected_sum_amount


@pytest.mark.asyncio
async def test__extract_category_ids(db_session: AsyncSession, user: UserModel):
    cat_names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]
    cat_params = []
    cat_ids = set()
    for index, cat_name in enumerate(cat_names):
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            cat_name,
            db_session,
        )
        cat_ids.add(category.id)
        if index % 2:
            cat_params.append(SCategoryQueryParams(category_name=cat_name))
        else:
            cat_params.append(SCategoryQueryParams(category_id=category.id))

    exctracted_cat_ids = await spendings_service._extract_category_ids(
        db_session,
        user.id,
        cat_params,
    )
    assert set(exctracted_cat_ids) == cat_ids


@pytest.mark.parametrize(
    "cat_names, spendings_qty, expected_amounts",
    [
        (["Food"], [5], [1500]),
        (["Food", "Relax", "Health"], [1, 3, 5], [100, 600, 1500]),
    ],
)
def test__summarize(
    cat_names: list[str],
    spendings_qty: list[int],
    expected_amounts: list[int],
):
    amounts = [100, 200, 300, 400, 500]
    transactions = []
    for index, cat_name in enumerate(cat_names):
        for i in range(spendings_qty[index]):
            tx = STransactionResponse(
                amount=amounts[i],
                category_name=cat_name,
                description="text",
                date=datetime(year=2020, month=1, day=1, hour=12),
                id=randint(1, 10000),
            )
            transactions.append(tx)

    summary = spendings_service._summarize(transactions)
    assert len(summary) == len(cat_names)
    for s in summary:
        for i in range(len(cat_names)):
            if s.category_name == cat_names[i]:
                assert s.amount == expected_amounts[i]


@pytest.mark.parametrize(
    "cat_names, spendings_qty, amounts, expected_order",
    [
        (
            ["Food", "Relax", "Health"],
            [1, 3, 5],
            [100, 200, 300, 400, 500],
            ["Health", "Relax", "Food"],
        ),
        (
            ["Food", "Relax", "Health", "Casino", "Fun"],
            [4, 1, 2, 3, 5],
            [100, 200, 300, 400, 500],
            ["Fun", "Food", "Casino", "Health", "Relax"],
        ),
    ],
)
def test__sort_summarize(
    cat_names: list[str],
    spendings_qty: list[int],
    amounts: list[int],
    expected_order: list[str],
):
    transactions = []
    for index, cat_name in enumerate(cat_names):
        for i in range(spendings_qty[index]):
            tx = STransactionResponse(
                amount=amounts[i],
                category_name=cat_name,
                description="text",
                date=datetime(year=2020, month=1, day=1, hour=12),
                id=randint(1, 10000),
            )
            transactions.append(tx)

    summary = spendings_service._summarize(transactions)
    sorted_summary = spendings_service._sort_summarize(summary)
    assert [i.category_name for i in sorted_summary] == expected_order


@pytest.mark.asyncio
async def test_get_summary_chart(db_session: AsyncSession, user: UserModel):
    spendings_qty = 30
    num_of_cats = 3
    categories_ids = await create_n_categories(num_of_cats, user.id, db_session)

    for i in range(spendings_qty):
        spending = SpendingsFactory(
            user_id=user.id,
            category_id=categories_ids[i % len(categories_ids)],
        )
        await add_obj_to_db(spending, db_session)

    cat_params = [SCategoryQueryParams(category_id=i) for i in categories_ids]

    chart = await spendings_service.get_summary_chart(
        user_id=user.id,
        categories_params=cat_params,
        session=db_session,
    )
    assert chart
    assert type(chart) is bytes
    assert len(chart) > 1000


@pytest.mark.asyncio
async def test_get_annual_summary(db_session: AsyncSession, user: UserModel):
    await create_test_spendings(db_session, user.id)

    summary = await spendings_service.get_annual_summary(
        db_session,
        user.id,
        date.today().year,
    )
    assert all(type(s) is MonthTransactionsSummary for s in summary)


@pytest.mark.asyncio
async def test_annual_summary_chart(db_session: AsyncSession, user: UserModel):
    await create_test_spendings(db_session, user.id)

    for split_by_cat in (True, False):
        chart = await spendings_service.get_annual_summary_chart(
            user_id=user.id,
            year=date.today().year,
            transactions_type="spendings",
            split_by_category=split_by_cat,
            session=db_session,
        )
        assert chart
        assert type(chart) is bytes
        assert len(chart) > 1000


@pytest.mark.asyncio
async def test_get_monthly_summary(db_session: AsyncSession, user: UserModel):
    await create_test_spendings(
        db_session, user.id, spendings_date_range="this_month"
    )

    summary = await spendings_service.get_monthly_summary(
        db_session,
        user.id,
        date.today().year,
        date.today().month,
    )
    assert 1 <= len(summary) <= 31
    assert all(type(s) is DayTransactionsSummary for s in summary)


@pytest.mark.asyncio
async def test_get_monthly_summary_chart(
    db_session: AsyncSession,
    user: UserModel,
):
    await create_test_spendings(
        db_session, user.id, spendings_date_range="this_month"
    )

    for split_by_cat in (True, False):
        chart = await spendings_service.get_monthly_summary_chart(
            session=db_session,
            user_id=user.id,
            year=date.today().year,
            month=date.today().month,
            transactions_type="spendings",
            split_by_category=split_by_cat,
        )
        assert chart
        assert type(chart) is bytes
        assert len(chart) > 1000


@pytest.mark.asyncio
async def test__get_categories_from_summary(
    db_session: AsyncSession,
    user: UserModel,
):
    categories_n = 3
    periods_n = 5
    period_summary = [
        BasePeriodTransactionsSummary(
            total_amount=200000,
            summary=[STransactionsSummaryFactory() for _ in range(categories_n)],
        )
        for _ in range(periods_n)
    ]
    categories = spendings_service._get_categories_from_summary(period_summary)
    assert len(categories) == IsApprox(
        categories_n * periods_n, delta=categories_n
    )


@pytest.mark.asyncio
async def test__prepare_data_for_chart_with_categories_split(
    db_session: AsyncSession,
    user: UserModel,
):
    await create_test_spendings(db_session, user.id)

    summary = await spendings_service.get_annual_summary(
        db_session,
        user.id,
        date.today().year,
    )
    categories = spendings_service._get_categories_from_summary(summary)

    prepared_data = (
        spendings_service._prepare_data_for_chart_with_categories_split(
            summary,
            categories,
        )
    )
    assert [len(d) == len(prepared_data[0]) for d in prepared_data]


@pytest.mark.asyncio
async def test_prepare_period_summary_for_csv__year(
    db_session: AsyncSession,
    user: UserModel,
):
    await create_test_spendings(db_session, user.id)

    summary = await spendings_service.get_annual_summary(
        db_session,
        user.id,
        date.today().year,
    )

    prepared_data = spendings_service.prepare_annual_summary_for_csv(
        period_summary=summary,
    )

    assert all(type(d) is MonthTransactionsSummaryCSV for d in prepared_data)


@pytest.mark.asyncio
async def test_prepare_period_summary_for_csv__month(
    db_session: AsyncSession,
    user: UserModel,
):
    await create_test_spendings(
        db_session,
        user.id,
        spendings_date_range="this_month",
    )

    summary = await spendings_service.get_monthly_summary(
        db_session,
        user.id,
        date.today().year,
        date.today().month,
    )

    prepared_data = spendings_service.prepare_monthly_summary_for_csv(
        period_summary=summary,
    )

    assert all(type(d) is DayTransactionsSummaryCSV for d in prepared_data)

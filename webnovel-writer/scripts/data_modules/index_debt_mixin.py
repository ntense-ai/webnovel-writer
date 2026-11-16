#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IndexDebtMixin extracted from IndexManager.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class IndexDebtMixin:
    def create_override_contract(self, contract: OverrideContractMeta) -> int:
        'Create or update an Override Contract using SQLite INSERT ... ON CONFLICT ... DO UPDATE for an atomic UPSERT. Safe under concurrency without explicit locks; preserves the ID so chase_debt.override_contract_id cannot dangle; freezes all fields once fulfilled or cancelled. Requires SQLite 3.24+ for ON CONFLICT and does not depend on RETURNING (3.35+). Return the contract ID.'
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Use ON CONFLICT for an atomic UPSERT (SQLite 3.24+).
            # Freeze terminal states completely: preserve every field when fulfilled or cancelled.
            cursor.execute(
                """
                INSERT INTO override_contracts
                (chapter, constraint_type, constraint_id, rationale_type,
                 rationale_text, payback_plan, due_chapter, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chapter, constraint_type, constraint_id) DO UPDATE SET
                    rationale_type = CASE
                        WHEN override_contracts.status IN ('fulfilled', 'cancelled')
                        THEN override_contracts.rationale_type
                        ELSE excluded.rationale_type
                    END,
                    rationale_text = CASE
                        WHEN override_contracts.status IN ('fulfilled', 'cancelled')
                        THEN override_contracts.rationale_text
                        ELSE excluded.rationale_text
                    END,
                    payback_plan = CASE
                        WHEN override_contracts.status IN ('fulfilled', 'cancelled')
                        THEN override_contracts.payback_plan
                        ELSE excluded.payback_plan
                    END,
                    due_chapter = CASE
                        WHEN override_contracts.status IN ('fulfilled', 'cancelled')
                        THEN override_contracts.due_chapter
                        ELSE excluded.due_chapter
                    END,
                    status = CASE
                        WHEN override_contracts.status IN ('fulfilled', 'cancelled')
                        THEN override_contracts.status
                        ELSE excluded.status
                    END
            """,
                (
                    contract.chapter,
                    contract.constraint_type,
                    contract.constraint_id,
                    contract.rationale_type,
                    contract.rationale_text,
                    contract.payback_plan,
                    contract.due_chapter,
                    contract.status,
                ),
            )

            # Query the ID rather than use RETURNING, which requires SQLite 3.35+.
            cursor.execute(
                """
                SELECT id FROM override_contracts
                WHERE chapter = ? AND constraint_type = ? AND constraint_id = ?
            """,
                (contract.chapter, contract.constraint_type, contract.constraint_id),
            )
            row = cursor.fetchone()
            if not row:
                # A missing record after UPSERT is an unexpected error.
                raise RuntimeError(
                    f"Cannot retrieve ID after override contract UPSERT: "
                    f"chapter={contract.chapter}, type={contract.constraint_type}, "
                    f"id={contract.constraint_id}"
                )
            contract_id = row[0]

            conn.commit()
            return contract_id

    def get_pending_overrides(self, before_chapter: int = None) -> List[Dict]:
        'Get Override Contracts awaiting repayment.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if before_chapter:
                cursor.execute(
                    """
                    SELECT * FROM override_contracts
                    WHERE status = 'pending' AND due_chapter <= ?
                    ORDER BY due_chapter ASC
                """,
                    (before_chapter,),
                )
            else:
                cursor.execute("""
                    SELECT * FROM override_contracts
                    WHERE status = 'pending'
                    ORDER BY due_chapter ASC
                """)
            return [dict(row) for row in cursor.fetchall()]

    def get_overdue_overrides(self, current_chapter: int) -> List[Dict]:
        'Get overdue Override Contracts.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM override_contracts
                WHERE status = 'pending' AND due_chapter < ?
                ORDER BY due_chapter ASC
            """,
                (current_chapter,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def fulfill_override(self, contract_id: int) -> bool:
        'Mark an Override Contract fulfilled.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE override_contracts SET
                    status = 'fulfilled',
                    fulfilled_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (contract_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_chapter_overrides(self, chapter: int) -> List[Dict]:
        'Get Override Contracts created in a chapter.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM override_contracts WHERE chapter = ?
            """,
                (chapter,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== v5.3 Reader-engagement debt operations ====================

    def create_debt(self, debt: ChaseDebtMeta) -> int:
        'Create reader-engagement debt and return its ID.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chase_debt
                (debt_type, original_amount, current_amount, interest_rate,
                 source_chapter, due_chapter, override_contract_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    debt.debt_type,
                    debt.original_amount,
                    debt.current_amount,
                    debt.interest_rate,
                    debt.source_chapter,
                    debt.due_chapter,
                    debt.override_contract_id if debt.override_contract_id else None,
                    debt.status,
                ),
            )
            conn.commit()
            debt_id = cursor.lastrowid

            # Record the creation event.
            self._record_debt_event(
                cursor,
                debt_id,
                "created",
                debt.original_amount,
                debt.source_chapter,
                f"Create debt: {debt.debt_type}",
            )
            conn.commit()
            return debt_id

    def get_active_debts(self) -> List[Dict]:
        'Get all active debts.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chase_debt
                WHERE status = 'active'
                ORDER BY due_chapter ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_overdue_debts(self, current_chapter: int) -> List[Dict]:
        'Get overdue debts, including expired active debts and those already marked overdue.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM chase_debt
                WHERE (status = 'overdue')
                   OR (status = 'active' AND due_chapter < ?)
                ORDER BY due_chapter ASC
            """,
                (current_chapter,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_total_debt_balance(self) -> float:
        'Get the total outstanding balance, including active and overdue debts.'
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(current_amount), 0) FROM chase_debt
                WHERE status IN ('active', 'overdue')
            """)
            return cursor.fetchone()[0]

    def accrue_interest(self, current_chapter: int) -> Dict[str, Any]:
        'Accrue interest once per chapter. Both active and overdue debts accrue interest. Use debt_events to prevent duplicate accrual for the same chapter, and check and update overdue status. Return {debts_processed, total_interest, new_overdues, skipped_already_processed}.'
        result = {
            "debts_processed": 0,
            "total_interest": 0.0,
            "new_overdues": 0,
            "skipped_already_processed": 0,
        }

        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Get all outstanding debts; both active and overdue balances continue accruing interest.
            cursor.execute("""
                SELECT * FROM chase_debt WHERE status IN ('active', 'overdue')
            """)
            debts = cursor.fetchall()

            for debt in debts:
                debt_id = debt["id"]
                current_amount = debt["current_amount"]
                interest_rate = debt["interest_rate"]
                due_chapter = debt["due_chapter"]
                debt_status = debt["status"]

                # Check whether this chapter has already accrued interest to prevent duplicate calls.
                cursor.execute(
                    """
                    SELECT 1 FROM debt_events
                    WHERE debt_id = ? AND chapter = ? AND event_type = 'interest_accrued'
                """,
                    (debt_id, current_chapter),
                )
                if cursor.fetchone():
                    result["skipped_already_processed"] += 1
                    continue

                # Calculate interest.
                interest = current_amount * interest_rate
                new_amount = current_amount + interest

                # Update the debt.
                cursor.execute(
                    """
                    UPDATE chase_debt SET
                        current_amount = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (new_amount, debt_id),
                )

                # Record the interest event.
                self._record_debt_event(
                    cursor,
                    debt_id,
                    "interest_accrued",
                    interest,
                    current_chapter,
                    f"Interest: {interest:.2f} (Rate: {interest_rate * 100:.0f}%)",
                )

                result["debts_processed"] += 1
                result["total_interest"] += interest

                # Check for overdue status, for active debts only.
                if debt_status == "active" and current_chapter > due_chapter:
                    cursor.execute(
                        """
                        UPDATE chase_debt SET status = 'overdue'
                        WHERE id = ? AND status = 'active'
                    """,
                        (debt_id,),
                    )
                    if cursor.rowcount > 0:
                        result["new_overdues"] += 1
                        self._record_debt_event(
                            cursor,
                            debt_id,
                            "overdue",
                            new_amount,
                            current_chapter,
                            f"Debt overdue (Deadline: Chapter {due_chapter})",
                        )

            conn.commit()

        return result

    def pay_debt(self, debt_id: int, amount: float, chapter: int) -> Dict[str, Any]:
        'Repay debt. Validate amount > 0. On full repayment, atomically check and mark the associated Override fulfilled, using a NOT EXISTS subquery to ensure all debts are cleared under concurrency. Return {remaining, fully_paid, override_fulfilled}.'
        # Validate the repayment amount.
        if amount <= 0:
            return {
                "remaining": 0,
                "fully_paid": False,
                "error": "Repayment amount must be greater than0",
            }

        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT current_amount, override_contract_id FROM chase_debt WHERE id = ?",
                (debt_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {"remaining": 0, "fully_paid": False, "error": "Debt does not exist"}

            current = row["current_amount"]
            override_contract_id = row["override_contract_id"]
            remaining = max(0, current - amount)
            override_fulfilled = False

            if remaining == 0:
                # Full repayment
                cursor.execute(
                    """
                    UPDATE chase_debt SET
                        current_amount = 0,
                        status = 'paid',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (debt_id,),
                )
                self._record_debt_event(
                    cursor, debt_id, "full_payment", amount, chapter, "Debt fully repaid"
                )

                # Atomically check and mark the Override fulfilled.
                # Use NOT EXISTS for concurrency safety: update only when no outstanding debts remain.
                if override_contract_id:
                    cursor.execute(
                        """
                        UPDATE override_contracts SET
                            status = 'fulfilled',
                            fulfilled_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                          AND status = 'pending'
                          AND NOT EXISTS (
                              SELECT 1 FROM chase_debt
                              WHERE override_contract_id = ?
                                AND status IN ('active', 'overdue')
                          )
                    """,
                        (override_contract_id, override_contract_id),
                    )
                    if cursor.rowcount > 0:
                        override_fulfilled = True
            else:
                # Partial repayment
                cursor.execute(
                    """
                    UPDATE chase_debt SET
                        current_amount = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (remaining, debt_id),
                )
                self._record_debt_event(
                    cursor,
                    debt_id,
                    "partial_payment",
                    amount,
                    chapter,
                    f"Partial repayment; remaining: {remaining:.2f}",
                )

            conn.commit()
            return {
                "remaining": remaining,
                "fully_paid": remaining == 0,
                "override_fulfilled": override_fulfilled,
            }

    def _record_debt_event(
        self,
        cursor,
        debt_id: int,
        event_type: str,
        amount: float,
        chapter: int,
        note: str = "",
    ):
        'Record a debt event; internal helper.'
        cursor.execute(
            """
            INSERT INTO debt_events (debt_id, event_type, amount, chapter, note)
            VALUES (?, ?, ?, ?, ?)
        """,
            (debt_id, event_type, amount, chapter, note),
        )

    def get_debt_history(self, debt_id: int) -> List[Dict]:
        "Get a debt's event history."
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM debt_events
                WHERE debt_id = ?
                ORDER BY created_at ASC
            """,
                (debt_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== v5.3 Chapter reader-engagement metadata ====================

    def get_debt_summary(self) -> Dict[str, Any]:
        'Get debt summary information.'
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Active debts
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(current_amount), 0) as total
                FROM chase_debt WHERE status = 'active'
            """)
            active = cursor.fetchone()

            # Overdue debts
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(current_amount), 0) as total
                FROM chase_debt WHERE status = 'overdue'
            """)
            overdue = cursor.fetchone()

            # Overrides awaiting repayment
            cursor.execute("""
                SELECT COUNT(*) FROM override_contracts WHERE status = 'pending'
            """)
            pending_overrides = cursor.fetchone()[0]

            return {
                "active_debts": active["count"],
                "active_total": active["total"],
                "overdue_debts": overdue["count"],
                "overdue_total": overdue["total"],
                "pending_overrides": pending_overrides,
                "total_balance": active["total"] + overdue["total"],
            }

    # ==================== Batch operations ====================


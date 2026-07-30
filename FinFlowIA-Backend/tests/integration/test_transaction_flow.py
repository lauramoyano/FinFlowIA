"""Integration tests for the complete transaction flow."""

import pytest
from httpx import AsyncClient


class TestTransactionFlow:
    @pytest.mark.asyncio
    async def test_create_and_retrieve_transaction(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that a transaction can be created and then retrieved by ID."""
        # Create
        create_response = await client.post(
            "/api/v1/transactions",
            json={
                "description": "Pago proveedor materiales",
                "amount": "500.00",
                "transaction_type": "expense",
                "transaction_date": "2026-05-22",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        transaction_id = create_response.json()["data"]["id"]
        assert transaction_id is not None

        # Retrieve
        get_response = await client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        data = get_response.json()["data"]
        assert data["description"] == "Pago proveedor materiales"
        assert data["amount"] == "500.00"
        assert data["transaction_type"] == "expense"

    @pytest.mark.asyncio
    async def test_list_transactions_returns_paginated_results(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that the transaction list endpoint returns paginated results."""
        # Create multiple transactions
        for i in range(3):
            await client.post(
                "/api/v1/transactions",
                json={
                    "description": f"Transaction {i}",
                    "amount": f"{(i + 1) * 100}.00",
                    "transaction_type": "expense",
                    "transaction_date": "2026-05-22",
                },
                headers=auth_headers,
            )

        response = await client.get(
            "/api/v1/transactions?page=1&page_size=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "total" in body
        assert body["total"] >= 3

    @pytest.mark.asyncio
    async def test_delete_transaction(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that a transaction can be deleted and becomes inaccessible."""
        # Create
        create_response = await client.post(
            "/api/v1/transactions",
            json={
                "description": "To be deleted",
                "amount": "100.00",
                "transaction_type": "expense",
                "transaction_date": "2026-05-22",
            },
            headers=auth_headers,
        )
        transaction_id = create_response.json()["data"]["id"]

        # Delete
        delete_response = await client.delete(
            f"/api/v1/transactions/{transaction_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access_returns_401(self, client: AsyncClient) -> None:
        """Test that endpoints require authentication."""
        response = await client.get("/api/v1/transactions")
        assert response.status_code == 401  # missing credentials -> HTTPBearer 401

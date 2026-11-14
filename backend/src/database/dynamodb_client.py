"""DynamoDB transaction storage adapter."""

from typing import Any

from src.config import load_settings


class DynamoDBClient:
    """Small DynamoDB adapter for transaction CRUD operations."""

    def __init__(self, table_name: str | None = None):
        import boto3

        settings = load_settings()
        resolved_table_name = table_name or settings.dynamodb_table_name
        if not resolved_table_name:
            raise ValueError("Set DYNAMODB_TABLE_NAME before using DynamoDB.")
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self._table = dynamodb.Table(resolved_table_name)

    def put_transaction(self, transaction: dict[str, Any]) -> dict[str, Any]:
        """Insert or replace a transaction item."""
        self._table.put_item(Item=transaction)
        return transaction

    def get_transactions(self, user_id: str) -> list[dict[str, Any]]:
        """Query transactions by partition key user_id."""
        from boto3.dynamodb.conditions import Key

        transactions: list[dict[str, Any]] = []
        query: dict[str, Any] = {
            "KeyConditionExpression": Key("user_id").eq(user_id),
        }
        while True:
            response = self._table.query(**query)
            transactions.extend(response["Items"])
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return transactions
            query["ExclusiveStartKey"] = last_key

from enum import Enum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class CategoryType(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    SUPPLIES = "supplies"
    MARKETING = "marketing"
    PAYROLL = "payroll"
    RENT = "rent"
    EQUIPMENT = "equipment"
    SALES = "sales"
    SERVICES = "services"
    OTHER = "other"
    UNCATEGORIZED = "uncategorized"

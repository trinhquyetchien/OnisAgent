"""Streamlit entry point for the Onis finance dashboard."""

import streamlit as st

from app.components.chat_interface import render_chat_interface
from app.components.dashboard import render_dashboard
from app.components.sidebar import render_sidebar
from src.config import load_settings
from src.database.dynamodb_client import DynamoDBClient
from src.database.local_storage import load_transactions

st.set_page_config(page_title="Onis | Quản lý dòng tiền", page_icon="💸", layout="wide")
settings = load_settings()
page = render_sidebar(settings.data_source)

st.title("Onis – Trợ lý AI quản lý dòng tiền")
if settings.data_source == "csv":
    transactions = load_transactions()
else:
    transactions = DynamoDBClient().get_transactions(settings.user_id)

if page == "Tổng quan":
    render_dashboard(transactions)
else:
    render_chat_interface()

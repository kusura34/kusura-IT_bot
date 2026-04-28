from __future__ import annotations

import json
import os

import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore_client(firebase_credentials: str | None = None):
    raw_credentials = (firebase_credentials or os.getenv("FIREBASE_CREDENTIALS", "")).strip()
    if not raw_credentials:
        raise ValueError(
            "FIREBASE_CREDENTIALS is missing or empty. "
            "Set FIREBASE_CREDENTIALS to the full Firebase service account JSON string."
        )

    try:
        credentials_data = json.loads(raw_credentials)
    except json.JSONDecodeError as exc:
        raise ValueError("FIREBASE_CREDENTIALS must be a valid JSON string") from exc

    app = firebase_admin.get_app() if firebase_admin._apps else firebase_admin.initialize_app(
        credentials.Certificate(credentials_data)
    )
    return firestore.client(app=app)

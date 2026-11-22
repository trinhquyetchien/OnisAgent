# OnisAgent Flutter app

The assistant screen calls the FastAPI backend at `/api/v1/chat` and displays
the backend intent, route, confidence, status, slots, and quick replies.

## Run the connected stack locally

Terminal 1 — backend:

```bash
cd backend
python3 -m pip install -r requirements.txt
PYTHONPATH=. python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — Flutter web/desktop:

```bash
cd app
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

For an Android emulator, use the host gateway instead:

```bash
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

The API base URL is configurable through `API_BASE_URL`; it defaults to
`http://127.0.0.1:8000` for web, desktop, and iOS simulator testing.

On first launch, the app opens the authentication screen. Register or log in;
the access token is stored locally and attached to chat requests. To enforce
authentication on the backend, set `AUTH_REQUIRED=true` and configure a strong
`AUTH_SECRET`.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

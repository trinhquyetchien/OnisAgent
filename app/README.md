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
flutter run -d emulator-5554 \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000 \
  --dart-define=GOOGLE_APP_CLIENT_ID=431226224662-v9g44g70vla4u4hh6t5ruubkda0elgea.apps.googleusercontent.com
```

The API base URL is configurable through `API_BASE_URL`; it defaults to
`http://127.0.0.1:8000` for web, desktop, and iOS simulator testing.
Google Sign-In uses the Web OAuth Client ID as `serverClientId` on Android and
as `clientId` on Web. The app has the provided Web Client ID as a default, and
`GOOGLE_APP_CLIENT_ID` or `GOOGLE_WEB_CLIENT_ID` can override it at build time.

On first launch, the app opens the authentication screen. Register or log in;
the access token is attached to API requests and the refresh token is stored in
platform secure storage when “Remember me” is enabled. To enforce authentication
on the backend, set `AUTH_REQUIRED=true` and configure a strong `AUTH_SECRET`.

Google sign-in requires the same OAuth Web Client ID in `app/.env` as
`GOOGLE_APP_CLIENT_ID` and in `backend/.env` as `GOOGLE_WEB_CLIENT_ID`.
For local Web development, copy the example config once and start the app with:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Set GOOGLE_APP_CLIENT_ID in .env, then:
.\run_web.ps1
```

The script reads only the needed client ID and API URL from `app/.env`, then
passes them as Flutter build defines and starts Chrome on port `7357`. Add
`http://localhost` and `http://localhost:7357` to the OAuth client's Authorized
JavaScript origins in Google Cloud. These origins are only needed for browser
sign-in, not Android. For Android, configure the Android OAuth client in Google
Cloud for package `com.onis.app` and the SHA-1 fingerprint of the app's signing
key; Flutter passes the Web Client ID as `serverClientId`. Windows and Linux
desktop are not supported by `google_sign_in`.

Set the matching `GOOGLE_WEB_CLIENT_ID` in `backend/.env`. For a physical phone,
set `API_BASE_URL` to the development machine's LAN address instead of
`127.0.0.1`. Email verification and password-reset OTP require SMTP settings in
`backend/.env`; see `backend/.env.example`. Never pass the complete backend
`.env` to Flutter builds or add the SMTP password to source control.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

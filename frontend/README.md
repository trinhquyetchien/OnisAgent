# OnisAgent - Frontend Service (Web Client)

Giao diện Web Cyber Dark Dashboard tích hợp đàm thoại giọng nói tiếng Việt hai chiều (Web Speech STT + Neural TTS) và giám sát thời gian thực số token tiết kiệm.

## Cấu Trúc Thư Mục
```
frontend/
├── index.html            # Giao diện chính (Cyber Dark Dashboard)
├── css/
│   └── style.css         # Bộ stylesheet Cyber Dark
├── js/
│   ├── app.js            # Điều phối trạng thái, tabs, gọi API backend
│   └── voice.js          # Xử lý Web Speech API (nhận diện & phát âm)
├── package.json          # Cấu hình script chạy
└── run_frontend.sh       # Script khởi chạy web server độc lập
```

## Khởi Chạy Frontend Độc Lập
Frontend hoàn toàn tách rời và có thể chạy trên bất kỳ cổng web tĩnh nào:
```bash
# Chạy trên cổng 3000
./frontend/run_frontend.sh 3000

# Hoặc dùng python http.server
python3 -m http.server 3000 --directory frontend

# Hoặc dùng Node.js
npx serve -l 3000 frontend
```

*Lưu ý:* Khi frontend chạy trên cổng khác (ví dụ `:3000`), file `js/app.js` sẽ tự động cấu hình `API_BASE` trỏ về Backend API tại `http://localhost:8000`. Bạn cũng có thể thiết lập `window.API_BASE_URL = "http://dia-chi-ip-backend:8000"` nếu deploy lên server từ xa.

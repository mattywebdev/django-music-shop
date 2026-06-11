# 🎵 Django Music Shop

A full-stack Django web application for browsing and purchasing digital music and merchandise.  
This project simulates a real e-commerce experience with cart management, checkout flow, user accounts, and API endpoints.

---

<img width="1673" height="977" alt="image" src="https://github.com/user-attachments/assets/f5a92e85-c154-4728-ba15-ffa791a77a14" />
<img width="1645" height="980" alt="image" src="https://github.com/user-attachments/assets/83cb9951-02be-4b34-bd9e-cd781b14d58d" />
<img width="359" height="741" alt="image" src="https://github.com/user-attachments/assets/43ee2782-a856-4f82-9d5a-7375560de6e1" />
<img width="362" height="740" alt="image" src="https://github.com/user-attachments/assets/ae9fc1f6-5508-45b6-9bd3-db8d48eb2dee" />




## 🚀 Features

- 🎧 Browse albums, tracks, ambient releases, and merchandise  
- 🛒 Session-based shopping cart (add, update, remove items)  
- 💳 Checkout flow creating orders and order items  
- 👤 User authentication (register, login, logout)  
- ❤️ Favorites system  
- 📦 Account dashboard with order history  
- 🔍 Search suggestions (AJAX)  
- 🔗 REST API endpoints (albums, tracks, search)  
- 🧪 Test coverage included  

---

## 🛠️ Tech Stack

- Python  
- Django  
- Django REST Framework  
- JavaScript (AJAX / fetch)  
- HTML / CSS (Bootstrap)  

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/mattywebdev/django-music-shop.git
cd django-music-shop
```

### 2. Create virtual environment

```bash
python -m venv venv
```

#### Activate it

**Mac/Linux**
```bash
source venv/bin/activate
```

**Windows**
```bash
venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Run migrations

```bash
python manage.py migrate
```

---

### 5. Load demo data
```bash
python manage.py loaddata demo_store_data_professional.json
```
This will populate the store with:

- albums
- tracks
- ambient sounds
- merchandise

The original starter fixture is still available as `demo_store_data_final.json`.

---

### 6. Run the development server
```bash
python manage.py runserver
```
Open:

http://127.0.0.1:8000/

---

## API Endpoints

### 📀 Albums
- `GET /api/albums/`  
  Retrieve all albums

---

### 🎵 Tracks
- `GET /api/tracks/`  
  Retrieve all tracks

- `GET /api/tracks/?artist=<id>`  
  Filter tracks by artist ID

- `GET /api/tracks/?album=<id>`  
  Filter tracks by album ID

- `GET /api/tracks/?q=<query>`  
  Search tracks by title or artist name

- `GET /api/tracks/?ordering=price`  
  Sort tracks (price, -price, title, -title)

---

### ➕ Create Track
- `POST /api/tracks/`

Example body:
```json
{
  "title": "Santa this summer",
  "artist_id": 1,
  "album_id": 5,
  "price": "3.55",
  "duration": "00:11:23"
}
```
---

## 🖼 Demo Media

Sample media files (images and audio previews) are included in the repository so the store loads with working content out of the box.

---

## 🧠 Key Features Explained
Album data is dynamically derived from its related tracks.

- The number of tracks is calculated automatically based on associated records
- Total duration is computed by summing the duration of all tracks

This ensures album data always stays consistent without manual updates.

- Data Relationships
- Albums → Tracks (1-to-many)
- Artists → Albums / Merch
- Generic cart system supporting multiple item types
- Order System
- Supports multiple item types (albums, tracks, merch, ambient)
- Calculates totals dynamically
- Stores order history

---

## 📁 Project Structure

```
music_shop/
├── shop/               # Main app (models, views, cart, orders)
├── media/              # Demo media (images & audio)
├── templates/          # HTML templates
├── static/             # CSS / JS
├── manage.py
└── requirements.txt
```

---

## 🧪 Testing

```bash
python manage.py test
```

---

## ⚠️ Notes

- This project is for learning and portfolio purposes  
- No real payment gateway is integrated  
- Media handling is configured for local development  
- Production/demo deployment reads key settings from environment variables. Copy `.env.example`, set a real `DJANGO_SECRET_KEY`, keep `DJANGO_DEBUG=False`, and configure `DJANGO_ALLOWED_HOSTS` for your domain.

---

## License

Copyright © 2026 Mateusz Obstawski. All rights reserved.

This project is publicly visible for portfolio and review purposes only.
No permission is granted to copy, modify, redistribute, or use this code commercially without written permission.
## 👨‍💻 Author

Mateusz Obstawski  
Self-taught Django developer

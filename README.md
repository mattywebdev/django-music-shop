# 🎵 Django Music Shop

A full-stack Django web application for browsing and purchasing digital music and merchandise.  
This project simulates a real e-commerce experience with cart management, checkout flow, user accounts, and API endpoints.

---

<img width="1351" height="616" alt="image" src="https://github.com/user-attachments/assets/20eeed72-2bf3-4c86-93ef-896ea626dfc0" />
<img width="1265" height="653" alt="image" src="https://github.com/user-attachments/assets/7c5fea32-0c8b-4174-998c-bd5630701de0" />
<img width="1393" height="680" alt="image" src="https://github.com/user-attachments/assets/bd6023a6-af28-406b-924e-a52b402ae5ab" />


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
python manage.py loaddata demo_store_data_final.json
```
This will populate the store with:

albums
tracks
ambient sounds
merchandise

---

### 6. Run the development server
```bash
python manage.py runserver
```
Open:

http://127.0.0.1:8000/

## 📡 API Endpoints

```
/api/albums/
/api/tracks/
/api/search_suggest/
/api/ping/
```

---

## 🖼 Demo Media

Sample media files (images and audio previews) are included in the repository so the store loads with working content out of the box.

---

## 🧠 Key Features Explained
Dynamic Pricing Logic

Tracks can inherit pricing from albums or define their own custom price.

Data Relationships
Albums → Tracks (1-to-many)
Artists → Albums / Merch
Generic cart system supporting multiple item types
Order System
Supports multiple item types (albums, tracks, merch, ambient)
Calculates totals dynamically
Stores order history

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

---

## 👨‍💻 Author

Mateusz Obstawski  
Self-taught Django developer

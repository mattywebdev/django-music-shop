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

### 5. Run the server

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---

## 📡 API Endpoints

```
/api/albums/
/api/tracks/
/api/search_suggest/
/api/ping/
```

---

## 📁 Project Structure

```
music_shop/
├── shop/               # Main app (models, views, cart, orders)
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

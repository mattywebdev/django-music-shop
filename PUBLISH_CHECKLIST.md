# Publish Checklist for Django Music Shop

## 1) Clean the repository
- Remove `htmlcov/`
- Remove `.coverage`
- Remove all `__pycache__/` folders
- Make sure no real secrets or private data are included

## 2) Add missing repo files
- Add `README.md`
- Add `requirements.txt`
- Keep a clean `.gitignore`

## 3) Fix code issues before publishing
- Remove duplicate `account_dashboard` definition in `shop/account_views.py`
- Remove duplicated `unit_price` field in `OrderItem` in `shop/models.py`
- Fix or remove `album_list` in `shop/views.py` because `ProductSerializer` is not imported
- Remove duplicated URL patterns in `shop/urls.py`

## 4) Improve settings
- Move `SECRET_KEY` to an environment variable
- Set `DEBUG` from environment
- Add a sensible local/dev fallback only if needed
- Configure `ALLOWED_HOSTS` for deployment

## 5) Create requirements file
In your project root, run:

```bash
pip freeze > requirements.txt
```

Then review it and make sure it includes at least:
- Django
- djangorestframework
- django-crispy-forms
- Pillow

## 6) Recommended git workflow
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/django-music-shop.git
git push -u origin main
```

## 7) Nice upgrades after upload
- Add screenshots to the README
- Pin important dependencies
- Add a short architecture / feature summary to your CV
- Consider deploying a demo version later

# Instagram SMM Dashboard

Веб-інтерфейс для моніторингу та аналізу Instagram акаунту.

## Структура

```
src/dashboard/
├── __init__.py           # Ініціалізація модуля
├── app.py                # Flask додаток
├── routes.py             # Маршрути та API endpoints
├── templates/            # HTML шаблони
│   ├── base.html        # Базовий шаблон
│   ├── index.html       # Головна сторінка
│   ├── posts.html       # Публікації
│   ├── analytics.html   # Аналітика
│   ├── competitors.html # Конкуренти
│   ├── settings.html    # Налаштування
│   └── reports.html     # Звіти
└── static/              # Статичні файли
    ├── css/
    │   └── style.css    # Стилі
    └── js/
        └── charts.js    # Графіки Plotly
```

## Функціонал

### Головна сторінка (/)
- Ключові метрики (підписники, engagement, охоплення, публікації)
- Графік динаміки engagement
- AI рекомендації
- Топ публікації
- Останні публікації

### Публікації (/posts)
- Перегляд усіх публікацій з фільтрами
- Пагінація
- Експорт в CSV
- Метрики кожної публікації

### Аналітика (/analytics)
- Графік зростання підписників
- Охоплення та покази
- Engagement rate
- Лайки та коментарі
- Топ публікації
- Топ хештеги

### Конкуренти (/competitors)
- Порівняння підписників
- Порівняння engagement rate
- Активність публікацій
- Детальна таблиця

### Звіти (/reports)
- Генерація тижневих, місячних, квартальних звітів
- Експорт даних
- Ключові висновки

### Налаштування (/settings)
- Цілі та таргети
- Налаштування акаунту
- Список конкурентів
- Telegram сповіщення
- Управління даними

## API Endpoints

- `GET /api/metrics?period=<7d|30d|90d>` - Основні метрики
- `GET /api/engagement?period=<period>` - Дані engagement
- `GET /api/top-posts?period=<period>&limit=<n>` - Топ публікації
- `GET /api/competitors-comparison` - Порівняння конкурентів
- `GET /api/hashtags?limit=<n>` - Топ хештеги
- `GET /api/export/posts?period=<period>` - Експорт публікацій (CSV)
- `GET /api/export/stats?period=<period>` - Експорт статистики (CSV)
- `POST /api/generate-report` - Генерація звіту

## Технології

- **Backend**: Flask 3.0+
- **Frontend**: Bootstrap 5
- **Charts**: Plotly
- **Database**: SQLAlchemy
- **Icons**: Bootstrap Icons

## Особливості

### Теми
- Світла/темна тема з перемиканням
- Збереження вибору в localStorage
- Автоматичне оновлення графіків

### Responsive Design
- Адаптивний дизайн для всіх пристроїв
- Mobile-friendly інтерфейс

### Ukrainian Language
- Весь інтерфейс українською мовою
- Локалізовані формати дат

## Запуск

```bash
# З кореневої директорії проекту
python run_dashboard.py
```

Або:

```bash
# Безпосередньо через Flask
python -m flask --app src.dashboard.app:create_app run --host=0.0.0.0 --port=5000
```

Dashboard буде доступний за адресою: http://localhost:5000

## Конфігурація

Налаштування через змінні середовища (.env):

```env
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
DEBUG=False
```

## Використання

1. Переконайтеся, що база даних містить дані
2. Запустіть dashboard
3. Відкрийте браузер на http://localhost:5000
4. Перемикайте між сторінками через навігацію
5. Використовуйте фільтри періодів для різних звітів
6. Експортуйте дані в CSV за потреби

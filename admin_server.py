from flask import Flask, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "bot_database.db"

def get_paid_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.user_id,
            u.username,
            u.full_name,
            u.role,
            u.is_privileged,
            u.phone_1,
            s.start_date,
            s.end_date,
            s.is_active,
            s.role as subscription_role,
            CASE 
                WHEN s.role = 'model' THEN 100
                WHEN s.role = 'customer' THEN 500
                ELSE 0
            END as amount
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.payment_id IS NOT NULL 
        AND s.payment_id != 'trial'
        ORDER BY s.start_date DESC
    """)
    
    users = cursor.fetchall()
    conn.close()
    return users

HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>Админ панель</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 32px; color: #333; margin-bottom: 10px; }
        .header p { color: #666; }
        .time { 
            color: #10b981; 
            font-size: 14px; 
            margin-top: 10px;
            font-weight: bold;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        .stat-item h3 { color: #667eea; font-size: 28px; }
        .stat-item p { color: #666; font-size: 14px; margin-top: 5px; }
        .table-box {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-size: 14px;
        }
        td { padding: 15px; border-bottom: 1px solid #eee; font-size: 14px; }
        tr:hover { background: #f5f5f5; }
        .badge {
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        }
        .badge.customer { background: #dbeafe; color: #1e40af; }
        .badge.model { background: #fce7f3; color: #be185d; }
        .badge.privileged { background: #fef3c7; color: #92400e; }
        .badge.regular { background: #e5e7eb; color: #4b5563; }
        .badge.active { background: #d1fae5; color: #065f46; }
        .badge.inactive { background: #fee2e2; color: #991b1b; }
        .amount { color: #10b981; font-weight: bold; font-size: 16px; }
        .no-data { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💳 Админ панель</h1>
            <p>Платные подписки</p>
            <div class="time">🔄 {{ update_time }}</div>
            <p style="font-size: 12px; color: #999; margin-top: 5px;">Автообновление каждые 30 сек</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <h3>{{ total_users }}</h3>
                <p>Всего платежей</p>
            </div>
            <div class="stat-item">
                <h3>{{ total_models }}</h3>
                <p>Моделей</p>
            </div>
            <div class="stat-item">
                <h3>{{ total_customers }}</h3>
                <p>Заказчиков</p>
            </div>
            <div class="stat-item">
                <h3>{{ total_revenue }} ₽</h3>
                <p>Доход</p>
            </div>
        </div>
        
        <div class="table-box">
            {% if users %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Имя</th>
                        <th>Телефон</th>
                        <th>Роль</th>
                        <th>Статус</th>
                        <th>Сумма</th>
                        <th>Оплачено</th>
                        <th>До</th>
                        <th>Активность</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td><b>{{ u[0] }}</b></td>
                        <td>{% if u[1] %}@{{ u[1] }}{% else %}нет{% endif %}</td>
                        <td>{% if u[2] %}{{ u[2] }}{% else %}-{% endif %}</td>
                        <td>{% if u[5] %}{{ u[5] }}{% else %}-{% endif %}</td>
                        <td>
                            {% if u[9] == 'customer' %}
                                <span class="badge customer">Заказчик</span>
                            {% else %}
                                <span class="badge model">Модель</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if u[9] == 'model' %}
                                {% if u[4] == 1 %}
                                    <span class="badge privileged">Привилегированная</span>
                                {% else %}
                                    <span class="badge regular">Обычная</span>
                                {% endif %}
                            {% else %}
                                <span class="badge customer">Подписка</span>
                            {% endif %}
                        </td>
                        <td class="amount">{{ u[10] }} ₽</td>
                        <td>{% if u[6] %}{{ u[6][:16] }}{% else %}-{% endif %}</td>
                        <td>{% if u[7] %}{{ u[7][:16] }}{% else %}-{% endif %}</td>
                        <td>
                            {% if u[8] == 1 %}
                                <span class="badge active">Активна</span>
                            {% else %}
                                <span class="badge inactive">Истекла</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="no-data">
                <h3>📭 Нет платежей</h3>
                <p>Данные появятся после первой оплаты</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    users = get_paid_users()
    
    total_users = len(users)
    total_models = len([u for u in users if u[9] == 'model'])
    total_customers = len([u for u in users if u[9] == 'customer'])
    total_revenue = sum([u[10] for u in users])
    
    return render_template_string(HTML,
                                 users=users,
                                 total_users=total_users,
                                 total_models=total_models,
                                 total_customers=total_customers,
                                 total_revenue=total_revenue,
                                 update_time=datetime.now().strftime('%d.%m.%Y %H:%M:%S'))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Админ-панель запущена!")
    print("📍 Открой: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
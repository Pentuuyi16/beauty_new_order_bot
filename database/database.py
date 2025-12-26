import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    role TEXT NOT NULL,
                    full_name TEXT,
                    city TEXT,
                    district TEXT,
                    phone_1 TEXT,
                    phone_2 TEXT,
                    activity_type TEXT,
                    address TEXT,
                    photo_id TEXT,
                    age INTEGER,
                    height INTEGER,
                    skin_type TEXT,
                    contraindications TEXT,
                    available_days TEXT,
                    experience TEXT,
                    photo_video_agree BOOLEAN,
                    portfolio_ids TEXT,
                    is_privileged BOOLEAN DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_blocked BOOLEAN DEFAULT 0,
                    gdpr_consent BOOLEAN DEFAULT 0
                )
            """)
            
            # Таблица заявок заказчиков
            await db.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT NOT NULL,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    requirements TEXT,
                    models_needed INTEGER NOT NULL,
                    experience_required BOOLEAN,
                    viewers_count INTEGER,
                    photo_video TEXT,
                    materials_payment TEXT,
                    participation_type TEXT NOT NULL,
                    payment_amount TEXT,
                    dress_code TEXT,
                    comment TEXT,
                    message_id INTEGER,
                    is_closed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица заявок моделей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    district TEXT NOT NULL,
                    category TEXT NOT NULL,
                    zones TEXT NOT NULL,
                    time_range TEXT NOT NULL,
                    photo_video TEXT,
                    participation_type TEXT NOT NULL,
                    note TEXT,
                    message_id INTEGER,
                    is_closed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица откликов моделей на заявки заказчиков
            await db.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    model_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id),
                    FOREIGN KEY (model_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица откликов заказчиков на заявки моделей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS customer_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_application_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_application_id) REFERENCES model_applications(id),
                    FOREIGN KEY (customer_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица рейтингов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    rater_id INTEGER NOT NULL,
                    rated_id INTEGER NOT NULL,
                    came BOOLEAN,
                    prepared BOOLEAN,
                    requirements_met BOOLEAN,
                    work_again BOOLEAN,
                    location_convenient BOOLEAN,
                    conditions_met BOOLEAN,
                    attitude_correct BOOLEAN,
                    cooperate_again BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications(id),
                    FOREIGN KEY (rater_id) REFERENCES users(user_id),
                    FOREIGN KEY (rated_id) REFERENCES users(user_id)
                )
            """)

            # Таблица подписок
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    payment_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            await db.commit()
    
    # ============== USERS ==============
    
    async def migrate_subscriptions_add_role(self):
        """Добавить поле role в таблицу subscriptions"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем есть ли уже колонка role
            async with db.execute("PRAGMA table_info(subscriptions)") as cursor:
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'role' not in column_names:
                    # Добавляем колонку role
                    await db.execute("ALTER TABLE subscriptions ADD COLUMN role TEXT DEFAULT 'model'")
                    await db.commit()
                    print("✅ Добавлена колонка role в таблицу subscriptions")

    async def add_user(self, user_id: int, username: str, role: str):
        """Добавить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, role) VALUES (?, ?, ?)",
                (user_id, username, role)
            )
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_user(self, user_id: int, **kwargs):
        """Обновить данные пользователя"""
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE users SET {fields} WHERE user_id = ?",
                values
            )
            await db.commit()
    
    async def get_user_role(self, user_id: int) -> Optional[str]:
        """Получить роль пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def block_user(self, user_id: int):
        """Заблокировать пользователя"""
        await self.update_user(user_id, is_blocked=True)
    
    async def unblock_user(self, user_id: int):
        """Разблокировать пользователя"""
        await self.update_user(user_id, is_blocked=False)
    
    async def set_privileged(self, user_id: int, status: bool):
        """Установить привилегированный статус модели"""
        await self.update_user(user_id, is_privileged=status)
    
    # ============== APPLICATIONS ==============
    
    async def create_application(self, customer_id: int, **kwargs) -> int:
        """Создать заявку заказчика"""
        fields = ", ".join(["customer_id"] + list(kwargs.keys()))
        placeholders = ", ".join(["?"] * (len(kwargs) + 1))
        values = [customer_id] + list(kwargs.values())
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"INSERT INTO applications ({fields}) VALUES ({placeholders})",
                values
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Получить заявку"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM applications WHERE id = ?", (app_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_application(self, app_id: int, **kwargs):
        """Обновить заявку"""
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [app_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE applications SET {fields} WHERE id = ?",
                values
            )
            await db.commit()
    
    async def get_customer_applications(self, customer_id: int) -> List[Dict[str, Any]]:
        """Получить все заявки заказчика"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM applications WHERE customer_id = ? ORDER BY created_at DESC",
                (customer_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def close_application(self, app_id: int):
        """Закрыть набор на заявку"""
        await self.update_application(app_id, is_closed=True)
    
    async def get_all_active_applications(self) -> List[Dict[str, Any]]:
        """Получить все активные заявки"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM applications WHERE is_closed = 0 ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            
    async def get_active_applications_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Получить активные заявки по категории"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM applications WHERE is_closed = 0 AND category = ? ORDER BY created_at DESC",
                (category,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    # ============== MODEL APPLICATIONS ==============
    
    async def create_model_application(self, model_id: int, **kwargs) -> int:
        """Создать заявку модели"""
        fields = ", ".join(["model_id"] + list(kwargs.keys()))
        placeholders = ", ".join(["?"] * (len(kwargs) + 1))
        values = [model_id] + list(kwargs.values())
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"INSERT INTO model_applications ({fields}) VALUES ({placeholders})",
                values
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_model_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Получить заявку модели"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM model_applications WHERE id = ?", (app_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_model_application(self, app_id: int, **kwargs):
        """Обновить заявку модели"""
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [app_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE model_applications SET {fields} WHERE id = ?",
                values
            )
            await db.commit()
    
    async def get_model_applications_by_model(self, model_id: int) -> List[Dict[str, Any]]:
        """Получить заявки модели"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM model_applications WHERE model_id = ? ORDER BY created_at DESC",
                (model_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    # ============== RESPONSES ==============
    
    async def add_response(self, application_id: int, model_id: int) -> int:
        """Добавить отклик модели на заявку заказчика"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO responses (application_id, model_id) VALUES (?, ?)",
                (application_id, model_id)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def check_response_exists(self, application_id: int, model_id: int) -> bool:
        """Проверить, есть ли уже отклик"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id FROM responses WHERE application_id = ? AND model_id = ?",
                (application_id, model_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row is not None
    
    async def get_response(self, response_id: int) -> Optional[Dict[str, Any]]:
        """Получить отклик"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM responses WHERE id = ?", (response_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_response_status(self, response_id: int, status: str):
        """Обновить статус отклика"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE responses SET status = ? WHERE id = ?",
                (status, response_id)
            )
            await db.commit()
    
    async def get_application_responses(self, application_id: int) -> List[Dict[str, Any]]:
        """Получить все отклики на заявку"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM responses WHERE application_id = ?",
                (application_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_model_responses(self, model_id: int) -> List[Dict[str, Any]]:
        """Получить все отклики модели"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM responses WHERE model_id = ? ORDER BY created_at DESC",
                (model_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def count_responses(self, application_id: int) -> int:
        """Подсчитать количество откликов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM responses WHERE application_id = ?",
                (application_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    # ============== CUSTOMER RESPONSES ==============
    
    async def add_customer_response(self, model_application_id: int, customer_id: int) -> int:
        """Добавить отклик заказчика на заявку модели"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO customer_responses (model_application_id, customer_id) VALUES (?, ?)",
                (model_application_id, customer_id)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def check_customer_response_exists(self, model_application_id: int, customer_id: int) -> bool:
        """Проверить, есть ли уже отклик заказчика"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id FROM customer_responses WHERE model_application_id = ? AND customer_id = ?",
                (model_application_id, customer_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row is not None
    
    async def get_model_application_responses(self, model_application_id: int) -> List[Dict[str, Any]]:
        """Получить все отклики на заявку модели"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM customer_responses WHERE model_application_id = ?",
                (model_application_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    # ============== RATINGS ==============
    
    async def add_rating(self, **kwargs):
        """Добавить рейтинг"""
        fields = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        values = list(kwargs.values())
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"INSERT INTO ratings ({fields}) VALUES ({placeholders})",
                values
            )
            await db.commit()
    
    async def calculate_rating(self, user_id: int) -> float:
        """Рассчитать средний рейтинг пользователя (используем calculate_simple_rating)"""
        return await self.calculate_simple_rating(user_id)
    
    # ============== SUBSCRIPTIONS ==============
    
    async def add_subscription(self, user_id: int, days: int, payment_id: str = None, role: str = "model") -> int:
        """Добавить подписку для конкретной роли"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now() + timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO subscriptions (user_id, end_date, payment_id, role) VALUES (?, ?, ?, ?)",
                (user_id, end_date.isoformat(), payment_id, role)
            )
            await db.commit()
            
            # Обновляем статус привилегированной модели только если это подписка модели
            if role == "model":
                await self.update_user(user_id, is_privileged=True)
            
            return cursor.lastrowid
    
    async def get_active_subscription(self, user_id: int, role: str = None):
        """Получить активную подписку пользователя для конкретной роли"""
        from datetime import datetime
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if role:
                # Ищем подписку для конкретной роли
                query = """
                    SELECT * FROM subscriptions 
                    WHERE user_id = ? AND role = ? AND is_active = 1 AND end_date > ? 
                    ORDER BY end_date DESC LIMIT 1
                """
                params = (user_id, role, datetime.now().isoformat())
            else:
                # Ищем любую активную подписку (для обратной совместимости)
                query = """
                    SELECT * FROM subscriptions 
                    WHERE user_id = ? AND is_active = 1 AND end_date > ? 
                    ORDER BY end_date DESC LIMIT 1
                """
                params = (user_id, datetime.now().isoformat())
            
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def check_subscription_expired(self, user_id: int) -> bool:
        """Проверить истекла ли подписка МОДЕЛИ"""
        subscription = await self.get_active_subscription(user_id, role="model")
        
        if not subscription:
            # Если нет активной подписки модели, убираем привилегии
            await self.update_user(user_id, is_privileged=False)
            return True
        
        return False
    
    async def deactivate_subscription(self, subscription_id: int):
        """Деактивировать подписку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE subscriptions SET is_active = 0 WHERE id = ?",
                (subscription_id,)
            )
            await db.commit()
    
    async def get_subscription_info(self, user_id: int) -> dict:
        """Получить информацию о подписке МОДЕЛИ"""
        from datetime import datetime
        
        subscription = await self.get_active_subscription(user_id, role="model")
        
        if not subscription:
            return {
                'has_subscription': False,
                'days_left': 0,
                'end_date': None
            }
        
        end_date = datetime.fromisoformat(subscription['end_date'])
        days_left = (end_date - datetime.now()).days
        
        return {
            'has_subscription': True,
            'days_left': max(0, days_left),
            'end_date': end_date.strftime('%d.%m.%Y')
        }
    
    async def get_customer_subscription_info(self, user_id: int) -> dict:
        """Получить информацию о подписке ЗАКАЗЧИКА"""
        from datetime import datetime
        
        subscription = await self.get_active_subscription(user_id, role="customer")
        
        if not subscription:
            return {
                'has_subscription': False,
                'days_left': 0,
                'end_date': None
            }
        
        end_date = datetime.fromisoformat(subscription['end_date'])
        days_left = (end_date - datetime.now()).days
        
        return {
            'has_subscription': True,
            'days_left': max(0, days_left),
            'end_date': end_date.strftime('%d.%m.%Y')
        }
    
    async def check_customer_subscription(self, user_id: int) -> bool:
        """Проверить есть ли у заказчика активная подписка"""
        subscription = await self.get_active_subscription(user_id, role="customer")
        
        if not subscription:
            return False
        
        from datetime import datetime
        end_date = datetime.fromisoformat(subscription['end_date'])
        
        if datetime.now() > end_date:
            return False
        
        return True
    
    async def delete_user(self, user_id: int):
        """Удалить пользователя из БД (для смены роли)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем только пользователя, остальное удалится автоматически через CASCADE
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await db.commit()
    
    async def delete_user_keep_subscription(self, user_id: int):
        """Удалить данные пользователя, но сохранить подписку"""
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем только пользователя, подписки остаются в таблице subscriptions
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await db.commit()
    
    async def add_simple_rating(self, rater_id: int, rated_id: int, rating: int):
        """Добавить простую оценку от 1 до 10"""
        async with aiosqlite.connect(self.db_path) as db:
            # Создаем фиктивный application_id = 0 для простых оценок
            await db.execute("""
                INSERT INTO ratings (application_id, rater_id, rated_id, 
                    came, prepared, requirements_met, work_again,
                    location_convenient, conditions_met, attitude_correct, cooperate_again)
                VALUES (0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rater_id, rated_id, 
                  rating >= 8, rating >= 8, rating >= 8, rating >= 8,
                  rating >= 8, rating >= 8, rating >= 8, rating >= 8))
            await db.commit()
    
    async def check_simple_rating_exists(self, rater_id: int, rated_id: int) -> bool:
        """Проверить, оставлял ли уже оценку"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id FROM ratings WHERE rater_id = ? AND rated_id = ?
            """, (rater_id, rated_id)) as cursor:
                result = await cursor.fetchone()
                return result is not None
    
    async def calculate_simple_rating(self, user_id: int) -> float:
        """Вычислить средний рейтинг из простых оценок"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT AVG(
                    (CAST(came AS REAL) + CAST(prepared AS REAL) + 
                     CAST(requirements_met AS REAL) + CAST(work_again AS REAL) +
                     CAST(location_convenient AS REAL) + CAST(conditions_met AS REAL) +
                     CAST(attitude_correct AS REAL) + CAST(cooperate_again AS REAL)) / 8.0 * 10
                ) as avg_rating
                FROM ratings WHERE rated_id = ?
            """, (user_id,)) as cursor:
                result = await cursor.fetchone()
                return round(result[0], 1) if result and result[0] else 0.0
    
    async def get_simple_ratings_count(self, user_id: int) -> int:
        """Получить количество оценок"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM ratings WHERE rated_id = ?
            """, (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def add_response_rating(self, response_id: int, rater_id: int, rated_id: int, rating: int):
        """Добавить оценку привязанную к конкретному отклику"""
        async with aiosqlite.connect(self.db_path) as db:
            # application_id = response_id для привязки к отклику
            await db.execute("""
                INSERT INTO ratings (application_id, rater_id, rated_id, 
                    came, prepared, requirements_met, work_again,
                    location_convenient, conditions_met, attitude_correct, cooperate_again)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (response_id, rater_id, rated_id, 
                  rating >= 8, rating >= 8, rating >= 8, rating >= 8,
                  rating >= 8, rating >= 8, rating >= 8, rating >= 8))
            await db.commit()
    
    async def check_trial_used(self, user_id: int, role: str) -> bool:
   
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id FROM subscriptions 
                WHERE user_id = ? AND role = ? AND payment_id = 'trial'
            """, (user_id, role)) as cursor:
                result = await cursor.fetchone()
                return result is not None

    async def activate_trial_subscription(self, user_id: int, role: str, days: int = 30) -> int:
        """Активировать пробную подписку"""
        from datetime import datetime, timedelta
    
        end_date = datetime.now() + timedelta(days=days)
    
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO subscriptions (user_id, end_date, payment_id, role) VALUES (?, ?, ?, ?)",
                (user_id, end_date.isoformat(), 'trial', role)
            )
            await db.commit()
        
        # Обновляем статус привилегированной модели только если это подписка модели
            if role == "model":
                await self.update_user(user_id, is_privileged=True)
        
            return cursor.lastrowid

    async def check_response_rating_exists(self, response_id: int, rater_id: int) -> bool:
        """Проверить, оставлял ли уже оценку за этот отклик"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id FROM ratings WHERE application_id = ? AND rater_id = ?
            """, (response_id, rater_id)) as cursor:
                result = await cursor.fetchone()
                return result is not None
            
    
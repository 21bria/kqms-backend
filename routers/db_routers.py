# db_routers.py
class KQMSRouter:
    route_apps = {'kqms'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_apps:
            return 'kqms_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_apps:
            return 'kqms_db'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_apps:
            return db == 'kqms_db'
        return None  # pastikan app lain tidak bermigrasi ke kqms_db

class KSafeRouter:
    """
    Router untuk app 'ksafe' → database 'ksafe_db'
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'ksafe':
            return 'ksafe_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'ksafe':
            return 'ksafe_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'ksafe' or obj2._meta.app_label == 'ksafe':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'ksafe':
            return db == 'ksafe_db'
        return None

class AuthRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label in ['auth', 'admin', 'contenttypes', 'sessions']:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in ['auth', 'admin', 'contenttypes', 'sessions']:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in ['auth', 'admin', 'contenttypes', 'sessions']:
            return db == 'default'
        return None


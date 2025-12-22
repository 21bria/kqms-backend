# db_routers.py
class DefaultRouter:
    """
    Semua infra & core app → main_db (default)
    """
    route_app_labels = {
        'auth',
        'admin',
        'contenttypes',
        'sessions',
        'django_celery_beat',
         'account',
        'file_manager',
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, **hints):
        if app_label in self.route_app_labels:
            return db == 'default'
        return None

class KQMSRouter:
    """
    Semua domain KQMS → kqms_db
    """
    route_app_labels = {
        'kqms',
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'kqms_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'kqms_db'
        return None

    def allow_migrate(self, db, app_label, **hints):
        if app_label in self.route_app_labels:
            return db == 'kqms_db'
        return None

from rest_framework import exceptions


class BaseRepository:
    """
    Base repository class for interacting with Django models.
    Provides common CRUD operations for database interactions.
    """

    def __init__(self, model):
        self.model = model

    def create(self, values: dict):
        """Creates a new object in the database."""
        obj = self.model(**values)
        obj.save()
        return obj

    def get_first(self, filters=None, error=True, err_detail="Not Found"):
        """
        Retrieves the first object that matches the filter criteria.
        """
        filters = dict(filters or [])
        obj = self.model.objects.filter(**filters).first()
        if error and not obj:
            raise exceptions.NotFound(detail=err_detail)
        return obj

    def get_latest(self, filters=None, error=True, err_detail="Not Found"):
        """
        Gets the latest object based on creation date (requires `created_at` field).
        """
        filters = dict(filters or [])
        obj = self.model.objects.filter(**filters).order_by('-created_at').first()
        if error and not obj:
            raise exceptions.NotFound(detail=err_detail)
        return obj

    def get_all(self, filters=None, error=True, err_detail="Not Found"):
        """
        Retrieves all objects matching the filters.
        """
        filters = dict(filters or [])
        queryset = self.model.objects.filter(**filters)
        if error and not queryset.exists():
            raise exceptions.NotFound(detail=err_detail)
        return queryset

    def query(self, filters=None):
        """
        Returns a queryset filtered based on the given conditions.
        """
        filters = dict(filters or [])
        return self.model.objects.filter(**filters)

    def update_where(self, filters: list, updates: list):
        """
        Updates objects matching the filters with the provided updates.
        """
        return self.model.objects.filter(**dict(filters)).update(**dict(updates))

    def delete_where(self, filters: list):
        """
        Deletes objects that match the given filters.
        """
        return self.model.objects.filter(**dict(filters)).delete()

    def create_or_update(self, filters: list, values: dict):
        """
        Creates a new object or updates an existing one based on the filters.
        """
        obj = self.get_first(filters=filters, error=False)
        if obj:
            for key, value in values.items():
                setattr(obj, key, value)
            obj.save()
        else:
            obj = self.create(values)
        return obj

    def create_or_update_v2(self, filters: list, values: dict):
        filter_dict = dict(filters)
        
        obj, created = self.model.objects.update_or_create(defaults=values, **filter_dict)
        
        return obj

from django.db import models
from django.contrib.gis.db import models as geomodels

# For Mines Sources
class SourceMines(models.Model):
    sources_area = models.CharField(max_length=50, unique=True)
    remarks      = models.CharField(max_length=255, default=None, null=True, blank=True)
    category     = models.CharField(max_length=25, default=None, null=True, blank=True)
    status       = models.IntegerField(default=None, null=True, blank=True)
    latitude     = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    longitude    = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    geometry     = geomodels.PolygonField(null=True, blank=True)  # area loading point
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sources_area

    class Meta:
        db_table = 'mine_sources'
        app_label= 'kqms'
    
    indexes = [
        models.Index(fields=['sources_area'])
    ]

class SourceMinesLoading(models.Model):
    loading_point = models.CharField(max_length=50, unique=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    category      = models.CharField(max_length=25, default=None, null=True, blank=True)
    id_sources    = models.ForeignKey(
        SourceMines, 
        related_name='mine_sources_point_loading_sources_FK', 
        on_delete=models.SET_NULL,null=True,blank=True,db_column='id_sources' 
    )
    status        = models.IntegerField(default=None, null=True, blank=True)
    latitude      = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    longitude     = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    geometry      = geomodels.PolygonField(null=True, blank=True)  # area loading point
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loading_point

    class Meta:
        db_table = 'mine_sources_point_loading'
        app_label= 'kqms'
    
    indexes = [
        models.Index(fields=['loading_point'])
    ]

class SourceMinesDumping(models.Model):
    dumping_point = models.CharField(max_length=50, unique=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    category      = models.CharField(max_length=25, default=None, null=True, blank=True)
    compositing   = models.CharField(max_length=5, default=None, null=True, blank=True)
    status        = models.IntegerField(default=None, null=True, blank=True)
    geometry      = geomodels.PolygonField(null=True, blank=True)
    latitude      = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    longitude     = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.dumping_point
    
    def save(self, *args, **kwargs):
        if self.geometry:
            centroid = self.geometry.centroid
            self.latitude = centroid.y
            self.longitude = centroid.x
        super().save(*args, **kwargs)


    class Meta:
        db_table = 'mine_sources_point_dumping'
        app_label= 'kqms'

    indexes = [
        models.Index(fields=['dumping_point'])
    ]

class SourceMinesDome(models.Model):
    pile_id     = models.CharField(max_length=50, unique=True)
    remarks     = models.CharField(max_length=255, default=None, null=True, blank=True)
    category    = models.CharField(max_length=25, default=None, null=True, blank=True)
    compositing = models.CharField(max_length=15, default=None, null=True, blank=True)
    dome_finish = models.CharField(max_length=25, default=None, null=True, blank=True)
    status_dome = models.CharField(max_length=15, default=None, null=True, blank=True)
    plan_ni_min = models.FloatField(default=None, null=True, blank=True)
    plan_ni_max = models.FloatField(default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    direct_sale = models.CharField(max_length=10,default=None, null=True, blank=True)
    id_dumping  = models.BigIntegerField(default=None, null=True, blank=True)
    latitude    = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    geometry    = geomodels.PolygonField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pile_id
    
    def save(self, *args, **kwargs):
        if self.geometry:
            centroid = self.geometry.centroid
            self.latitude = centroid.y
            self.longitude = centroid.x
        super().save(*args, **kwargs)


    class Meta:
        db_table = 'mine_sources_point_dome'
        app_label= 'kqms'
    
    indexes = [
        models.Index(fields=['pile_id'])
    ]

class detailsDome(models.Model):
    pile_id       = models.CharField(max_length=50,default=None, null=True, blank=True)
    dumping_point = models.CharField(max_length=50,default=None, null=True, blank=True)
    remarks       = models.CharField(max_length=255, default=None, null=True, blank=True)
    category      = models.CharField(max_length=25, default=None, null=True, blank=True)
    compositing   = models.CharField(max_length=15, default=None, null=True, blank=True)
    dome_finish   = models.CharField(max_length=25, default=None, null=True, blank=True)
    status_dome   = models.CharField(max_length=15, default=None, null=True, blank=True)
    plan_ni_min   = models.FloatField(default=None, null=True, blank=True)
    plan_ni_max   = models.FloatField(default=None, null=True, blank=True)
    status        = models.IntegerField(default=None, null=True, blank=True)
    direct_sale   = models.CharField(max_length=10,default=None, null=True, blank=True)
    id_dumping    = models.BigIntegerField(default=None, null=True, blank=True)

    

    class Meta:
        managed   = False
        db_table  = 'dome_point_details'
        app_label = 'kqms'
    


from django.contrib import admin

from . import models as erp_models

# Accounts
admin.site.register(erp_models.Librarian)
admin.site.register(erp_models.Subscriber)

# Library resources
admin.site.register(erp_models.Author)
admin.site.register(erp_models.Genre)
admin.site.register(erp_models.GenericBook)
admin.site.register(erp_models.Book)
admin.site.register(erp_models.Rental)
admin.site.register(erp_models.Booking)

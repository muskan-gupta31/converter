# djg/urls.py
from django.urls import path
from .views import PassportSheetView, ConverterView

urlpatterns = [
    path('', PassportSheetView.as_view(), name='home'),  # Root URL shows passport form
    path('photocollage/', PassportSheetView.as_view(), name='passport_sheet'),  # Your existing API
    path('converter/', ConverterView.as_view(), name='converter'),  # New converter endpoint
]
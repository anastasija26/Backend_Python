from django.urls import path

from .views import (
    CollectDetailAPIView,
    CollectListCreateAPIView,
    PaymentDetailAPIView,
    PaymentListCreateAPIView,
)

urlpatterns = [
    path("collects/", CollectListCreateAPIView.as_view(), name="collect-list-create"),
    path("collects/<int:pk>/", CollectDetailAPIView.as_view(), name="collect-detail-update-destroy"),
    path("collects/<int:collect_id>/payments/", PaymentListCreateAPIView.as_view(), name="payment-list-create"),
    path("payments/<int:pk>/", PaymentDetailAPIView.as_view(), name="payment-detail-update-destroy"),
]
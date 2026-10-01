from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "buyer", "final_amount", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("order_number", "buyer__email", "buyer__phone")
    inlines = [OrderItemInline, OrderStatusHistoryInline]

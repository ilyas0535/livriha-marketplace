from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Cart, CartItem, Wishlist

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'price', 'quantity', 'created_at']
    list_filter = ['shop', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)


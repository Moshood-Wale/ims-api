from rest_framework import serializers
from .models import ProductInventory, Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True}
        }


class ProductInventorySerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    default_quantity = serializers.CharField()
    current_quantity = serializers.CharField()
    
    class Meta:
        model = ProductInventory
        fields = ("name", "default_quantity", "current_quantity", "cost_price", "selling_price", 
                    "minimum_stock_quantity", "labels", "category", "low_quantity", "created_by",)
        extra_kwargs = {
            "id": {"read_only": True}
        }

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        user = self.context["request"].user
        name = attrs.get("name", None)
        minimum_stock_quantity = attrs.get("minimum_stock_quantity") or 0
        current_quantity = attrs.get("current_quantity") or 0
        
        if instance is None or not instance.name == name:
            product_qs = ProductInventory.objects.filter(created_by=user)
            if name and product_qs.filter(name=name).exists():
                raise serializers.ValidationError("Product with this name already exist")
            if int(minimum_stock_quantity) > int(current_quantity):
                raise serializers.ValidationError("minimum stock quantity is higher than current quantity") 
        
        return super().validate(attrs)      
    
    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        if not validated_data.get("minimum_stock_quantity"):
            validated_data["minimum_stock_quantity"] = 0
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data['current_quantity'] = validated_data["default_quantity"]
        if not validated_data.get("minimum_stock_quantity"):
            validated_data["minimum_stock_quantity"] = 0
        return super().update(instance, validated_data)


class ProductListInventorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductInventory
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
            "created_by": {"read_only": True},
        }


class RestockProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()

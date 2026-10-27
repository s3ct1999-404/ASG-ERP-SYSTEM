from __future__ import annotations

from rest_framework import serializers

from tenancy.models import Branch, Company, Membership, Role, RoleAssignment


class CompanySerializer(serializers.ModelSerializer[Company]):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "base_currency",
            "tin",
            "vat_registered",
            "allow_negative_stock",
            "is_active",
        ]
        read_only_fields = ["id"]


class BranchSerializer(serializers.ModelSerializer[Branch]):
    class Meta:
        model = Branch
        fields = ["id", "company", "name", "code", "is_active"]
        read_only_fields = ["id"]


class RoleSerializer(serializers.ModelSerializer[Role]):
    class Meta:
        model = Role
        fields = ["id", "name", "permissions", "is_system"]
        read_only_fields = ["id", "is_system"]


class MembershipSerializer(serializers.ModelSerializer[Membership]):
    email = serializers.CharField(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "email", "status"]


class AssignmentSerializer(serializers.ModelSerializer[RoleAssignment]):
    class Meta:
        model = RoleAssignment
        fields = ["id", "membership", "role", "company", "branch"]
        read_only_fields = ["id", "membership"]

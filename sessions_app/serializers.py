# sessions/serializers.py

from django.db import transaction
from rest_framework import serializers

from courses.models import Course
from inventory.models import Equipment

from .models import Session, SessionEquipment, SessionSection


class SessionEquipmentSerializer(serializers.ModelSerializer):
    """Ligne de réservation, telle qu'attendue dans le tableau `equipments`."""

    equipment_id = serializers.PrimaryKeyRelatedField(
        source="equipment",
        queryset=Equipment.objects.all(),
    )
    name = serializers.CharField(source="equipment.name", read_only=True)

    class Meta:
        model = SessionEquipment
        fields = ["equipment_id", "name", "quantity_reserved"]

    def validate(self, attrs):
        equipement = attrs["equipment"]
        demande = attrs.get("quantity_reserved", 1)

        if demande > equipement.quantity:
            raise serializers.ValidationError(
                f"Stock insuffisant pour « {equipement.name} » : "
                f"{demande} demande(s) pour {equipement.quantity} en stock."
            )
        return attrs


class SessionSerializer(serializers.ModelSerializer):
    """Lecture d'une séance avec le cours et le matériel réservé."""

    equipments = SessionEquipmentSerializer(
        source="equipment_reservations",
        many=True,
        read_only=True,
    )
    # Expose uniquement l'ID du cours pour respecter la signature JSON attendue
    course_id = serializers.IntegerField(source="course.id", read_only=True, default=None)
    course_title = serializers.CharField(source="course.title", read_only=True, default=None)

    class Meta:
        model = Session
        fields = [
            "id",
            "date",
            "location",
            "theme",
            "description",
            "course_id",
            "course_title",
            "equipments",
        ]


class SessionWriteSerializer(serializers.ModelSerializer):
    """Création / modification d'une séance avec son matériel réservé."""

    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.all(),
        required=False,
        allow_null=True,
    )
    equipments = SessionEquipmentSerializer(many=True, required=False)

    class Meta:
        model = Session
        fields = ["id", "date", "location", "theme", "description", "course_id", "equipments"]

    def validate_equipments(self, value):
        vus = set()
        for ligne in value:
            identifiant = ligne["equipment"].id
            if identifiant in vus:
                raise serializers.ValidationError(
                    "Un même matériel ne peut apparaître qu'une fois dans la réservation."
                )
            vus.add(identifiant)
        return value

    @transaction.atomic
    def create(self, validated_data):
        reservations = validated_data.pop("equipments", [])
        session = Session.objects.create(**validated_data)
        self._enregistrer_reservations(session, reservations)
        return session

    @transaction.atomic
    def update(self, instance, validated_data):
        reservations = validated_data.pop("equipments", None)

        for champ, valeur in validated_data.items():
            setattr(instance, champ, valeur)
        instance.save()

        if reservations is not None:
            instance.equipment_reservations.all().delete()
            self._enregistrer_reservations(instance, reservations)

        return instance

    @staticmethod
    def _enregistrer_reservations(session, reservations):
        SessionEquipment.objects.bulk_create(
            [
                SessionEquipment(
                    session=session,
                    equipment=ligne["equipment"],
                    quantity_reserved=ligne.get("quantity_reserved", 1),
                )
                for ligne in reservations
            ]
        )

    def to_representation(self, instance):
        return SessionSerializer(instance, context=self.context).data
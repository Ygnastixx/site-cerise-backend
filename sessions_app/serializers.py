from django.db import transaction
from rest_framework import serializers

from courses.models import Course
from inventory.models import Equipment

from .models import Session, SessionEquipment, SessionSection


class SessionEquipmentSerializer(serializers.ModelSerializer):
    """Ligne de reservation, telle qu'attendue dans le tableau `equipments`."""

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
    """Lecture d'une seance, materiel reserve inclus."""

    equipments = SessionEquipmentSerializer(
        source="equipment_reservations",
        many=True,
        read_only=True,
    )
    course_id = serializers.PrimaryKeyRelatedField(source="course", read_only=True)
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
    """Creation / modification d'une seance avec son materiel reserve."""

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
                    "Un meme materiel ne peut apparaitre qu'une fois dans la reservation."
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

        # `equipments` absent du payload : les reservations existantes sont conservees.
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


class SessionSectionSerializer(serializers.ModelSerializer):
    """Association d'une section de cours a une seance."""

    section_id = serializers.PrimaryKeyRelatedField(source="section", read_only=True)
    section_title = serializers.CharField(source="section.title", read_only=True)

    class Meta:
        model = SessionSection
        fields = ["id", "section_id", "section_title"]

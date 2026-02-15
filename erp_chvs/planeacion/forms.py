# planeacion/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Programa
from principal.models import PrincipalMunicipio
import re
from datetime import date


class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ['programa', 'municipio', 'fecha_inicial', 'fecha_final', 'estado', 'contrato', 'imagen']
        
        widgets = {
            'fecha_inicial': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_final': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'programa': forms.TextInput(attrs={
                'placeholder': 'Ej: Programa de Alimentación Escolar 2025',
                'class': 'form-control',
                'maxlength': '200'
            }),
            'municipio': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Seleccione un municipio'
            }),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'contrato': forms.TextInput(attrs={
                'placeholder': 'Ej: CONTRATO-2025-001',
                'class': 'form-control',
                'maxlength': '100'
            }),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_programa(self):
        programa = self.cleaned_data.get('programa')
        if not programa:
            raise ValidationError("El nombre del programa es obligatorio.")
        
        if len(programa.strip()) < 5:
            raise ValidationError("El nombre del programa debe tener al menos 5 caracteres.")
        
        # Solo permitir letras, números, espacios y algunos símbolos básicos
        if not re.match(r'^[a-zA-ZáéíóúñÑ0-9\s\-_().,]+$', programa):
            raise ValidationError("El nombre del programa contiene caracteres no válidos.")
        
        return programa.strip().upper()

    def clean_fecha_inicial(self):
        fecha_inicial = self.cleaned_data.get('fecha_inicial')
        if not fecha_inicial:
            raise ValidationError("La fecha inicial es obligatoria.")
        
        if fecha_inicial < date(2020, 1, 1):
            raise ValidationError("La fecha inicial no puede ser anterior al año 2020.")
        
        if fecha_inicial > date(2030, 12, 31):
            raise ValidationError("La fecha inicial no puede ser posterior al año 2030.")
        
        return fecha_inicial

    def clean_fecha_final(self):
        fecha_final = self.cleaned_data.get('fecha_final')
        if not fecha_final:
            raise ValidationError("La fecha final es obligatoria.")
        
        if fecha_final < date(2020, 1, 1):
            raise ValidationError("La fecha final no puede ser anterior al año 2020.")
        
        if fecha_final > date(2030, 12, 31):
            raise ValidationError("La fecha final no puede ser posterior al año 2030.")
        
        return fecha_final

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio')
        if not municipio:
            raise ValidationError("El municipio es obligatorio.")
        return municipio

    def clean_contrato(self):
        contrato = self.cleaned_data.get('contrato')
        if not contrato:
            raise ValidationError("El número de contrato es obligatorio.")

        if len(contrato.strip()) < 3:
            raise ValidationError("El número de contrato debe tener al menos 3 caracteres.")

        # Permitir letras, números, guiones, guiones bajos, espacios, puntos y slashes
        if not re.match(r'^[a-zA-Z0-9\-_/\.\s]+$', contrato):
            raise ValidationError("El número de contrato contiene caracteres no válidos.")

        return contrato.strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicial = cleaned_data.get('fecha_inicial')
        fecha_final = cleaned_data.get('fecha_final')
        
        if fecha_inicial and fecha_final:
            if fecha_final <= fecha_inicial:
                raise ValidationError("La fecha final debe ser posterior a la fecha inicial.")
        
        return cleaned_data

# planeacion/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Programa, InformacionCodindem
import re
from datetime import date


class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ['programa', 'fecha_inicial', 'fecha_final', 'estado', 'imagen']
        
        widgets = {
            'fecha_inicial': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_final': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'programa': forms.TextInput(attrs={
                'placeholder': 'Ej: Programa de Alimentación Escolar 2025',
                'class': 'form-control',
                'maxlength': '200'
            }),
            'estado': forms.Select(attrs={'class': 'form-control'}),
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
        
        return programa.strip()

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

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicial = cleaned_data.get('fecha_inicial')
        fecha_final = cleaned_data.get('fecha_final')
        
        if fecha_inicial and fecha_final:
            if fecha_final <= fecha_inicial:
                raise ValidationError("La fecha final debe ser posterior a la fecha inicial.")
        
        return cleaned_data


class ComedorForm(forms.ModelForm):
    class Meta:
        model = InformacionCodindem
        fields = [
            'id_codindem', 'id_departamento', 'departamento', 'id_municipio', 'municipio',
            'id_tipo', 'tipo_comedor', 'dane', 'cod_interface', 'institucion', 'sede',
            'direccion', 'telefono', 'contacto', 'estado'
        ]
        widgets = {
                'id_codindem': forms.TextInput(attrs={
                    'placeholder': 'Identificador único',
                    'class': 'form-control',
                    'maxlength': '50'
                }),
                'id_departamento': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'ID Departamento',
                    'min': 1
                }),
                'departamento': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '100',
                    'placeholder': 'Nombre del departamento'
                }),
                'id_municipio': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'ID Municipio',
                    'min': 1
                }),
                'municipio': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '100',
                    'placeholder': 'Nombre del municipio'
                }),
                'id_tipo': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'ID Tipo',
                    'min': 1
                }),
                'tipo_comedor': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '50',
                    'placeholder': 'Tipo de comedor'
                }),
                'dane': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '20',
                    'placeholder': 'Código DANE',
                    'pattern': '[0-9]+'
                }),
                'cod_interface': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '20',
                    'placeholder': 'Código de interfaz único'
                }),
                'direccion': forms.Textarea(attrs={
                    'rows': 3,
                    'class': 'form-control',
                    'placeholder': 'Dirección completa de la sede'
                }),
                'institucion': forms.TextInput(attrs={
                    'placeholder': 'Nombre de la Institución Educativa',
                    'class': 'form-control',
                    'maxlength': '255'
                }),
                'sede': forms.TextInput(attrs={
                    'placeholder': 'Nombre de la Sede',
                    'class': 'form-control',
                    'maxlength': '255'
                }),
                'telefono': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '30',
                    'placeholder': 'Teléfono de contacto',
                    'pattern': '[0-9+\-\s()]+'
                }),
                'contacto': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '255',
                    'placeholder': 'Nombre del contacto'
                }),
                'estado': forms.TextInput(attrs={
                    'class': 'form-control',
                    'maxlength': '50',
                    'placeholder': 'Estado actual'
                }),
            }
        labels = {
                'id_codindem': 'ID Único (PK)',
                'id_departamento': 'ID Departamento',
                'id_municipio': 'ID Municipio',
                'id_tipo': 'ID Tipo',
                'cod_interface': 'Código de Interfaz',
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos que ciertos campos sean de solo lectura si se está editando
        if self.instance and self.instance.pk:
            self.fields['id_codindem'].widget.attrs['readonly'] = True
            self.fields['id_departamento'].widget.attrs['readonly'] = True
            self.fields['id_municipio'].widget.attrs['readonly'] = True
            self.fields['id_tipo'].widget.attrs['readonly'] = True
            self.fields['dane'].widget.attrs['readonly'] = True
            self.fields['cod_interface'].widget.attrs['readonly'] = True

    def clean_id_codindem(self):
        id_codindem = self.cleaned_data.get('id_codindem')
        if not id_codindem:
            raise ValidationError("El ID CODINDEM es obligatorio.")
        
        if len(id_codindem.strip()) < 3:
            raise ValidationError("El ID CODINDEM debe tener al menos 3 caracteres.")
        
        # Solo permitir letras, números, guiones y guiones bajos
        if not re.match(r'^[a-zA-Z0-9\-_]+$', id_codindem):
            raise ValidationError("El ID CODINDEM solo puede contener letras, números, guiones y guiones bajos.")
        
        return id_codindem.strip().upper()

    def clean_departamento(self):
        departamento = self.cleaned_data.get('departamento')
        if not departamento:
            raise ValidationError("El departamento es obligatorio.")
        
        if len(departamento.strip()) < 4:
            raise ValidationError("El nombre del departamento debe tener al menos 4 caracteres.")
        
        # Solo permitir letras, espacios y algunos símbolos
        if not re.match(r'^[a-zA-ZáéíóúñÑ\s\-]+$', departamento):
            raise ValidationError("El nombre del departamento solo puede contener letras, espacios y guiones.")
        
        return departamento.strip().title()

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio')
        if not municipio:
            raise ValidationError("El municipio es obligatorio.")
        
        if len(municipio.strip()) < 3:
            raise ValidationError("El nombre del municipio debe tener al menos 3 caracteres.")
        
        # Solo permitir letras, espacios y algunos símbolos
        if not re.match(r'^[a-zA-ZáéíóúñÑ\s\-]+$', municipio):
            raise ValidationError("El nombre del municipio solo puede contener letras, espacios y guiones.")
        
        return municipio.strip().title()

    def clean_dane(self):
        dane = self.cleaned_data.get('dane')
        if not dane:
            raise ValidationError("El código DANE es obligatorio.")
        
        # Solo números
        if not re.match(r'^\d+$', dane):
            raise ValidationError("El código DANE solo debe contener números.")
        
        if len(dane) < 8 or len(dane) > 12:
            raise ValidationError("El código DANE debe tener entre 8 y 12 dígitos.")
        
        return dane

    def clean_cod_interface(self):
        cod_interface = self.cleaned_data.get('cod_interface')
        if not cod_interface:
            raise ValidationError("El código de interfaz es obligatorio.")
        
        if len(cod_interface.strip()) < 3:
            raise ValidationError("El código de interfaz debe tener al menos 3 caracteres.")
        
        # Solo permitir alfanuméricos y algunos símbolos
        if not re.match(r'^[a-zA-Z0-9\-_]+$', cod_interface):
            raise ValidationError("El código de interfaz solo puede contener letras, números, guiones y guiones bajos.")
        
        return cod_interface.strip().upper()

    def clean_institucion(self):
        institucion = self.cleaned_data.get('institucion')
        if not institucion:
            raise ValidationError("El nombre de la institución es obligatorio.")
        
        if len(institucion.strip()) < 5:
            raise ValidationError("El nombre de la institución debe tener al menos 5 caracteres.")
        
        return institucion.strip().title()

    def clean_sede(self):
        sede = self.cleaned_data.get('sede')
        if not sede:
            raise ValidationError("El nombre de la sede es obligatorio.")
        
        if len(sede.strip()) < 3:
            raise ValidationError("El nombre de la sede debe tener al menos 3 caracteres.")
        
        return sede.strip().title()

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Permitir números, espacios, paréntesis, guiones y símbolo +
            if not re.match(r'^[0-9+\-\s()]+$', telefono):
                raise ValidationError("El teléfono solo puede contener números, espacios, paréntesis, guiones y el símbolo +.")
            
            # Remover espacios y símbolos para verificar longitud mínima de números
            numeros_solamente = re.sub(r'[^0-9]', '', telefono)
            if len(numeros_solamente) < 7:
                raise ValidationError("El teléfono debe tener al menos 7 dígitos.")
        
        return telefono

    def clean_contacto(self):
        contacto = self.cleaned_data.get('contacto')
        if contacto:
            if len(contacto.strip()) < 3:
                raise ValidationError("El nombre del contacto debe tener al menos 3 caracteres.")
            
            # Solo permitir letras, espacios y algunos símbolos básicos
            if not re.match(r'^[a-zA-ZáéíóúñÑ\s\-.,]+$', contacto):
                raise ValidationError("El nombre del contacto contiene caracteres no válidos.")
            
            return contacto.strip().title()
        
        return contacto

from django import forms
from django.core.exceptions import ValidationError
from .models import TablaAlimentos2018Icbf, FirmaNutricionalContrato
import re
from decimal import Decimal, InvalidOperation

class AlimentoForm(forms.ModelForm):
    class Meta:
        model = TablaAlimentos2018Icbf
        fields = [
            'codigo', 'nombre_del_alimento', 'parte_analizada', 'id_componente',
            'humedad_g', 'energia_kcal', 'energia_kj', 'proteina_g',
            'lipidos_g', 'carbohidratos_totales_g', 'carbohidratos_disponibles_g',
            'fibra_dietaria_g', 'cenizas_g', 'calcio_mg', 'hierro_mg',
            'sodio_mg', 'fosforo_mg', 'yodo_mg', 'zinc_mg', 'magnesio_mg',
            'potasio_mg', 'tiamina_mg', 'riboflavina_mg', 'niacina_mg',
            'folatos_mcg', 'vitamina_b12_mcg', 'vitamina_c_mg', 'vitamina_a_er',
            'grasa_saturada_g', 'grasa_monoinsaturada_g', 'grasa_poliinsaturada_g',
            'colesterol_mg', 'parte_comestible_field'
        ]
        
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del alimento',
                'required': True
            }),
            'id_componente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nombre_del_alimento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del alimento',
                'required': True
            }),
            'parte_analizada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parte analizada (opcional)'
            }),
            'humedad_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Humedad en gramos',
                'required': True
            }),
            'energia_kcal': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Energía en kcal',
                'required': True
            }),
            'energia_kj': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Energía en kJ',
                'required': True
            }),
            'proteina_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Proteína en gramos',
                'required': True
            }),
            'lipidos_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Lípidos en gramos',
                'required': True
            }),
            'carbohidratos_totales_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Carbohidratos totales en gramos',
                'required': True
            }),
            'carbohidratos_disponibles_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Carbohidratos disponibles en gramos'
            }),
            'fibra_dietaria_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Fibra dietaria en gramos'
            }),
            'cenizas_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cenizas en gramos'
            }),
            'calcio_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Calcio en mg'
            }),
            'hierro_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Hierro en mg'
            }),
            'sodio_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Sodio en mg'
            }),
            'fosforo_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Fósforo en mg'
            }),
            'yodo_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Yodo en mg'
            }),
            'zinc_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Zinc en mg'
            }),
            'magnesio_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Magnesio en mg'
            }),
            'potasio_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Potasio en mg'
            }),
            'tiamina_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Tiamina en mg'
            }),
            'riboflavina_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Riboflavina en mg'
            }),
            'niacina_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Niacina en mg'
            }),
            'folatos_mcg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Folatos en mcg'
            }),
            'vitamina_b12_mcg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Vitamina B12 en mcg'
            }),
            'vitamina_c_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Vitamina C en mg'
            }),
            'vitamina_a_er': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Vitamina A ER'
            }),
            'grasa_saturada_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Grasa saturada en gramos'
            }),
            'grasa_monoinsaturada_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Grasa monoinsaturada en gramos'
            }),
            'grasa_poliinsaturada_g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Grasa poliinsaturada en gramos'
            }),
            'colesterol_mg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Colesterol en mg'
            }),
            'parte_comestible_field': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Parte comestible (%)'
            })
        }
        
        labels = {
            'codigo': 'Código',
            'nombre_del_alimento': 'Nombre del Alimento',
            'parte_analizada': 'Parte Analizada',
            'id_componente': 'Componente de Alimento',
            'humedad_g': 'Humedad (g)',
            'energia_kcal': 'Energía (kcal)',
            'energia_kj': 'Energía (kJ)',
            'proteina_g': 'Proteína (g)',
            'lipidos_g': 'Lípidos (g)',
            'carbohidratos_totales_g': 'Carbohidratos Totales (g)',
            'carbohidratos_disponibles_g': 'Carbohidratos Disponibles (g)',
            'fibra_dietaria_g': 'Fibra Dietaria (g)',
            'cenizas_g': 'Cenizas (g)',
            'calcio_mg': 'Calcio (mg)',
            'hierro_mg': 'Hierro (mg)',
            'sodio_mg': 'Sodio (mg)',
            'fosforo_mg': 'Fósforo (mg)',
            'yodo_mg': 'Yodo (mg)',
            'zinc_mg': 'Zinc (mg)',
            'magnesio_mg': 'Magnesio (mg)',
            'potasio_mg': 'Potasio (mg)',
            'tiamina_mg': 'Tiamina (mg)',
            'riboflavina_mg': 'Riboflavina (mg)',
            'niacina_mg': 'Niacina (mg)',
            'folatos_mcg': 'Folatos (mcg)',
            'vitamina_b12_mcg': 'Vitamina B12 (mcg)',
            'vitamina_c_mg': 'Vitamina C (mg)',
            'vitamina_a_er': 'Vitamina A (ER)',
            'grasa_saturada_g': 'Grasa Saturada (g)',
            'grasa_monoinsaturada_g': 'Grasa Monoinsaturada (g)',
            'grasa_poliinsaturada_g': 'Grasa Poliinsaturada (g)',
            'colesterol_mg': 'Colesterol (mg)',
            'parte_comestible_field': 'Parte Comestible (%)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que solo algunos campos sean requeridos
        required_fields = ['codigo', 'nombre_del_alimento', 'humedad_g', 'energia_kcal', 
                          'energia_kj', 'proteina_g', 'lipidos_g', 'carbohidratos_totales_g']
        
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False
                
        # Deshabilitar campo código si es edición
        if self.instance and self.instance.pk:
            self.fields['codigo'].widget.attrs['readonly'] = True

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise ValidationError("El código es obligatorio.")
        
        if len(codigo.strip()) < 3:
            raise ValidationError("El código debe tener al menos 3 caracteres.")
        
        # Solo permitir alfanuméricos, guiones y guiones bajos
        if not re.match(r'^[a-zA-Z0-9\-_]+$', codigo):
            raise ValidationError("El código solo puede contener letras, números, guiones y guiones bajos.")
        
        return codigo.strip().upper()

    def clean_nombre_del_alimento(self):
        nombre = self.cleaned_data.get('nombre_del_alimento')
        if not nombre:
            raise ValidationError("El nombre del alimento es obligatorio.")
        
        if len(nombre.strip()) < 3:
            raise ValidationError("El nombre del alimento debe tener al menos 3 caracteres.")
        
        if len(nombre.strip()) > 200:
            raise ValidationError("El nombre del alimento no puede exceder 200 caracteres.")
        
        # Permitir letras, números, espacios y algunos símbolos básicos para alimentos
        if not re.match(r'^[a-zA-ZáéíóúñÑ0-9\s\-_().,/%]+$', nombre):
            raise ValidationError("El nombre del alimento contiene caracteres no válidos.")
        
        return nombre.strip().title()

    def clean_parte_analizada(self):
        parte = self.cleaned_data.get('parte_analizada')
        if parte:
            if len(parte.strip()) > 100:
                raise ValidationError("La parte analizada no puede exceder 100 caracteres.")
            
            return parte.strip().title()
        return parte

    def _validate_positive_number(self, value, field_name, max_value=None, decimals=2):
        """Método auxiliar para validar números positivos"""
        if value is not None:
            try:
                decimal_value = Decimal(str(value))
                if decimal_value < 0:
                    raise ValidationError(f"{field_name} debe ser un valor positivo.")
                
                if max_value and decimal_value > max_value:
                    raise ValidationError(f"{field_name} no puede ser mayor a {max_value}.")
                
                # Verificar decimales
                if decimals == 2 and decimal_value.as_tuple().exponent < -2:
                    raise ValidationError(f"{field_name} no puede tener más de 2 decimales.")
                
                return decimal_value
            except (ValueError, InvalidOperation):
                raise ValidationError(f"{field_name} debe ser un número válido.")
        return value

    def clean_humedad_g(self):
        humedad = self.cleaned_data.get('humedad_g')
        if humedad is None:
            raise ValidationError("La humedad es obligatoria.")
        return self._validate_positive_number(humedad, "La humedad", max_value=100)

    def clean_energia_kcal(self):
        energia = self.cleaned_data.get('energia_kcal')
        if energia is None:
            raise ValidationError("La energía en kcal es obligatoria.")
        return self._validate_positive_number(energia, "La energía (kcal)", max_value=900)

    def clean_energia_kj(self):
        energia = self.cleaned_data.get('energia_kj')
        if energia is None:
            raise ValidationError("La energía en kJ es obligatoria.")
        return self._validate_positive_number(energia, "La energía (kJ)", max_value=3800)

    def clean_proteina_g(self):
        proteina = self.cleaned_data.get('proteina_g')
        if proteina is None:
            raise ValidationError("La proteína es obligatoria.")
        return self._validate_positive_number(proteina, "La proteína", max_value=100)

    def clean_lipidos_g(self):
        lipidos = self.cleaned_data.get('lipidos_g')
        if lipidos is None:
            raise ValidationError("Los lípidos son obligatorios.")
        return self._validate_positive_number(lipidos, "Los lípidos", max_value=100)

    def clean_carbohidratos_totales_g(self):
        carbohidratos = self.cleaned_data.get('carbohidratos_totales_g')
        if carbohidratos is None:
            raise ValidationError("Los carbohidratos totales son obligatorios.")
        return self._validate_positive_number(carbohidratos, "Los carbohidratos totales", max_value=100)

    def clean_carbohidratos_disponibles_g(self):
        carbohidratos = self.cleaned_data.get('carbohidratos_disponibles_g')
        return self._validate_positive_number(carbohidratos, "Los carbohidratos disponibles", max_value=100)

    def clean_fibra_dietaria_g(self):
        fibra = self.cleaned_data.get('fibra_dietaria_g')
        return self._validate_positive_number(fibra, "La fibra dietaria", max_value=50)

    def clean_cenizas_g(self):
        cenizas = self.cleaned_data.get('cenizas_g')
        return self._validate_positive_number(cenizas, "Las cenizas", max_value=20)

    def clean_calcio_mg(self):
        calcio = self.cleaned_data.get('calcio_mg')
        return self._validate_positive_number(calcio, "El calcio", max_value=2000)

    def clean_hierro_mg(self):
        hierro = self.cleaned_data.get('hierro_mg')
        return self._validate_positive_number(hierro, "El hierro", max_value=50)

    def clean_vitamina_c_mg(self):
        vitamina_c = self.cleaned_data.get('vitamina_c_mg')
        return self._validate_positive_number(vitamina_c, "La vitamina C", max_value=1000)

    def clean_parte_comestible_field(self):
        parte_comestible = self.cleaned_data.get('parte_comestible_field')
        if parte_comestible is not None:
            if parte_comestible < 0 or parte_comestible > 100:
                raise ValidationError("La parte comestible debe estar entre 0 y 100%.")
        return parte_comestible

    def clean(self):
        cleaned_data = super().clean()
        
        # Validación cruzada: carbohidratos disponibles no pueden ser mayores que totales
        carb_totales = cleaned_data.get('carbohidratos_totales_g')
        carb_disponibles = cleaned_data.get('carbohidratos_disponibles_g')
        
        if carb_totales and carb_disponibles and carb_disponibles > carb_totales:
            raise ValidationError("Los carbohidratos disponibles no pueden ser mayores que los carbohidratos totales.")
        
        # Validación de suma de macronutrientes (aproximada)
        proteina = cleaned_data.get('proteina_g') or 0
        lipidos = cleaned_data.get('lipidos_g') or 0
        carbohidratos = cleaned_data.get('carbohidratos_totales_g') or 0
        humedad = cleaned_data.get('humedad_g') or 0
        cenizas = cleaned_data.get('cenizas_g') or 0
        
        suma_componentes = proteina + lipidos + carbohidratos + humedad + cenizas
        if suma_componentes > 105:  # Margen de tolerancia del 5%
            raise ValidationError("La suma de los componentes principales (proteína + lípidos + carbohidratos + humedad + cenizas) no puede exceder 105g por 100g de alimento.")
        
        return cleaned_data


class FirmaNutricionalContratoForm(forms.ModelForm):
    class Meta:
        model = FirmaNutricionalContrato
        fields = [
            'elabora_nombre',
            'elabora_matricula',
            'elabora_firma_texto',
            'elabora_firma_imagen',
            'aprueba_nombre',
            'aprueba_matricula',
            'aprueba_firma_texto',
            'aprueba_firma_imagen',
        ]
        widgets = {
            'elabora_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'elabora_matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'elabora_firma_texto': forms.TextInput(attrs={'class': 'form-control'}),
            'elabora_firma_imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'aprueba_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'aprueba_matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'aprueba_firma_texto': forms.TextInput(attrs={'class': 'form-control'}),
            'aprueba_firma_imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'elabora_nombre': 'Nombre (Elabora)',
            'elabora_matricula': 'Matrícula (Elabora)',
            'elabora_firma_texto': 'Firma texto (Elabora)',
            'elabora_firma_imagen': 'Firma imagen (Elabora)',
            'aprueba_nombre': 'Nombre (Aprueba)',
            'aprueba_matricula': 'Matrícula (Aprueba)',
            'aprueba_firma_texto': 'Firma texto (Aprueba)',
            'aprueba_firma_imagen': 'Firma imagen (Aprueba)',
        }

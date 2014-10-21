from django import forms

from django.contrib.auth.models import User

from django.forms import Textarea, TextInput, NumberInput, CheckboxSelectMultiple

from models import *

class RegistrationForm(forms.ModelForm):

    confirm_password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput
        }

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        pwd = cleaned_data.get('password')
        pwd_conf = cleaned_data.get('confirm_password')

        if pwd and pwd_conf and pwd != pwd_conf:
            raise forms.ValidationError("Password did not match.")

        return cleaned_data
    
    @transaction.atomic
    def clean_username(self):
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username):
            raise forms.ValidationError("Username is already taken.")

        return username

class CategoryForm(forms.ModelForm):
    
    class Meta:
        model = Category
        exclude = ('program', 'included_in_program', )
        widgets = {
            'description': Textarea(attrs={'cols': 80, 'rows': 2, 'placeholder': 'Short description of this category'}),
            'minimum_credits': NumberInput(),
            'minimum_classes': NumberInput(),
        }

    def clean(self):
        cleaned_data = super(CategoryForm, self).clean()
        minimum_inner_categories = cleaned_data['minimum_inner_categories']
        inner_categories = cleaned_data['inner_categories']

        if  minimum_inner_categories > inner_categories.count():
            raise forms.ValidationError("Too many categories")

        return cleaned_data

    @transaction.atomic
    def clean_name(self):
        name = self.cleaned_data.get('name')
        program = self.instance.program

        if Category.objects.filter(name=name, program=program):
            raise forms.ValidationError("Category name already taken.")

        return name

class ClassConstraintForm(forms.ModelForm):

    @transaction.atomic
    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school')
        super(ClassConstraintForm, self).__init__(*args, **kwargs)
        self.fields['classes'].queryset = Class.objects.filter(school=school)

    class Meta:
        model = ClassConstraint
        exclude = ('program', ) 
        widgets = {
            'mandatory_classes': CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super(ClassConstraintForm, self).clean()
        print cleaned_data
        minimum_classes = cleaned_data['minimum_classes']
        class_count = cleaned_data['classes'].count()

        if class_count < minimum_classes:
            cleaned_data['minimum_classes'] = class_count

        return cleaned_data

    @transaction.atomic
    def clean_name(self):
        name = self.cleaned_data.get('name')
        program = self.instance.program

        if ClassConstraint.objects.filter(name=name, program=program):
            raise forms.ValidationError("Group name already taken.")

        return name


class ClassForm(forms.ModelForm):

    @transaction.atomic
    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school')
        super(ClassForm, self).__init__(*args, **kwargs)
        self.fields['faculty'].queryset = Faculty.objects.filter(school=school)
        self.fields['prereqs'].queryset = Class.objects.filter(school=school)

    class Meta:
        model = Class
        exclude = ('school', )

    @transaction.atomic
    def clean_number(self):
        number = self.cleaned_data.get('number')
        school = self.instance.school

        if Class.objects.filter(school=school, number=number):
            raise forms.ValidationError("Class number already taken.")

        return number

class FacultyForm(forms.ModelForm):

    class Meta:
        model = Faculty
        exclude = ('school', )

    @transaction.atomic
    def clean_name(self):
        name = self.cleaned_data.get('name')
        school = self.instance.school

        if Faculty.objects.filter(school=school, name=name):
            raise forms.ValidationError("Faculty name already taken.")

        return name

class ExistingSchoolForm(forms.Form):
    name = forms.CharField(max_length=70)
    programName = forms.CharField(max_length=70)
    publicProgram = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop("user")
        super(ExistingSchoolForm, self).__init__(*args, **kwargs)

    @transaction.atomic
    def clean_programName(self):
        programName = self.cleaned_data['programName']
        schoolObject = School.objects.get(name=self.cleaned_data['name'])
        if Program.objects.filter(name=programName, school=schoolObject, author=self.author):
            raise forms.ValidationError("You already have a program by this name")

        return programName

class NewSchoolForm(ExistingSchoolForm):
    publicProgram = forms.IntegerField(required=False)

    @transaction.atomic
    def clean_programName(self):
        name = self.cleaned_data['name']
        schoolObjects = School.objects.filter(name=self.cleaned_data['name'])
        programName = self.cleaned_data['programName']

        if schoolObjects.count() == 0:
            return programName
       
        return super(NewSchoolForm, self).clean_programName()


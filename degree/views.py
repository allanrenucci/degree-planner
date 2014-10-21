from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.core.urlresolvers import reverse
from random import getrandbits

# Needed to manually create HttpResponses or raise an Http404 exception
from django.http import HttpResponse, Http404

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail

# Allow complex queries
from django.db.models import Q

# Import settings
from django.conf import settings

from models import *
from forms import *
import random
import string

def test(request):
	context = {}
	return render(request, 'degree/test.html', context)

@transaction.atomic
def home(request):
	context = {}
	if request.user.is_authenticated():
		context['user_programs'] = Program.objects.filter(author=request.user)
	return render(request, 'degree/home.html', context)

@transaction.atomic
def register(request):
	context = {}

	# Just display the registration form if this is a GET request
	if request.method == 'GET':
		context['form'] = RegistrationForm()
		return render(request, 'registration/register.html', context)

	new_user = User()
	form = RegistrationForm(request.POST, instance=new_user)

	# Checks the validity of the form data
	if not form.is_valid():
		context['form'] = form
		return render(request, 'registration/register.html', context)

	# Hack to hash password
	password = new_user.password
	new_user.set_password(password)

	if not settings.EMAIL_CONFIRM:
		form.save()
		new_user = authenticate(username=new_user.username, password=password)
		login(request, new_user)
		return redirect('home')

	new_user.is_active = False
	form.save()

	# generate secret token
	secret_token = SecretToken(
		user=new_user,
		token=getrandbits(63))
	secret_token.save()

	# send an email with the confirmation link
	link = request.build_absolute_uri(
		reverse('confirm email', args=(new_user.username, secret_token.token))
	)
	subject = 'Degree Planner: email confirmation link'
	message = (
		'Welcome ' + new_user.username + ' on Degree Planner.\n'
		'Please click on the following link to confirm your email address:\n\n'
		+ link
	)

	new_user.email_user(subject, message)
	context['email'] = new_user.email

	return render(request, 'registration/confirmation_sent.html', context)

def confirm_email(request, username, token):
	user = get_object_or_404(User, username=username)
	secret_token = SecretToken.objects.get(user=user)

	if secret_token.token != long(token):
		raise Http404

	user.is_active = True
	user.save()
	return render(request, 'registration/confirm.html', { 'user': username })

@login_required
@transaction.atomic
def create_degree(request):
	context = {}
	context['user_programs'] = Program.objects.filter(author=request.user)
	context['schools'] = School.objects.all()
	return render(request, 'degree/create/create_school.html', context)

@login_required
@transaction.atomic
def create_new_school(request):

	form = NewSchoolForm(request.POST, user=request.user)
	if not form.is_valid():
		return HttpResponse("programName")

	school = form.cleaned_data["name"]
	schoolObject, created = School.objects.get_or_create(name=request.POST["name"])
	schoolObject.save()

	programName =  form.cleaned_data["programName"]
	program = Program(name=programName, author=request.user, school=schoolObject).save()

	return HttpResponse(reverse('create', args=[school, programName]))

@login_required
@transaction.atomic
def create_existing_school(request):

	form = ExistingSchoolForm(request.POST, user=request.user)
	if not form.is_valid():
		return HttpResponse("programName")

	school = form.cleaned_data["name"]
	schoolObject = School.objects.get(name=school)
	public_number = form.cleaned_data['publicProgram']
	programName = form.cleaned_data['programName']

	if (public_number != -1):
		program = Program.objects.get(id=public_number).cloneWithNewAuthorAndName(request.user, programName)
	else:
		program = Program(name=programName, author=request.user, school=schoolObject).save()

	return HttpResponse(reverse('create', args=[school, programName]))


def build_create_context(user, school, program,
	categoryForm=None, classForm=None, constraintForm=None, facultyForm=None):

	context = {}

	if categoryForm:
		context['cat_form'] = categoryForm
	else:
		context['cat_form'] = CategoryForm()

	if classForm:
		context['class_form'] = classForm
	else:
		context['class_form'] = ClassForm(school=school)

	if constraintForm:
		context['constraint_form'] = constraintForm
	else:
		context['constraint_form'] = ClassConstraintForm(school=school)

	if facultyForm:
		context['fac_form'] = facultyForm
	else:
		context['fac_form'] = FacultyForm()

	context['school'] = school.name
	context['program'] = program.name
	context['categories'] = Category.objects.filter(program=program)
	context['constraints'] = ClassConstraint.objects.filter(program=program)
	context['user_programs'] = Program.objects.filter(author=user)

	context['classes'] = {}
	faculties = Faculty.objects.filter(school=school)

	for fac in faculties:
		context['classes'][fac] = Class.objects.filter(
			school=school, faculty=fac)

	return context

def process_program(user, school, program):
	school = get_object_or_404(School, name=school)
	program = get_object_or_404(Program, school=school, name=program,
		author=user)
	return school, program

@login_required
@transaction.atomic
def create(request, school, program):
	user = request.user
	school, program = process_program(user, school, program)
	context = build_create_context(request.user, school, program)
	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def create_group(request, school, program):
	user = request.user
	school, program = process_program(user, school, program)
	new_constraint = ClassConstraint(program=program)

	form = ClassConstraintForm(request.POST, school=school,
		instance=new_constraint)

	if not form.is_valid():
		context = build_create_context(user, school, program,
			constraintForm=form)
	else:
		form.save()
		context = build_create_context(user, school, program)

	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def create_class(request, school, program):
	user = request.user
	school, program = process_program(user, school, program)
	new_class = Class(school=school)

	form = ClassForm(request.POST, school=school, instance=new_class)

	if not form.is_valid():
		context = build_create_context(user, school, program,
			classForm=form)
	else:
		form.save()
		context = build_create_context(user, school, program)

	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def create_category(request, school, program):
	user = request.user
	school, program = process_program(user, school, program)
	new_category = Category(program=program)

	form = CategoryForm(request.POST, instance=new_category)

	if not form.is_valid():
		context = build_create_context(user, school, program,
			categoryForm=form)
	else:
		form.save()
		context = build_create_context(user, school, program)

	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def create_faculty(request, school, program):
	user = request.user
	school, program = process_program(user, school, program)
	new_faculty = Faculty(school=school)

	form = FacultyForm(request.POST, instance= new_faculty)

	if not form.is_valid():
		context = build_create_context(user, school, program,
			facultyForm=form)
	else:
		form.save()
		context = build_create_context(user, school, program)

	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def remove_group(request, school, program, group_id):
	user = request.user
	school, program = process_program(user, school, program)
	group = get_object_or_404(ClassConstraint, id=group_id)

	if group.program.author == user:
		group.delete()

	context = build_create_context(user, school, program)
	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def remove_category(request, school, program, category_id):
	user = request.user
	school, program = process_program(user, school, program)
	category = get_object_or_404(Category, id=category_id)

	if category.program.author == user:
		for taken in TakenClass.objects.filter(in_categories__id=category_id):
			taken.in_categories.remove(category)
			taken.save()
			if taken.in_categories.count() == 0:
				taken.delete()
		category.delete()

	context = build_create_context(user, school, program)
	return render(request, 'degree/create/create_category.html', context)

@login_required
@transaction.atomic
def assign_categories(request, school, program):
	user = request.user
	_, program = process_program(user, school, program)
	context = {}

	main, sub = sortCategories(program)
	context['school'] = school
	context['program'] = program.name
	context['main_cats'] = main
	context['sub_cats'] = sub
	context['user_programs'] = Program.objects.filter(author=user)
	return render(request, 'degree/create/create_program.html', context)

@transaction.atomic
def sortCategories(program):
	main = list(Category.objects.filter(program=program))
	sub = []
	for category in Category.objects.all():
		for inner in category.inner_categories.all():
			if inner in main:
				main.remove(inner)
				sub.append(inner)
	return (main,sub)

@login_required
@transaction.atomic
def finalize_program(request, school, program):
	school, program = process_program(request.user, school, program)

	if 'categoryInProrgam' in request.POST:
		chosen_categories = request.POST.getlist('categoryInProrgam')
		for cat_id in chosen_categories:
			category = Category.objects.get(id=cat_id)
			category.included_in_program = True
			category.save()

	# MAKE EDITABLE - IE SET TO FALSE EVERY CATEGORY NOT IN HERE!!

	if 'description' in request.POST:
		program.description = request.POST['description']
		program.save()

	return redirect('build', school=school.name, program=program.name)

@login_required
@transaction.atomic
def build(request, school, program, category_id = None):
	user = request.user
	school, program = process_program(user, school, program)
	
	context = {}

	if category_id != None:
		category = get_object_or_404(Category, id=int(category_id))
		context['cur_category'] = category
		context['classes'] = {}
		allowed_classes = category.allowedClasses()
		for allowed_class in allowed_classes:
			if TakenClass.objects.filter(taken_class=allowed_class, program=program).exists():
				context['classes'][allowed_class] = TakenClass.objects.get(taken_class=allowed_class, program=program)
			else:
				context['classes'][allowed_class] = False

	context['program'] = program.name
	context['school'] = school.name
	context['user_programs'] = Program.objects.filter(author=user)
	context['main_cats'] = Category.objects.filter(program=program, included_in_program=True)

	return render(request, 'degree/build/build_home.html', context)

@login_required
@transaction.atomic
def add_class(request, school, program, category_id, class_id):

	category = Category.objects.get(id=int(category_id))
	takenClass = getAndCreateTakenClass(school, program, category, class_id)

	return HttpResponse("201");

@login_required
@transaction.atomic
def remove_class(request, school, program, category_id, class_id):
	category = get_object_or_404(Category, id=int(category_id))
	cla = get_object_or_404(Class, id=int(class_id))
	program = category.program
	takenClass = TakenClass.objects.get(program=program, taken_class=cla)

	if category in takenClass.in_categories.all():
		takenClass.in_categories.remove(category)
		takenClass.save()

	if takenClass.in_categories.count() == 0:
		takenClass.delete()
	
	for inner_cat in category.inner_categories.all():
		remove_class(request, school, program, inner_cat.id, class_id)

	return HttpResponse("201");

@login_required
@transaction.atomic
def add_grade(request, school, program, category_id, class_id):
	school, program = process_program(request.user, school, program)

	category = Category.objects.get(id=int(category_id))
	takenClass = getAndCreateTakenClass(school, program, category, class_id)

	if 'grade' in request.POST and request.POST['grade'] != "":
		takenClass.grade = float(request.POST['grade'])
		takenClass.save()

	return HttpResponse("201");

@login_required
@transaction.atomic
def generate_details(request, school, program, category_id, category_id2 = None):

	context = {}

	context['back'] = None
	if category_id != category_id2:
		context['back'] = category_id2
		category = Category.objects.get(id=int(category_id2))
	else:
		category = Category.objects.get(id=int(category_id))
	context['cur_category'] = category
	context['first_category_id'] = category_id
	context['school'] = school
	context['program'] = program

	(classes, credits) = category.classesAndCreditsTakenInCategory()
	context['currentClassAmount'] = classes
	context['currentCreditAmount'] = credits

	context['complete'] = []
	context['incomplete'] = []
	for constraint in category.constraints.all():
		if constraint.constraintIsComplete(category):
			context['complete'].append(constraint)
		else:
			context['incomplete'].append(constraint)

	context['complete_cats'] = []
	context['incomplete_cats'] = []
	for cat in category.inner_categories.all():
		if cat.categoryIsComplete():
			context['complete_cats'].append(cat)
		else:
			context['incomplete_cats'].append(cat)

	context['innerCategoriesDone'] = len(context['complete_cats'])

	return render(request, 'degree/build/generated_details.html', context)

@transaction.atomic
def getAndCreateTakenClass(school, program, category, class_id):
	this_class = get_object_or_404(Class, id=int(class_id))
	cprogram = category.program
	candidate = TakenClass.objects.filter(program=cprogram, taken_class=this_class)
	if candidate.count() == 0:
		taken = TakenClass(taken_class=this_class, program=cprogram)
		taken.save()
	else:
		taken = candidate[0]

	taken.in_categories.add(category)
	taken.save()

	for inner_cat in category.inner_categories.all():
		getAndCreateTakenClass(school, program, inner_cat, class_id)
	
	return taken

@login_required
@transaction.atomic
def analyze_program(request, school, program):
	_, program = process_program(request.user, school, program)
	context = {}
	incomplete = []
	no_prereqs = {}
	double_counted = {}

	for category in Category.objects.filter(program=program, included_in_program=True):
		if not category.categoryIsComplete():
			incomplete.append(category)

	taken_classes = TakenClass.objects.filter(program=program)
	for taken in taken_classes:
		counted_in = taken.in_categories.filter(included_in_program=True) 
		taken_class = taken.taken_class
		if len(counted_in) > 1:
			double_counted[taken_class] = counted_in
		for prereq_class in taken.taken_class.prereqs.all():
			if TakenClass.objects.filter(taken_class=prereq_class, program=program).count() == 0:
				if not taken_class in no_prereqs:
					no_prereqs[taken_class] = []
				no_prereqs[taken_class].append(prereq_class)

	context['no_prereqs'] = no_prereqs
	context['double_counted'] = double_counted
	context['incomplete'] = incomplete

	return render(request, 'degree/build/analysis_results.html', context)

@login_required
@transaction.atomic
def publish(request, school, program):
	_, program = process_program(request.user, school, program)
	program.public = True
	program.save()

	return HttpResponse("201")

@login_required
@transaction.atomic
def get_public(request, school):
	context = {}
	school = get_object_or_404(School, name=school)
	context['public'] = Program.objects.filter(
		Q(school=school), Q(public=True) | Q(author=request.user))

	return render(request, 'degree/create/public_programs.html', context)

@login_required
@transaction.atomic
def program_info(request, school, program):
	context = {}
	_, program = process_program(request.user, school, program)
	context['programObject'] = program

	credits = 0

	taken = TakenClass.objects.filter(program=program)
	context['taken'] = taken 
	
	for taken_class in taken:
		credits += taken_class.taken_class.credits
	classes = taken.count()

	context['classes'] = classes
	context['credits'] = credits

	return render(request, 'degree/build/program_info.html', context)

@login_required
@transaction.atomic
def gradesheet(request, school, program):
	user = request.user
	school, program = process_program(user, school, program)
	my_gradesheet = GradeSheet.objects.filter(author=user, program=program)

	if my_gradesheet.count() != 0:
		url = request.build_absolute_uri(reverse('gradesheet public', args=[my_gradesheet[0].identifier]))
		return create_gradesheet(request, school.name, program.name, user, { 'gradesheet': url })

	identifier = ''.join(random.choice(string.letters) for i in range(20))
	if GradeSheet.objects.filter(identifier=identifier).count() != 0:
		return gradesheet(request, school.name, program.name)

	gradesheet = GradeSheet(identifier=identifier, author=user, program=program)
	gradesheet.save()

	url = request.build_absolute_uri(reverse('gradesheet public', args=[identifier]))

	return create_gradesheet(request, school.name, program.name, user, { 'gradesheet': url })

@transaction.atomic
def create_gradesheet(request, school, program, user, context = {}):
	_, program = process_program(user, school, program)
	taken = TakenClass.objects.filter(program=program).exclude(grade=-1)

	context['user_programs'] = Program.objects.filter(author=user)
	context['taken_classes'] = taken
	context['school'] = school
	context['program'] = program.name
	context['author'] = user

	average = 0
	credits = 0
	for taken_class in taken:
		cur_credit = taken_class.taken_class.credits
		credits += cur_credit
		average += taken_class.grade * cur_credit
	classes = taken.count()
	if credits > 0:
		average /= credits

	context['credits'] = credits
	context['classes'] = classes
	context['average'] = average

	return render(request, 'degree/gradesheet.html', context)

@transaction.atomic
def gradesheet_public(request, identifier):
	gradesheet = get_object_or_404(GradeSheet, identifier=identifier)
	return create_gradesheet(request, gradesheet.program.school, gradesheet.program.name, gradesheet.author)

@login_required
@transaction.atomic
def regenerate_link(request, school, program):
	user = request.user
	_, program = process_program(user, school, program)
	my_gradesheet = GradeSheet.objects.get(author=user, program=program)

	identifier = ''.join(random.choice(string.letters) for i in range(20))
	if GradeSheet.objects.filter(identifier=identifier).count() != 0:
		return regenerate_link(request, school, program.name)

	my_gradesheet.delete()
	GradeSheet(identifier=identifier, author=user, program=program).save()

	url = request.build_absolute_uri(reverse('gradesheet public', args=[identifier]))

	return HttpResponse(content=str(url))

@login_required
@transaction.atomic
def add_all(request, school, program, category_id):
	_, program = process_program(request.user, school, program)
	category = get_object_or_404(Category, id=category_id)

	for aclass in category.allowedClasses():
		taken, created = TakenClass.objects.get_or_create(taken_class=aclass, program=program)
		taken.save()
		if not category in taken.in_categories.all():
			taken.in_categories.add(category)
			taken.save()	
		
	return redirect('build category', school=school, program=program.name, category_id=category_id)

@login_required
@transaction.atomic
def remove_all(request, school, program, category_id):
	_, program = process_program(request.user, school, program)
	category = get_object_or_404(Category, id=category_id)

	for taken in TakenClass.objects.filter(program=program, in_categories__id=category_id):
		taken.in_categories.remove(category)
		taken.save()
		if taken.in_categories.count() == 0:
			taken.delete()

	return redirect('build category', school=school, program=program.name, category_id=category_id)

@login_required
@transaction.atomic
def add_from_public(request, school, program, category_id):
		
	add_from_public_helper(request, school, program)
	return redirect('build category', school=school, program=program, category_id=category_id)

@login_required
@transaction.atomic
def add_from_public_no_cat(request, school, program):

	add_from_public_helper(request, school, program)
	return redirect('build', school=school, program=program)

@login_required
@transaction.atomic
def add_from_public_helper(request, school, program):
	_, program = process_program(request.user, school, program)

	if not program.template:
		return

	categories = {}
	for cat in Category.objects.filter(program=program):
		categories[cat.name] = (cat, cat.allowedClasses())

	for taken in TakenClass.objects.filter(program=program.template):
		for cat in taken.in_categories.all():
			if cat.name in categories and taken.taken_class in categories[cat.name][1]:
				newTaken, created = TakenClass.objects.get_or_create(taken_class=taken.taken_class, program=program)
				newTaken.save()
				if not categories[cat.name][0] in newTaken.in_categories.all():
					newTaken.in_categories.add(categories[cat.name][0])
					newTaken.save()


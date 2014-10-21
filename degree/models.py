from django.db import models
from django.contrib.auth.models import User
from django.db import transaction

class School(models.Model):
	name = models.CharField(max_length=70, primary_key=True, unique=True)

	def __unicode__(self):
		return self.name

class Faculty(models.Model):
	school = models.ForeignKey(School)
	name = models.CharField(max_length=70)

	class Meta:
		unique_together = ("school", "name")

	def __unicode__(self):
		return self.name

class Class(models.Model):
	school = models.ForeignKey(School)
	number = models.IntegerField()
	name = models.CharField(max_length=45)
	faculty = models.ForeignKey(Faculty)
	credits = models.FloatField()
	prereqs = models.ManyToManyField("self", blank=True, symmetrical=False)

	class Meta:
		unique_together = ("school", "number")
		ordering = ['number']

	def __unicode__(self):
		return str(self.number) + " - " + self.name

class Program(models.Model):
	school = models.ForeignKey(School)
	name = models.CharField(max_length=70)
	author = models.ForeignKey(User)
	public = models.BooleanField(default=False)
	description = models.CharField(max_length=600, blank=True)
	template = models.ForeignKey("self", null=True, blank=True)

	class Meta:
		unique_together = ("school", "name", "author")

	def __unicode__(self):
		return self.name

	@transaction.atomic
	def cloneWithNewAuthorAndName(self, author, name):
		program = Program(	school=self.school,
							name=name,
							author=author,
							public=False,
							description=self.description,
							template=self	)
		program.save()

		for category in Category.objects.filter(program=self, included_in_program=True):
			category.cloneForNewProgram(program)

		return program

class ClassConstraint(models.Model):
	name = models.CharField(max_length=20)
	program = models.ForeignKey(Program)
	classes = models.ManyToManyField(Class, blank=True, related_name='Classes', symmetrical=False)
	minimum_classes = models.IntegerField()

	def __unicode__(self):
		return self.name

	@transaction.atomic
	def cloneForNewProgram(self, program):
		constraint = ClassConstraint(name=self.name,
			program=program,
			minimum_classes=self.minimum_classes)
		constraint.save()

		for aclass in self.classes.all():
			constraint.classes.add(aclass)
			constraint.save()

		return constraint

	@transaction.atomic
	def constraintIsComplete(self, category):
		to_complete = self.minimum_classes
		completed = 0
		if to_complete == 0:
			return True
		for aclass in self.classes.all():
			if TakenClass.objects.filter(program=self.program, taken_class=aclass, in_categories__id=category.id).count() != 0:
				completed += 1
			if completed >= to_complete:
				return True
		return False

class Category(models.Model):
	program = models.ForeignKey(Program)
	name = models.CharField(max_length=40)
	description = models.CharField(max_length=500, blank=True)
	constraints = models.ManyToManyField(ClassConstraint, blank=True)
	minimum_credits = models.FloatField(default=0)
	minimum_classes = models.IntegerField(default=0)
	inner_categories = models.ManyToManyField("self", blank=True, symmetrical=False)
	minimum_inner_categories = models.IntegerField(default=0)
	included_in_program = models.BooleanField(default=False)

	def __unicode__(self):
		return self.name

	@transaction.atomic
	def cloneForNewProgram(self, program):
		new_cat = Category(	program=program,
							name=self.name,
							description=self.description,
							minimum_credits=self.minimum_credits,
							minimum_classes=self.minimum_classes,
							minimum_inner_categories=self.minimum_inner_categories,
							included_in_program=self.included_in_program 	)
		new_cat.save()

		for inner in self.inner_categories.all():
			new_cat.inner_categories.add(inner.cloneForNewProgram(program))
			new_cat.save()

		for constraint in self.constraints.all():
			new_cat.constraints.add(constraint.cloneForNewProgram(program))
			new_cat.save()

		return new_cat
	
	@transaction.atomic
	def allowedClasses(self):
		classes = []
		for constraint in self.constraints.all():
			for clas in constraint.classes.all():
				classes.append(clas)

		for category in self.inner_categories.all():
			classes += category.allowedClasses()

		return set(classes) 

	@transaction.atomic
	def allTakenClassesOfCategory(self):
		classes = []
		taken = TakenClass.objects.filter(program=self.program, in_categories__id=self.id)
		for taken_class in taken:
			classes.append(taken_class.taken_class)
		for cat in self.inner_categories.all():
			classes += cat.allTakenClassesOfCategory()
		return set(classes)

	@transaction.atomic
	def classesAndCreditsTakenInCategory(self):
		credits = 0
		taken = self.allTakenClassesOfCategory()
		for taken_class in taken:
			credits += taken_class.credits
		classes = len(taken)
		return (classes,credits)

	@transaction.atomic
	def categoryIsComplete(self):
		for constraint in self.constraints.all():
			if not constraint.constraintIsComplete(self):
				return False
		flag = False
		to_complete = self.minimum_inner_categories
		completed = 0
		if to_complete == 0:
			flag = True
		for cat in self.inner_categories.all():
			if cat.categoryIsComplete():
				completed += 1
			if completed >= to_complete:
				flag = True
		if flag == False:
			return False
		(classes,credits) = self.classesAndCreditsTakenInCategory()
		return classes >= self.minimum_classes and credits >= self.minimum_credits

class TakenClass(models.Model):
	taken_class = models.ForeignKey(Class)
	program = models.ForeignKey(Program)
	in_categories = models.ManyToManyField(Category, blank=True, symmetrical=False)
	grade = models.FloatField(blank=True, default=-1.0)

	class Meta:
		ordering = ['taken_class']

class GradeSheet(models.Model):
	identifier = models.CharField(max_length=20, primary_key=True)
	author = models.ForeignKey(User)
	program = models.ForeignKey(Program)

class SecretToken(models.Model):
	user = models.OneToOneField(User, unique=True)
	token = models.BigIntegerField()


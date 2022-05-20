import os
import uuid
import boto3
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
# Although Django did not include a URL or view, it does include a UserCreationForm that we can 
# use in a template to generate all of the inputs for a User model.

# In addition, we're also going to use the login function to automatically log in a user when 
# they sign up - users hate signing up and then having to turn around and log in!
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Cat, Toy, Photo
from .forms import FeedingForm

# View functions

def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')
@login_required
def cats_index(request):
  cats = Cat.objects.filter(user=request.user)
  # This reads ALL cats, not just the logged in user's cats user comes from model
  # cats = Cat.objects.all()
  return render(request, 'cats/index.html', { 'cats': cats })
@login_required
def cats_detail(request, cat_id):
  cat = Cat.objects.get(id=cat_id)
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
  # instantiate FeedingForm to be rendered in the template
  feeding_form = FeedingForm()
  return render(request, 'cats/detail.html', {
    'cat': cat,
    'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have
  })

class CatCreate(LoginRequiredMixin, CreateView):
  model = Cat
  fields = ['name', 'breed', 'description', 'age']
  
  # This inherited method is called when a
  # valid cat form is being submitted
  def form_valid(self, form):
    # Assign the logged in user (self.request.user)
    form.instance.user = self.request.user  # form.instance is the cat, attach 
    #user information to the form for the cat
    # Let the CreateView do its job as usual
    return super().form_valid(form)

#We're overriding the CreateView's form_valid method to assign the logged in user, 
#self.request.user. Yes, the built-in auth automatically assigns the user to the 
# request object similar to what Passport did in Express.

#In Python, methods inherited by the superclass can be invoked by prefacing the 
#method name with super(). Accordingly, after updating the form to include the user, 
#we're calling super().form_valid(form) to let the CreateView do its usual job of 
#creating the model in the database and redirecting.

class CatUpdate(LoginRequiredMixin, UpdateView):
  model = Cat
  fields = ['breed', 'description', 'age']

class CatDelete(LoginRequiredMixin, DeleteView):
  model = Cat
  success_url = '/cats/'

@login_required
def add_feeding(request, cat_id):
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)

@login_required
def add_photo(request, cat_id):
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
    s3 = boto3.client('s3')
    # need a unique "key" for s3 (filename)
    key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
    try:
      bucket = os.environ['S3_BUCKET']
      s3.upload_fileobj(photo_file, bucket, key)
      url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
      Photo.objects.create(url=url, cat_id=cat_id)
    except:
      print('An error occurred uploading file to S3')
  return redirect('detail', cat_id=cat_id)



@login_required
def assoc_toy(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.add(toy_id)
  return redirect('detail', cat_id=cat_id)

@login_required
def unassoc_toy(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.remove(toy_id)
  return redirect('detail', cat_id=cat_id)

def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST)
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)

# The signup view function will be the first view we've coded that performs two different 
# behaviors based upon whether it was called via a GET or POST request:

# If it's a GET request: The view function should render a template with a form for the user to enter their info.
# If it's a POST request: The user has submitted their info and the function should create the user and redirect.


class ToyList(LoginRequiredMixin, ListView):
  model = Toy

class ToyDetail(LoginRequiredMixin, DetailView):
  model = Toy

class ToyCreate(LoginRequiredMixin, CreateView):
  model = Toy
  fields = '__all__'

class ToyUpdate(LoginRequiredMixin, UpdateView):
  model = Toy
  fields = ['name', 'color']

class ToyDelete(LoginRequiredMixin, DeleteView):
  model = Toy
  success_url = '/toys/'

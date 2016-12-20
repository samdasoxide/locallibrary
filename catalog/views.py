import datetime

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .forms import RenewBookForm
from .models import Book, Author, BookInstance, Genre

# Create your views here.


def index(request):
    """
    view function for home page of site.
    """
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    # Number of all available copies of all books
    num_instances = BookInstance.objects.all().count()

    # Available books i.e. books with status available
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The all() is implmeneted by default.
    num_authors = Author.objects.count()

    # Genre count
    num_genre = Genre.objects.count()

    # Book titles that contain the word 'python'
    num_python = Book.objects.filter(title__icontains='python').count()

    # How many times the site has been visited
    # Each time we receive a request we increament the value
    # store it back in the session
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available,
                 'num_authors': num_authors,
                 'num_genre': num_genre,
                 'num_python': num_python,
                 'num_visits': num_visits
                 }
    )


class BookListView(generic.ListView):
    model = Book
    paginate_by = 3


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBookByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoadBooksByAllUsersListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = (
        'catalog.can_mark_returned',
        'catalog.change_bookinstance')

    template_name = 'catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it
        # with data from the request (binding)
        form = RenewBookForm(request.POST)

        # Check if form is valid
        if form.is_valid():
            # Process the data in form.cleaned as required
            # (here just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL
            return HttpResponseRedirect(reverse('all-borrowed'))
    # If this a GET (or any other method) create the defauld form
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = RenewBookForm(initial={'renewal-date': proposed_renewal_date, })

    return render(request,
                  'catalog/book_renew_librarian.html',
                  {'form': form, 'bookinst': book_inst}
                  )


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_birth': '12/10/2016', }


class AuthorUpdate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

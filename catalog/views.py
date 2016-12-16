from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import generic

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
    template = 'catalog/bookinstance_list_borrwed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrowed=self.request.user).filter(status__exact='o').order_by('due_back')

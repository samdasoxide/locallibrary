from __future__ import unicode_literals

# Required for unique book instances
from datetime import date
import uuid

from django.contrib.auth.models import User
from django.db import models
# Used to generate URLs by reverseing the URL patterns
from django.urls import reverse


# Create your models here.
class Genre(models.Model):
    """
    Model representing a book genre (e.g. Science Fiction, Non Fiction).
    """
    name = models.CharField(
        max_length=200,
        help_text="""Enter a book genre
                  (e.g. Science Fiction, French Poetry etc.)""")

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.name


class Language(models.Model):
    """
    Model representing the book language
    """
    name = models.CharField(
        max_length=100,
        help_text='Enter language book is written in')

    def __str__(self):
        """
        String representation of an object
        """
        return self.name


class Book(models.Model):
    """
    Model representing a book (but not a specific copy of a book)
    """
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)

    # Foreing key used because book can only have one author, but authors can have mutilple books
    # Author as a string rather than object because it hasn't been declared yet in the file.

    summary = models.TextField(
        max_length=1000,
        help_text='Enter brief description of the book')

    isbn = models.CharField(
        'ISBN',
        max_length=13,
        help_text='''13 Character
        <a href="https://www.isbn-international.org/content/what-isbn">
            ISBN number
        </a>''')

    genre = models.ManyToManyField(
        Genre,
        help_text='Select a genere for this book')

    # ManyToManyField used because genere can contain many books. Books can cover many generes.
    # Generes class has already been defined so we can specify the object above.

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        Returns the url to access a particular book instance
        """
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """
        Creates a string for the Genre.
        This is required to display genre in Admin.
        """
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'


class BookInstance(models.Model):
    """
    Model representing a specific copy of a book
    (i.e. that can be borrowed from the library)
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text='Unique id for this particular book across whole library')

    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)

    language = models.ForeignKey(
        'Language',
        on_delete=models.SET_NULL,
        null=True)

    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)

    LOAN_STATUS = (
        ('d', 'Maintanace'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True, null=True)

    borrower = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)

    def __str__(self):
        '''
        String for representing the model object
        '''
        return '%s (%s)' % (self.id, self.book.title)

    @property
    def is_overdue(self):
        if date.today() > self.due_back:
            return True
        return False


class Author(models.Model):
    """
    Model representing an author.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Died', null=True, blank=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular author instance
        """
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """
        String for representing the Model object.
        """

        return '%s, %s' % (self.last_name, self.first_name)

from django.contrib import admin

from .models import Author, Book, BookInstance, Genre, Language

# Register your models here.
# Defining ModelAdmin class
# This is to change how a model is displayed in the admin interface.


class BookInline(admin.TabularInline):
    model = Book


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name',
                    'first_name',
                    'date_of_birth',
                    'date_of_death')
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
    inlines = [BookInline]


class BookInstanceInline(admin.TabularInline):
    """
    Adding associated records at the same time
    i.e. have book information and information about specific copies
    on the same page.
    """
    model = BookInstance


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """
    Getting the genere may not be a good idea
    because of the 'cost' of the database operation.
    We will use a function in our (Book) model to get this
    """
    list_display = ('title', 'author', 'display_genre')
    inlines = [BookInstanceInline]


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'status', 'borrower', 'due_back', 'id')
    list_filter = ('status', 'due_back')

    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_back', 'borrower')
        }),
    )


# Register admin with the assosiated model
admin.site.register(Author, AuthorAdmin)
admin.site.register(Genre)
admin.site.register(Language)

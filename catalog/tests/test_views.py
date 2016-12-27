import datetime

from django.contrib.auth.models import Permission, User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from catalog.models import Author, BookInstance, Book, Genre, Language


class AuthorListviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 13 authors for pagniation tests
        number_of_authors = 13
        for author_num in range(number_of_authors):
            Author.objects.create(first_name='Christian %s',
                                  last_name='Surname %s' % author_num)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_corret_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagniation_is_three(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['author_list']) == 3)

    def test_list_all_authors(self):
        # Get seconnd page and confirm it has (exactly) remaining 1 item
        resp = self.client.get(reverse('authors') + '?page=5')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] ==  True)
        self.assertTrue(len(resp.context['author_list']) == 1)


class LoanedBookInstanceByUserListViewTest(TestCase):

    def setUp(self):
        # Create two users
        test_user1 = User.objects.create_user(
            username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(
            username='testuser2', password='12345')
        test_user2.save()

        # Create a book
        test_author = Author.objects.create(
            first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title', summary='My book Summary',
            isbn='ABCDEF', author=test_author)
        # Create  genre as a post step
        genere_objects_for_book = Genre.objects.all()
        test_book.genre = genere_objects_for_book
        test_book.save()

        # Create 30 BookInstance objects
        number_of_copies = 30
        for book_copy in range(number_of_copies):
            return_date = timezone.now() + datetime.timedelta(
                days=book_copy % 5)
            if book_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status = 'm'
            BookInstance.objects.create(
                book=test_book, imprint='Unlikely Imprint, 2016',
                due_back=return_date, borrower=the_borrower,
                status=status, language=test_language)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a response "Success"
        self.assertEqual(resp.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a repsonse "Success"
        self.assertEqual(resp.status_code, 200)

        # Check that initially we don't have any books in list (none on loan)
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        get_ten_books = BookInstance.objects.all()[:10]

        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        # Check that now we have borrowed books in the list
        resp = self.client.get(reverse('my-borrowed'))
        # Check our user is logged in
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # check that we got a response success
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)

        # Confirm that all books that belong to user on
        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):
        # change all books to be on load
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(resp.status_code, 200)

        # Confirm that of the items, only 10 are displayed due to pagniaiton
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


class RenewBookInstancesViews(TestCase):

    def setUp(self):
        # Create a user
        test_user1 = User.objects.create_user(
            username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(
            username='testuser2', password='12345')
        test_user2.save()

        permission = Permission.objects.get(name="Set book as returned")
        permission2 = Permission.objects.get(name="Can change book instance")
        test_user2.user_permissions.add(permission)
        test_user2.user_permissions.add(permission2)
        test_user2.save()

        # Create a book
        test_author = Author.objects.create(
            first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book title', summary='My book Summary',
            isbn='ABCDEFG', author=test_author)
        # Create genre as a post step
        genre_objects_for_book = Genre.objects.all()
        test_book.genre = genre_objects_for_book
        test_book.save()

        # create a bookinstance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)

        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book, imprint='Unlikely imprint, 2016',
            due_back=return_date, status='o',
            borrower=test_user1, language=test_language)

        # create a BookInstance object for test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book, imprint='Unlikely imprint, 2016',
            due_back=return_date, status='o',
            borrower=test_user2, language=test_language)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance1.pk, }))
        #Manually check redirect (Can't use assertRedirect because the redirect url is unpredicted)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance1.pk, }))

        # Manually check redirect(can't use assertRedirect because the redirect url is unpredicted)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        '''
        When the user has the correct permissions but not the borrower
        i.e. the librarian
        '''
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance2.pk, }))

        # Check that it let us login. We're a librarian, so we can view any users book
        self.assertEqual(resp.status_code, 200)


    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uid = uuid.uuid4()   #Unlikely UID to match our bookinstance!
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': test_uid, }))
        self.assertEqual(resp.status_code, 404)

    def test_users_correct_template(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance2.pk, }))

        self.assertEqual(resp.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(
            resp.context['form'].initial['renewal-date'],
            date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='testuser2', password='12345')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance1.pk, }),
            {'renewal_date': valid_date_in_future})
        self.assertRedirects(resp, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='12345')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        resp = self.client.post(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance2.pk, }),
            {'renewal_date': date_in_past})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='12345')
        date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        resp = self.client.post(reverse(
            'renew-book-librarian',
            kwargs={'pk': self.test_bookinstance1.pk, }),
            {'renewal_date': date_in_future})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(
            resp,
            'form',
            'renewal_date',
            'Invalid date - renewal more than 4 weeks')

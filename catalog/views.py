from django.shortcuts import render
from django.http import HttpResponse
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .forms import RenewBookForm
from .models import Author

@login_required
def index(request):
    """
    View function for home page of site.
    """
    # Generate counts of some of the main objects

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact = 'a').count()
    num_authors = Author.objects.count()

    genre_fantasy_specific = Genre.objects.filter(name__icontains = 'fantasy').count()
    book_contains_love = Book.objects.filter(title__icontains = 'love').count()

    # Session handling (Counting the number of visitors to the site)
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable
    return render(
        request, 
        'index.html',
        context={
            'num_books':num_books, 'num_instances':num_instances,
            'num_instances_available':num_instances_available,
            'num_authors': num_authors,'genre_fantasy_specific':genre_fantasy_specific,
            'book_contains_love':book_contains_love, 'num_visits':num_visits
            }
    )

class BookListView(generic.ListView):
    model = Book
    paginate_by  = 1

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user. 
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower= self.request.user).filter(status__exact = 'o').order_by('due_back')

class Borrowed(LoginRequiredMixin, PermissionRequiredMixin ,generic.ListView):
    """
    Generic class-based view listing books of every user to the staff. 
    """
    model = BookInstance
    template_name = 'catalog/borrowed.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'
    def get_queryset(self):
        return BookInstance.objects.all().filter(status__exact = 'o').order_by('due_back')

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})

class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death':'05/01/2018'}

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

class BookCreate(CreateView):
    model = Book
    fields = '__all__'
class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'
class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('books')
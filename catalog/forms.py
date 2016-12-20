from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime  # For checking renewal date range


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(
        help_text='Enter a date between now and 4 weeks (default 3)'
    )

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check date is not in past
        if data < datetime.date.today():
            raise ValidationError(_("Invalid date - renewal in past"))

        # Check date is in range librarian is allowed to change
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_("Invalid date - renewal more than 4 weeks"))

        # Remember always to retund cleaned data
        return data
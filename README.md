# EverPoll API with Django Rest Framework

This Everpoll REST API project is the companion of a [Everpoll Andorid App](https://github.com/manthansharma/EverPoll-app).

## Setup

1. Add "everpoll" to your INSTALLED_APPS setting like this::

        INSTALLED_APPS = [
            ...
            'everpoll',
        ]

2. Include the everpoll URLconf in your project urls.py like this:
        
        url(r'^everpoll/', include('everpoll.urls')),

3. Run `python manage.py migrate` to create the everpoll models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a everpoll code (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/api/ to create your poll.
